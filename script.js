window.Beacon = (function(){

    let beacon_script = document.currentScript;

    function flag(f){
        return typeof beacon_script.dataset[f] == "string";
    }

    let Beacon = function(path, data){
        path = "https://beacon.codl.fr/test" + path;
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

    return Beacon;
}())
