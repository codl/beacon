from flask import Flask, request, send_file, make_response, render_template
from flask_cors import CORS
from os import getenv
import psycopg2
import json
import time

app = Flask("beacon")
CORS(app, max_age=60*60*24*365, supports_credentials=True)

pg = psycopg2.connect(getenv("BEACON_POSTGRESQL", ""), application_name="beacon")

@app.route("/favicon.ico")
def favicon():
    return "no", 404

@app.route("/robots.txt")
def robots():
    return "", 204

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/s")
def script():
    return send_file("script.js")


@app.route("/collect/<path:path>", methods={"GET", "POST"})
def recieve_beacon(path=""):

    params = list(request.values.items())
    if len(params) > 0:
        body = dict(params)
    elif request.is_json or request.content_type == "application/csp_report":
        body = request.get_json(force = True);

    collected_at = time.time()
    if 'collected_at' in body:
        collected_at = body['collected_at']
        del body['collected_at']

    body = json.dumps(body)

    cur = pg.cursor()

    success = True
    try:
        cur.execute("""
            INSERT INTO beacons (collected_at, type, body)
            VALUES (to_timestamp(%(collected_at)s), %(type)s, %(body)s)
            ON CONFLICT (type, collected_at, body) DO UPDATE SET count = beacons.count + 1, received_at = now();
        """, dict(collected_at=collected_at, type=path, body=body))
        pg.commit()
    except Exception as e:
        pg.rollback()
        raise e
        success = False

    if(request.method == "GET"):
        resp = make_response(send_file("pixel.png", mimetype="image/png",
            add_etags=False, cache_timeout=0),
            200 if success else 500)
    else:
        resp = make_response("", 204 if success else 500)

    return resp

def setup_db():
    cur = pg.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS beacons (
            id serial PRIMARY KEY,
            collected_at timestamp without time zone DEFAULT now(),
            received_at timestamp without time zone DEFAULT now(),
            type text,
            body jsonb,
            count integer DEFAULT 1,
            UNIQUE (type, collected_at, body)
        );
        CREATE INDEX IF NOT EXISTS idx_beacons_collected_at ON beacons (collected_at);
        CREATE INDEX IF NOT EXISTS idx_beacons_type_collected_at ON beacons (type, collected_at);
        ''')
    pg.commit()


app.before_first_request(setup_db)

if __name__ == "__main__":
    app.run()
