import logging
from flask import Flask, request, send_file
from flask_cors import CORS
from os import getenv
from elasticsearch import Elasticsearch
import json
import time, datetime

logging.getLogger("elasticsearch").setLevel(logging.ERROR)

app = Flask("beacon")
CORS(app)


try:
    es = Elasticsearch([getenv("BEACON_ELASTICSEARCH", "localhost:9200")])
    es.info()
except Exception as e:
    logging.critical("Couldn't connect to Elasticsearch: %s", e)
    exit(1)

INDEX_PREFIX = getenv("BEACON_PREFIX", "beacon-")

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

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode()

        return json.JSONEncoder.default(self, obj)

@app.route("/favicon.ico")
def favicon():
    return "no", 404
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

    index_name = INDEX_PREFIX + datetime.date.today().isoformat()
    es.index(index=index_name, doc_type="beacon", body=json.dumps(event, cls=BytesEncoder))

    if(request.method == "GET"):
        return send_file("pixel.png", mimetype="image/png",
            add_etags=False, cache_timeout=0)
    else:
        return "", 204

if __name__ == "__main__":
    app.run()
