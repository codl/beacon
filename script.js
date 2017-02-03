window.Beacon = (function(){

    let beacon_script = document.currentScript;

    function flag(f){
        if(!beacon_script || !beacon_script.dataset){
            return true;
        }
        return typeof beacon_script.dataset[f] == "string";
    }

    let Beacon = function(path, data){
        path = "https://beacon.codl.fr" + path;
        let xhr = new XMLHttpRequest();
        xhr.open("POST", path);
        xhr.setRequestHeader("content-type", "application/json");
        xhr.send(JSON.stringify(data));
    }

    if(!flag("no-onerror")){
        window.addEventListener("error", function(e){
            let message = e.message;
            let filename = e.filename;
            let lineno = e.lineno;
            let colno = e.colno;
            Beacon("/onerror", {error:{message: message, filename: filename, lineno: lineno, colno:colno}});
        });
    }

    if(!flag("no-visit")){
        Beacon("/visit/" + window.location.hostname, {});
    }

    function perf(){
        let data = {}
        let t = performance.timing;
        data.dns = t.domainLookupEnd - t.domainLookupStart;
        data.connect = t.connectEnd - t.connectStart;
        data.firstByte = t.responseStart - t.requestStart;
        data.transfer = t.responseEnd - t.responseStart;
        data.parse = t.domInteractive - t.domLoading;
        data.load = t.domComplete - t.domInteractive;
        data.domContentLoadedHandlers = t.domContentLoadedEventEnd - t.domContentLoadedEventStart;
        data.loadHandlers = t.loadEventEnd - t.loadEventStart;

        Beacon("/perf/" + window.location.hostname, {timing: data});
    }

    if(!flag("no-perf") && window.performance && performance.timing){
        if(document.readyState == "complete"){
            perf();
        }
        else{
            window.addEventListener("load", function(){
                setTimeout(perf, 0);
            });
        }
    }

    return Beacon;
}())
