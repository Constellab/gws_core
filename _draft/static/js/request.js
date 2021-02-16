
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

class _Request{

    static send(request) {   
        var contentType = "text/html"
        if(request.type == "json")
            var contentType = "application/json"
            
        request.method = request.method || "GET"
        fetch(request.url, { 
            method: request.method,
            headers: new Headers({
                "Content-Type": contentType,
            })
        }).then(function(response) {
            if(request.type == "json"){
                return response.json()
            } else{
                return response.text()
            }
        }).then(function(data) {
            request.success(data);
        }).catch(function(error) {
            request.failure(error.message);
        });
    }

}

window.gws = window.gws || {}
window.gws.Request = _Request