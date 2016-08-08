from flask import Flask, request

app = Flask("beacon")

@app.route('/', defaults={'path': ''}, methods={"GET", "POST"})
@app.route("/<path:path>", methods={"GET", "POST"})
def recieve_beacon(path):
    ret = "<pre>bean %s<br/>" % (path,)
    for header in request.headers:
        ret += repr(header) + "<br>"
    for arg in request.values.items():
        ret += repr(arg) + "<br>"
    if request.json:
        ret += repr(request.json)
    return ret + "</pre>"

if __name__ == "__main__":
    app.run()
