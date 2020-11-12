
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

class gws{

    static send(request) {   
        var contentType = "text/html"
        if(request.type == "json")
            var contentType = "application/json"
            
        request.method = request.method || "GET"
        fetch('?only_inner_html=true', { 
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

    static loadPage(onload){
        gws.send({
            "url": "?only_inner_html=true",
            "type": "application/html",
            "method": "GET",
            "success":function(html){
                document.querySelector(".page-content").innerHTML = html
                GView.upgradeAll()
                onload()
            },
            "failure":function(html){
                document.querySelector(".page-content").innerHTML = html
                onload()
            }
        })
    }
}