
class SearchBar{

    constructor(){
        this.className = "gws-top-search-bar"
        this.defaultDisplay = ""
    }

    static activate(){
        var btn = document.querySelector(".gws-top-search-bar--open-btn")
        btn.style.display = "inherit"
    }

    static deactivate(){
        var btn = document.querySelector(".gws-top-search-bar--open-btn")
        btn.style.display = "none"
    }

    static hide(){
        const bar = document.querySelector(".gws-top-search-bar");
        bar.style.left = "50%"
        bar.style.top = "-70px"
    }

    static show( action ){
        const bar = document.querySelector(".gws-top-search-bar")
        bar.style.top = "8px"
        bar.style.left = "50%"
    }

    static setAction(action){
        if(action != null){
            const form = document.querySelector(".gws-top-search-bar-form form")
            form.action = action
        }
    }

}

SearchBar.url = ""

window.addEventListener("click", function () {
    SearchBar.hide()
})

window.addEventListener("load", function () {
    let icon = document.querySelector(".gws-top-search-bar--open-btn")
    icon.addEventListener("click", function (event) {
        event.stopImmediatePropagation()
        SearchBar.show()
    })

    let bar = document.querySelector(".gws-top-search-bar")
    bar.addEventListener("click", function (event) {
        event.stopImmediatePropagation()
    })
})