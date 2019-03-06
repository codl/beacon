from flask import Flask, request, send_file, make_response, render_template
from flask_cors import CORS
import json
import time
from datetime import datetime, timezone
from db import get_pg

app = Flask("beacon")
CORS(app, max_age=60 * 60 * 24 * 365, supports_credentials=True)


@app.route("/favicon.ico")
def favicon():
    return "no", 404


@app.route("/robots.txt")
def robots():
    return "", 204


@app.route("/")
def index():
    return render_template("index.html")


def authenticate(request, pg):
    authenticated = False
    purpose = None
    cur = pg.cursor()

    auth = request.headers.get('authorization', '')
    if auth.startswith('Bearer '):
        auth = auth[7:]
        cur.execute('''SELECT purpose FROM auth_tokens WHERE token = %s''',
                    (auth, ))
        row = cur.fetchone()
        if row is not None:
            authenticated = True
            purpose = row[0]

    return authenticated, purpose


def insert_beacons(beacons, authed, purpose, pg):
    now = datetime.utcnow()
    cur = pg.cursor()
    for beacon in beacons:
        if 'beacon_type' not in beacon:
            raise Exception('Malformed beacon {}'.format(beacon))
        type_ = beacon['beacon_type']
        del beacon['beacon_type']

        collected_at = now
        if 'collected_at' in beacon:
            collected_at = datetime.fromtimestamp(
                beacon['collected_at'], tz=timezone.utc)
            del beacon['collected_at']

        body = json.dumps(body)

        cur.execute(
            """
            INSERT INTO beacons (collected_at, type, body, authenticated, auth_purpose, received_at)
            VALUES (%(collected_at)s, %(type)s, %(body)s, %(authed)s, %(auth_purpose)s, %(now)s)
            ON CONFLICT (type, collected_at, body, authenticated) DO UPDATE SET count = beacons.count + 1, received_at = %(now)s;
        """,
            dict(
                collected_at=collected_at,
                type=type_,
                body=body,
                authed=authed,
                auth_purpose=purpose,
                now=now))


@app.route("/collect", methods=('POST', ))
@app.route("/collect/", methods=('POST', ))
def collect():
    if not request.is_json:
        return "this isn't json", 415

    beacons = request.get_json()

    if not isinstance(beacons, list):
        return '400', 400

    pg = get_pg()

    authenticated, purpose = authenticate(request, pg)

    if not authenticated:
        return '403', 403

    try:
        insert_beacons(beacons, authenticated, purpose, pg)
    except Exception as e:
        return e, 400

    pg.commit()

    return 'OK', 200


@app.route("/collect/<path:path>", methods=("POST", ))
def collect_single(path=""):
    if not (request.is_json
            or request.content_type == "application/csp_report"):
        return "this isn't json", 415

    body = request.get_json(force=True)
    body['beacon_type'] = path

    pg = get_pg()
    cur = pg.cursor()

    authenticated, purpose = authenticate(request, pg)

    try:
        insert_beacons([body], authed, purpose, pg)
    except Exception as e:
        return e, 400

    return 'OK', 200


if __name__ == "__main__":
    app.run()
