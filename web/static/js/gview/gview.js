
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */


var GViewCollector = {
    templates : {},
    views : {}
}

class GViewTemplate{

    constructor( data ) { 
        this._class = data.class
        this._render = function(d){
            var response = data.render(d)
            if(typeof response == "function"){
                return response
            } else{
                return response.trim()
            }
        }
        GViewCollector.templates[this._class] = this
    }
    
}

class GView{

    constructor( elem ) { 
        this._id = elem.id || uuidv4()
        this._dom = elem
        this._domTarget = elem
        this._dom.id = this._id
        this._className = GView.className(elem)
        GViewCollector.views[elem.id] = elem
    }

    //-- C --

    static className(elem){
        var className = ""
        if(GView.isGView(elem)){
            className = elem.className
        }
        return className
    }

    //-- G --    

    static get(request) {   
        request.method = "GET"
        GWS.send(request)
    }

    //-- I --

    static isGView(element){
        try{
            return element.className.startsWith(GView.classPrefix)
        }catch{ 
            return false
        }
    }

    //-- P --

    static post(request) {   
        request.method = "POST"
        GWS.send(request)
    }

    //-- R --

    render( data ){
        var template = GViewCollector.templates[this._className]
        if(template != null){
            if(this._dom.hasAttribute("target")){
                var target = this._dom.getAttribute("target")
                this._domTarget = document.querySelector(target)
                var response = template._render(data)
                if(typeof response == "function"){
                    response(this._domTarget, data)
                }else{
                    this._domTarget.innerHTML = response
                }
            } else{
                var response = template._render(data)
                if(typeof response == "function"){
                    response(this._dom, data)
                }else{
                    this._dom.innerHTML = response
                }
                this._dom.style.display = "initial"
            }

            if(this._dom.userData == null){
                this._dom.userData = {}
            }
            this._dom.userData["gview"] = this
        }   
    }

    //-- S --

    static selectAll(){
        return document.querySelectorAll("div[class^='"+GView.classPrefix+"']")
    }

    //-- U --

    static upgradeAll(force) {
        force = force || false;
        var elements = GView.selectAll()
        elements.forEach(elem => {
            GView.upgrade(elem, force)
        });
    }

    static upgrade(element, force) {
        force = force || false;
        if(typeof(element) == "string"){
            element = document.querySelector(element)
            if(element == null) return;
        }
        
        if(!GView.isGView(element)) return;
        if(element.dataset.isLoaded && !force) return;
        var data = {}
        if(element.hasAttribute("json")){
            data = JSON.parse(element.innerText)
        } else{
            //read HTML fields
            for(var i = 0; i<element.childNodes.length; i++){
                var child = element.childNodes[i]
                if (typeof child.tagName == "string"){
                    if (child.tagName.toLowerCase() == "div"){
                        var attr = child.attributes[0].name
                        data[attr] = child.innerHTML
                        child.innerHTML = ""    //remove template HTML content to prevent id collisions
                    } else if(child.tagName.toLowerCase() == "script"){
                        eval(child.innerHTML)
                    }
                }
            }
            
            //read TEXT fields
            for(i in element.dataset){
                data[i] = element.dataset[i]
            }
        }
        
        if(element.hasAttribute("target")){
            if(loadDelayed){
                var view = new GView(element)
                view.render(data)
            } else{
                delayedElements.push(element)
            }
        } else{
            var view = new GView(element)
            view.render(data)
        }

        element.dataset.isLoaded = true
    }
}

GView.classPrefix = "gview:";

// window.addEventListener("DOMContentLoaded", function () {
//     GView.upgradeAll()
// })

/**
 * Global Observer
 */


document.addEventListener('click',function(e){
    isSubmitButtonClicked = 
                    e.target 
                    && e.target.tagName.toLowerCase() == "button" 
                    && e.target.hasAttribute("type")
                    && e.target.getAttribute("type") == "submit"

    if(isSubmitButtonClicked){
        url = e.target.getAttribute("url");
        GView.post({
            "url": url,
            "type": "html"
        })
    }
});
