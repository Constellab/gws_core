class _Model{

    constructor(){
    }
    
    static get(canvas, uri){
        _Experiment._send(canvas, "/prism-api/experiment/"+uri)
    }

    static get_list(canvas, page){
        page = page || 1
        _Experiment._send(canvas, "/prism-api/experiment/list?page="+page)
    }

    static _send(canvas,url){
        var request = {
            type: "json",
            method: "GET",
            url: url,
            success: function(data){
                canvas.innerHTML = _Experiment.render(data)
            }
        }
        window.gws.Request.send(request)
    }

    static render(data){

    }

}

window.gws = window.gws || {}
window.gws.Model = _Model;