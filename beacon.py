from flask import Flask, request, send_file, make_response, render_template
from flask_cors import CORS
import json
import time
from db import get_pg

app = Flask("beacon")
CORS(app, max_age=60*60*24*365, supports_credentials=True)


@app.route("/favicon.ico")
def favicon():
    return "no", 404

@app.route("/robots.txt")
def robots():
    return "", 204

@app.route("/")
def index():
    return render_template("index.html")

def is_authed(request, cur):
    authenticated = False

    auth = request.headers.get('authorization', '')
    if auth.startswith('Bearer '):
        auth = auth[7:]
        cur.execute('''SELECT FROM auth_tokens WHERE token = %s''', (auth,))
        if cur.fetchone() is not None:
            authenticated = True

    return authenticated


@app.route("/collect/<path:path>", methods={"POST",})
def recieve_beacon(path=""):
    if not (request.is_json or request.content_type == "application/csp_report"):
        return "this isn't json", 415

    body = request.get_json(force = True);

    collected_at = time.time()
    if 'collected_at' in body:
        collected_at = body['collected_at']
        del body['collected_at']


    pg = get_pg()
    cur = pg.cursor()

    authenticated = is_authed(request, cur)

    body = json.dumps(body)

    success = True
    try:
        cur.execute("""
            INSERT INTO beacons (collected_at, type, body, authenticated)
            VALUES (to_timestamp(%(collected_at)s), %(type)s, %(body)s, %(authed)s)
            ON CONFLICT (type, collected_at, body, authenticated) DO UPDATE SET count = beacons.count + 1, received_at = now();
        """, dict(collected_at=collected_at, type=path, body=body, authed=authenticated))
        pg.commit()
    except Exception as e:
        pg.rollback()
        raise e
        success = False

    resp = make_response("", 204 if success else 500)

    return resp

if __name__ == "__main__":
    app.run()
