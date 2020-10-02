
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

    // static submit(request){
    //     data = GView.send(request)
    //     view = GViewCollector.views[data.id]
    //     view.render(data)
    // }

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

}

GView.classPrefix = "gview:";

/**
 * Global Observer
 */

window.addEventListener("load", function () {
    const targetNode = document.body
    const config = { childList: true, subtree: true };
    var delayedElements = []

    createCurrentElements()

    const observer = new MutationObserver(function (mutationsList, observer) {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(e => {
                    createGView(e)
                })
            }
        }
        createDelayedElements()
    });
    observer.observe(targetNode, config);

    function createGView(element, loadDelayed) {
        if(loadDelayed == null){
            loadDelayed = false
        }

        var isLazyScript = typeof element.tagName == "string" && element.tagName.toLowerCase() == "script"
        if (isLazyScript) {
            if (element.hasAttribute("lazy")) {
                eval(element.innerText)
            }
        } else {
            if (GView.isGView(element)) {       
                var data = {}
                if(element.hasAttribute("json")){
                    data = JSON.parse(element.innerText)
                } else{

                    //read HTML field
                    for(var i = 0; i<element.childNodes.length; i++){
                        child = element.childNodes[i]
                        if (typeof child.tagName == "string" && child.tagName.toLowerCase() == "div"){
                            var attr = child.attributes[0].name
                            data[attr] = child.innerHTML
                            child.innerHTML = ""    //remove template HTML content to prevent id collisions
                        }
                    }
                    
                    //read TEXT field
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
            }
        }
    }

    function createCurrentElements(){
        var elements = GView.selectAll()
        elements.forEach(elem => {
            createGView(elem)
        });
        createDelayedElements()
    }

    function createDelayedElements(){
        for (let i in delayedElements) {
            createGView(delayedElements[i], true)
        }
        delayedElements = []
    }
})

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

//  function createElementFromHTML(htmlString) {
//     var div = document.createElement('div');
//     div.innerHTML = htmlString.trim();
  
//     // Change this to div.childNodes to support multiple top-level nodes
//     return div.firstChild; 
//   }