
window.addEventListener("load", function(){

    const targetNode = document.body
    const config = { childList: true, subtree: true };
    const observer = new MutationObserver(function(mutationsList, observer){
        for(let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(e => {
                    createGWSNode(e)
                })
            }
        }
    });
    observer.observe(targetNode, config);

    var elements = document.querySelectorAll("x-gws")
    elements.forEach(elem => {
        createGWSNode(elem)
    });

    function createGWSNode(element){
        if(typeof element.tagName == "string" && element.tagName.toLowerCase() == "script"){
            if(element.dataset.lazy != undefined && element.dataset.lazy){
                eval(element.innerText)
            }
        }else if(typeof element.tagName == "string" && element.tagName.toLowerCase() == "x-gws"){
            console.log("gws element added")
            console.log(element)

            if(element.className == "gws-loader"){
                console.log("loader")
                console.log(element.innerText)
                eval(element.innerText)
            }
        }   

        
    }

})