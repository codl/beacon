# beacon

a web service that indexes events in elasticsearch

logstash is a trash fire but elasticsearch and kibana are nice so i made this to
replace my use of logstash

## setup

```
$ pip install -r requirements.txt
$ env BEACON_ELASTICSEARCH="127.0.0.1:9200" BEACON_PREFIX="beacon-" python beacon.py
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

you can and should also run it in your favourite wsgi server

```
$ env BEACON_ELASTICSEARCH="…" gunicorn beacon:app
```

### env vars
* `BEACON_ELASTICSEARCH` points at elasticsearch. default: `127.0.0.1:9200`
* `BEACON_PREFIX` defines the prefix of indices that will be created.
    the date will be appended
    default: `beacon-`
* `BEACON_INSECURE` if set, cookies will not have the secure flag. use this if
    you are not running beacon over https

## usage

```
$ curl -XPOST http://127.0.0.1:5000/some/event -d 'key=value'
$ # or
$ curl -XPOST http://127.0.0.1:5000/some/event \
    -H "Content-Type: application/json" \
    -d '{"key": "value"}'
```

GET requests return a 1x1px transparent png so you can insert it as an image in a web page

```
<img src="http://127.0.0.1:5000/some/event?key=value" />
```
