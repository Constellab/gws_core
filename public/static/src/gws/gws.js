
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
                    console.log(xobj.readyState)
                    console.log(xobj.status)
                    request.failure(xobj.responseText);
                }
            }
        };
        xobj.send(null);  
    }

}