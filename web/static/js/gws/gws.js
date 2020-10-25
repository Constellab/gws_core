
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

class GWS{

    static send(request) {   
        request.type = request.type || "application/json"
        request.method = request.method || "GET"
        var xobj = new XMLHttpRequest();
        xobj.overrideMimeType(request.type);
        xobj.open(request.method, request.url, true);
        xobj.onreadystatechange = function () {
            if (xobj.readyState == XMLHttpRequest.DONE){
                if(xobj.status == 200) {
                    if(request.type == "application/json"){
                        request.success(JSON.parse(xobj.responseText));
                    } else{
                        request.success(xobj.responseText);
                    }
                } else{
                    console.log(xobj)
                    request.failure(xobj.response);
                }
            }
        };
        xobj.send(null);  
    }

    static openPage(){
        GWS.send({
            "url": "?only_inner_html=true",
            "type": "application/html",
            "method": "GET",
            "success":function(html){
                document.querySelector(".page-content").innerHTML = html
            },
            "failure":function(html){
                document.querySelector(".page-content").innerHTML = html
            }
        })
    }
}