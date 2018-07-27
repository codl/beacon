from flask import Flask, request, send_file, make_response, render_template
from flask_cors import CORS
from os import getenv
import psycopg2

app = Flask("beacon")
CORS(app, max_age=60*60*24*365, supports_credentials=True)

pg = psycopg2.connect(getenv("BEACON_POSTGRESQL", ""))

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
    event = {
        "timestamp": int(time.time()*1000), #es requires milliseconds
        "method": request.method,
        "path": request.path,
        "client": request.remote_addr,
        "headers": dict(request.headers),
        "headers_raw": ["%s: %s" % header for header in request.headers]
    }

    params = list(request.values.items())
    if len(params) > 0:
        body = dict(params)
    elif request.is_json or request.content_type == "application/csp_report":
        body = request.get_json(force = True);

    cur = pg.cursor()

    cur.execute("""
        INSERT INTO beacons (created_at, type, body)
        VALUES (now(), %s, %s);
    """, (path, body))
    pg.commit()

    if(request.method == "GET"):
        resp = make_response(send_file("pixel.png", mimetype="image/png",
            add_etags=False, cache_timeout=0),
            200)
    else:
        resp = make_response("", 204)

    return resp

def setup_db():
    cur = pg.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS beacons (
            id serial PRIMARY KEY,
            created_at timestamp with time zone,
            type text,
            body jsonb
        );
        CREATE INDEX IF NOT EXISTS idx_beacons_created_at ON beacons (created_at);
        CREATE INDEX IF NOT EXISTS idx_beacons_type_created_at ON beacons (type, created_at);
        ''')
    pg.commit()


app.before_first_request(setup_db)

if __name__ == "__main__":
    app.run()
