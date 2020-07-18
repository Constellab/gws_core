/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import { Panel } from "./panel.js";
import { Stack } from "./panel.js";
import { Row } from "./panel.js";
import { Column } from "./panel.js";

class Leftbar{
    constructor(parent) {
        this.parent = parent;
        this._buttons = {};
    }

    //-- A -- 
    addButton(name, icon, callback){
        var container = document.querySelector("#gws-dashboard-sidebar-"+this.parent.uuid);
        var btn = document.createElement('div');
        btn.classList.add("left-toolbar-btn")
        btn.innerHTML = `<i class="`+icon+`"></i>`;
        container.appendChild(btn);
        this._buttons[name] = btn;
        this.onclick(name, callback);
    }

    addSeparator(){
        var container = document.querySelector("#gws-dashboard-sidebar-"+this.parent.uuid);
        var hr = document.createElement('hr');
        hr.classList.add("")
        container.appendChild(hr);
    }

    //-- G --
    
    getButton(name){
        return this._buttons[name];
    }

    //-- O --

    onclick(name, callback){
        if(typeof callback === "string"){
            this._buttons[name].onclick = function(){ eval(callback); }
        } else{
            this._buttons[name].onclick = callback;
        }
    }

    //-- V --

    _view(){
        //add btn using <g-left-btn> tags
        var buttons = document.querySelectorAll("x-gws-element.gws-dashboard-left-btn");
        var btn_tab = []
        for(var b of buttons){
            var pos = b.dataset.position || 0
            btn_tab.push(b)
        }

        btn_tab.sort( function(a,b){
            return (b.dataset.position || 0) - (a.dataset.position || 0)
        })

        for(var b of btn_tab){
            var name = b.dataset.name
            var icon = b.dataset.icon
            var fun = b.dataset.onclick.replace(/[^a-zA-Z\.]/g,";");
            if(!fun.startsWith("window")){
                fun = "window."+fun;
            }
            this.addButton(name, icon, fun+"()")
        }
    }
}

export class Dashboard {

    constructor(data = {}) {
        this.uuid = uuidv4();

        this.canvas = data.canvas || null;
        if(typeof this.canvas === "string")
            this.canvas = document.querySelector(this.canvas);

        this.data = data;
        this._panel = null;
        this._layout = null;
        this._leftBar = new Leftbar(this);

        if(!window.hasOwnProperty("gws"))
            window.gws = {};
        window.gws.dashboard = this;
    }

    //-- A --

    addTab(){
        
    }

    //-- G --

    getLeftBar(){
        return this._leftBar;
    }

    getLayout(){
        return this._layout;
    }

    getConfig(){
        var c = { 
            content: [ this._panel.getConfig() ]
        }
        return c;
    }

    getWidth(){
        return this.canvas.offsetWidth;
    }

    getHeight(){
        return this.canvas.offsetHeight;
    }

    //-- I --

    isVisible(){
        return this._layout != null;
    }

    //-- O --

    //-- R --

    refreshSize(){
        var h = document.getElementById(`gws-dashboard-${this.uuid}`).offsetHeight;
        var topH = document.getElementById(`gws-dashboard-top-bar-${this.uuid}`).offsetHeight;
        var bottomH = document.getElementById(`gws-dashboard-bottom-bar-${this.uuid}`).offsetHeight;
        h = (h - topH - bottomH) + "px";
        document.getElementById(`gws-dashboard-main-bar-${this.uuid}`).style.height = h;
        this._layout.updateSize(this.getWidth(), this.getHeight());
    }

    removePanel( ){
        this._panel.parent = null;
        this._panel = null;
    }

    //-- S --

    setPanel( panel ){
        if(panel instanceof Row || panel instanceof Column || panel instanceof Stack){
            this._panel = panel;
            this._panel.parent = this;
        } else{
            throw "A Row, Column or Stack panel is required"
        }
    }

    setHeight( h ){
        this.canvas.style.height = h
    }

    setWidth( w ){
        this.canvas.style.width = w
    }   

    removeAllPanels(){
        
    }

    //-- V --

    view(){
        if(this.isVisible())
            return;

        var html = `
            <div id="gws-dashboard-`+this.uuid+`" class="gws-dashboard">
                <div id="gws-dashboard-top-bar-`+this.uuid+`" class="gws-dashboard-top-bar padding-5">
                    <div id="gws-dashboard-logo`+this.uuid+`" class="gws-dashboard-logo"></div>
                    <input class="gws-input"/>
                </div>
                <div id="gws-dashboard-main-bar-`+this.uuid+`" class="gws-dashboard-main-bar">
                    <div id="gws-dashboard-sidebar-`+this.uuid+`" class="gws-dashboard-sidebar"></div>
                    <div id="gws-dashboard-content-`+this.uuid+`" class="gws-dashboard-content"></div>
                </div>
                <div id="gws-dashboard-bottom-bar-`+this.uuid+`" class="gws-dashboard-bottom-bar-">
                    <div id="bottom-grid-`+this.uuid+`" class="grid"></div>
                </div>
            </div>
            `;
        this.canvas.innerHTML = html;

        // init golden layout
        var that = this;
        this._layout = new window.GoldenLayout( this.getConfig(), "#gws-dashboard-content-"+this.uuid );
        this._layout.registerComponent( Panel.componentName, function( container, state ){
            container.getElement().html(state.HTMLContent);
        });

        this.refreshSize();
        this._layout.init();
        window.addEventListener('resize', function () {
            that.refreshSize();
        });

        this._leftBar._view();
    }
    
}