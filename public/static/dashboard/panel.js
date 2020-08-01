
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

export class Panel {
    constructor(data = {}) {
        this.uuid = uuidv4();
        this.parent = null;
        this._children = {};
        this.data = data;
        this.data.type = data.type || "row";
        this.data.name = data.name || this.uuid;
    }

    //-- A --

    add( panels ){
        for(var panel of panels){
            if(this.tabExists(panel.data.name)){
                throw "A panel or tab with name '" + panel.data.name + "' already exists"
            }

            if(panel.parent != null)
                throw "The element has already a parent"

            if(panel instanceof Panel){
                this._children[panel.uuid] = panel;
                panel.parent = this;
            } else{
                throw "A panel is required";
            }
        }
    }

    //-- G --

    getName(){
        return this.data.name;
    }

    getType(){
        return this.data.type || null;
    }

    //-- G --
     
    getDashboard(){
        if(this.parent instanceof Panel)
            return this.parent.getDashboard();
        else
            return this.parent;
    }

    getLayout(){
        return this.getDashboard().getLayout();
    }

    getConfig(){
        var childrenConfigs = [];
        for(var i in this._children){
            var panel = this._children[i];
            childrenConfigs.push(panel.getConfig());
        }

        var config = {
            type: this.data.type,
            content: childrenConfigs
        };

        return config;
    }

    getTabByName(name){
        for(var i in this._children){
            var elem = this._children[i];
            if(elem instanceof Tab){
                if(elem.getName() == name)
                    return elem;
            } else{
                //traverse the panel to check for sub-elements
                return elem.getTabByName(name)
            }
        }
        return null;
    }
    
    tabExists(name){
        return this.getTabByName(name) != null
    }

    //-- I --

    //-- M --

    //-- R --


    //-- S --

    //setName( name ){
    //    this.data.name = name;
    //}

    //-- R --

    remove( panels ){
        for(var panel in panels){
            delete this._children[panel.uuid];
            panel.parent = null;
        }
    }

    //-- V --

    view(){
        throw "Not allowed";
    }
}
Panel.componentName = 'tab';

export class Row extends Panel {
    
    constructor(data = {}) {
        super(data);
        this.data.type = "row";
    }
    
}

export class Column extends Panel {
    
    constructor(data = {}) {
        super(data);
        this.data.type = "column";
    }
}


export class Stack extends Panel {
    
    constructor(data = {}) {
        super(data);
        this.data.type = "stack";
    }

}

export class Tab extends Panel{
    
    constructor(data = {}) {
        super(data);
        this.data.type = "component";
        this.data.title = data.title || "Tab";
        this.data.componentName = Panel.componentName;
        this.data.componentState = data.componentState || {};
        this.data.componentState.HTMLContent = data.componentState.HTMLContent || "";
    }

    //-- A --

    add( child ){
        throw "Cannot add panel to a tab";
    }

    //-- G --

    getTitle(){
        return this.data.title;
    }

    getState(){
        return this.data.componentState;
    }

    getHTMLContent(){
        if(this.getState() != null){
            return this.getState().HTMLContent;
        } else{
            return "";
        }
    }

    getConfig(){
        var config = {
            type: this.getType(),
            title: this.getTitle(),
            componentName: Panel.componentName,
            componentState: {
                uuid: this.uuid,
                HTMLContent : this.getHTMLContent()
        }};
        return config;
    }

    //-- L --

    load( url, data = {} ){
        var that = this;
        var xobj = new XMLHttpRequest();
        data.type = data.type || "html"
        data.onload = data.onload || function(){}

        var mime = "text/html"
        if(data.type == "json"){
            mime = "applciation/json"
        }else if(data.type == "text"){
            mime = "text/plain; charset=utf8" 
        }

        xobj.upload.addEventListener("progress", updateProgress, false);
        xobj.upload.addEventListener("load", transferComplete, false);
        xobj.upload.addEventListener("error", transferFailed, false);
        xobj.upload.addEventListener("abort", transferCanceled, false);

        xobj.overrideMimeType(mime);
        xobj.open('GET', url, true);
        xobj.onreadystatechange = function () {
            if (this.readyState == 4 && this.status == 200) {
                that.setHTMLContent(xobj.responseText);
                data.onload(xobj.responseText);
            } else{
                // nothing
            }
        }
        xobj.send(null);  

        function updateProgress (oEvent) {
            if (oEvent.lengthComputable) {
                var percentComplete = oEvent.loaded / oEvent.total;
                that.setHTMLContent(percentComplete+"");
            } else {
                // Impossible de calculer la progression puisque la taille totale est inconnue
            }
        }

        function transferComplete(evt) {
            that.setHTMLContent("Tranfert done");
        }
        
        function transferFailed(evt) {
            that.setHTMLContent("An error occured");
        }
        
        function transferCanceled(evt) {
            that.setHTMLContent("Loading cenceled");
        }
    }

    //-- R --

    remove( child ){
        throw "A tab has no elements";
    }

    //-- S --

    setTitle( title ){
        this.data.title = title;
    }

    setHTMLContent( html ){
        if(this.getState() != null){
            document.getElementById("gws-dashboard-tab-content-"+this.uuid).innerHTML = html
            return this.data.componentState.HTMLContent = html;
        }
    }

}

Row.type = "row";
Column.type = "column";
Stack.type = "stack";
Tab.type = "component";