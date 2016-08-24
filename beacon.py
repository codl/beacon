import logging
from flask import Flask, request, send_file, make_response
from flask_cors import CORS
from os import getenv
from elasticsearch import Elasticsearch
import json
import time, datetime
import random

logging.getLogger("elasticsearch").setLevel(logging.ERROR)

app = Flask("beacon")
CORS(app)

INDEX_PREFIX = getenv("BEACON_PREFIX", "beacon-")

try:
    es = Elasticsearch([getenv("BEACON_ELASTICSEARCH", "localhost:9200")])
    es.indices.put_template(name="codl_beacon",
        body={
            "template": "%s*" % (INDEX_PREFIX,),
            "order": 10,
            "mappings": {
                "beacon": {
                    "properties": {
                        "timestamp": { "type": "date" },
                        "path": { "type": "string", "index": "not_analyzed" },
                        "method": { "type": "string", "index": "not_analyzed" },
                    },
                    "dynamic_templates": [
                        {
                            "strings": {
                                "match_mapping_type": "string",
                                "mapping": {
                                    "type": "string",
                                    "fields": {
                                        "raw": {
                                            "type": "string",
                                            "index": "not_analyzed"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        })
except Exception as e:
    logging.critical("Couldn't connect to Elasticsearch: %s", e)
    exit(1)

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode()

        return json.JSONEncoder.default(self, obj)

@app.route("/favicon.ico")
def favicon():
    return "no", 404

@app.route("/robots.txt")
def robots():
    return "", 204

@app.route("/", methods={"GET", "POST"})
@app.route("/<path:path>", methods={"GET", "POST"})
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
        event["body"] = dict(params)
    if request.json:
        event["body"] = request.json

    dnt = request.headers.get("DNT") == "1"

    if not dnt:
        uid = request.cookies.get('uid')
        if not uid:
            uid = genid(8)
        event["uid"] = uid

    index_name = INDEX_PREFIX + datetime.date.today().isoformat()

    failed = False
    try:
        es.index(index=index_name, doc_type="beacon", body=json.dumps(event, cls=BytesEncoder))
    except Exception:
        logging.error("Couldn't insert into Elasticsearch")
        failed = True

    if(request.method == "GET"):
        resp = make_response(send_file("pixel.png", mimetype="image/png",
            add_etags=False, cache_timeout=0),
            500 if failed else 200)
    else:
        resp = make_response("", 500 if failed else 204)

    if dnt:
        resp.set_cookie('uid', expires=0)
    else:
        resp.set_cookie('uid', uid)
    return resp

def genid(length = 8):
    """
    Generates a random unique ID of specified length

    >>> import random
    >>> random.seed(0)
    >>> genid()
    'UoNWq.fw'
    >>> genid(16)
    'vpYQTiumBXYcw7h7'
    """
    ALLOWED_CHARS="-_.23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    return ''.join([random.choice(ALLOWED_CHARS) for _ in range(length)])

if __name__ == "__main__":
    app.run()
