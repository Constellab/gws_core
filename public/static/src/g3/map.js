/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import { Element } from "./element.js";
import { Sphere } from "./node.js";
import { Node } from "./node.js";
import { Line } from "./line.js";
import * as FORCE from "./layout/force.js";
import * as UTILS from "../utils/files.js";
import * as COLOR from '../utils/color.js'

import * as THREE from '/static/dist/three-js/build/three.module.js';
import { TrackballControls } from '/static/dist/three-js/examples/jsm/controls/TrackballControls.js';
import { DragControls } from '/static/dist/three-js/examples/jsm/controls/DragControls.js';

export class Map {

    constructor(data = {}) {
        this.canvas = data.canvas || null;
        if(typeof this.canvas === "string")
            this.canvas = document.querySelector(this.canvas);

        this.children           = {};
        this.nodes              = {};
        this.lines              = {};

        this.uuid               = uuidv4();
        this.data               = data;
        this.data.id            = data.id || this.uuid;
        this.data.style         = data.style || {};
        this.data.style.width   = data.style.width ||  null;
        this.data.style.height  = data.style.height || null;
        this.data.style.color   = data.style.color || "#000";
        this.data.layout        = data.layout || "force";
        this.data.nodeColor     = data.nodeColor || null;

        this._renderer          = null;
        this._scene             = null;
        this._camera            = null;
        this._trackballControls     = null;
        this._dragControls      = null;
        //this._raycaster         = null;
        this._mouse             = {x: 0, y: 0};
        this._objects           = [];
        this._draggableObjects  = [];

        this._lastOveredElement    = null;
        this._lastClickedElement    = null;
        this._lastDragStartTime     = new Date();
        this._isTooltipVisible      = false;
        this._isClicked             = false;

        //build on the fly once
        this._layoutNodes           = [];
        this._layoutLinks           = [];
        this._layoutSimulation      = null;
    }

    add( element ){
        if(element instanceof Element){
            if(element.parent != null)
                throw "The element has already a parent"
            
            this.children[element.uuid] = element;
            element.parent = this;

            var colorList = {};
            if(element instanceof Node){
                this.nodes[element.getId()] = element;
                
                if(this.data.nodeColor != null){
                    if(this.data.nodeColor === true){
                        element.data.style.color = COLOR.Color.randomColor();
                    } else if(typeof this.data.nodeColor === "string"){
                        var colorProp = (element.data[this.data.nodeColor]+"") || "0";
                        
                        if(!colorList.hasOwnProperty(colorProp))
                            colorList[colorProp] = COLOR.Palette.randomColor();
                        
                        element.data.style.color = colorList[colorProp];
                    }
                }

            }

            if(element instanceof Line)
                this.lines[element.getId()] = element;

            if(this._scene != null){
                var o = element.three();
                this._scene.add(o);
                this._objects.push(o);

                if(element.isDraggable())
                    this._draggableObjects.push(o);
            }
        } else{
            throw "The element must be a node or a line";
        }
    }
    

    //-- C --

    //-- D --

    static _drag(e){
        var elem = e.object.userData.g3;
        if(!elem.isDraggable())
            return
        //Line.clickedPoint.three().visible = false;
        if(elem instanceof Node)
            elem.updateLinePositions();
    }

    static _dragEnd(e){
        var elem = e.object.userData.g3;
        var that = elem.parent;
        var elapseTime = ((new Date()) - that._lastDragStartTime);

        if(elapseTime < 300 && elem.isClickable()){
            Map._mouseClick(e);
        }

        if(!elem.isDraggable())
            return

        
        that._trackballControls.enabled = true;
        e.object.material.emissive.set( 0xaaaaaa );
    }

    static _dragStart(e){
        var elem = e.object.userData.g3;
        var that = elem.parent;
        that._lastDragStartTime = new Date();

        if(!elem.isDraggable())
            return

        if(that._layoutSimulation != null)
            that._layoutSimulation.stop();

        that._trackballControls.enabled = false;
        that.hideTooltip();
        e.object.material.emissive.set( 0xaaaaaa );
        this._isClicked = false;
    }

    //-- F --
    
    static loadJSONFile( url, callback ){
        UTILS.loadJSONFile(url, callback);
    }

    loadJSON( json ){
        for(var nodeData of json.nodes){
            var node = new Sphere({
                id: nodeData.id,
                name: nodeData.id,
                group: nodeData.group || null,
            });
            this.add(node);
        }

        for(var linkData of json.links){
            var link = new Line({
                id: linkData.id,
                name: linkData.id,
                value: linkData.value || null,
                nodes: [this.nodes[linkData.source], this.nodes[linkData.target]]
            });
            this.add(link);
        }
    }

    //-- G --

    getId(){
        return this.data.id;
    }

    getCamera(){
        return this._camera;
    }

    getTrackballControls(){
        return this._trackballControls;
    }

    getDragControls(){
        return this._dragControls;
    }

    getScene(){
        return this._scene;
    }

    // static _getRaycastIntersections( e ){
    //     var that = e.target.userData.g3;
    //     //1. sets the mouse position with a coordinate system where the center
    //     //   of the screen is the origin
    //     that._mouse.x = ( (e.clientX-that.canvas.offsetLeft) / that.canvas.offsetWidth ) * 2 - 1;
    //     that._mouse.y = - ( (e.clientY-that.canvas.offsetTop) / that.canvas.offsetHeight ) * 2 + 1;
    //     //2. set the picking ray from the camera position and mouse coordinates
    //     that._raycaster.setFromCamera( that._mouse, that._camera );    
    //     //3. compute intersections
    //     var recursive = false;
    //     var intersects = that._raycaster.intersectObjects( that._scene.children, recursive );
    //     return intersects;
    // }

    //-- H --

    hideTooltip(){
        var tooltip = document.querySelector("#g3-tooltip-"+this.uuid);
        tooltip.classList.remove("d-block");
        tooltip.classList.add("d-none");
        this._isTooltipVisible = false;
    }


    //-- I --

    //-- M --

    static _mouseOverOn(e){
        var elem = e.object.userData.g3;
        elem._mouseOverOn(e);
        var that = elem.parent;
        that._lastOveredElement = elem;
    }

    static _mouseOverOff(e){
        var elem = e.object.userData.g3;
        elem._mouseOverOff(e);
        var that = elem.parent;
        that._lastOveredElement = null;
    }

    static _mouseClick( e ){
        var that = null;
        var isClickedOnCanvas = (e instanceof  MouseEvent);
        if(isClickedOnCanvas){
            that = e.target.userData.g3;
            if(that._lastOveredElement == null)
                that.hideTooltip();
            
            that._lastClickedElement = null;
            return;
        }

        var elem = e.object.userData.g3;
        that = elem.parent;

        if(that._lastOveredElement == null){
            that.hideTooltip();
            that._lastClickedElement = null;
            return
        }

        if(that._lastClickedElement == that._lastOveredElement)
            return;

        that._lastOveredElement._mouseClick(e);
        that._lastClickedElement = that._lastOveredElement;
        that.showTooltip(that._mouse, that._lastOveredElement)
    }


    static _mouseMove( e ){
        var that = e.target.userData.g3;
        that._mouse.x = ( (e.clientX-that.canvas.offsetLeft) / that.canvas.offsetWidth ) * 2 - 1;
        that._mouse.y = - ( (e.clientY-that.canvas.offsetTop) / that.canvas.offsetHeight ) * 2 + 1;
    }


    //-- R --

    remove( element ){
        delete this.children[element.uuid];

        if(element instanceof Node)
            delete this.nodes[element.getId()]

        if(element instanceof Line)
            delete this.lines[element.getId()]

        element.parent = null;
    }

    //-- S --

    showTooltip(mousePosition, node){
        if(node.getName() == ""){
            return;
        }

        var tooltip = document.querySelector("#g3-tooltip-"+this.uuid);
        tooltip.dataset.g3Id = this.getId();
        tooltip.innerHTML = `
            <div class="g3-tooltip-title">
                `+node.getName()+`
            </div>
            <div class="g3-tooltip-text">
                `+node.getDescription()+`
            </div>
        `;

        tooltip.classList.add("d-block");
        tooltip.classList.remove("d-none");

        //shift x position
        var xshift = tooltip.offsetWidth / 2;
        var left = this.canvas.offsetWidth * (mousePosition.x + 1) / 2 + this.canvas.offsetLeft - xshift;
        tooltip.style.left = left + "px";
        
        //shift y position
        var yshift = -tooltip.offsetHeight-15;
        var top = - this.canvas.offsetHeight * (mousePosition.y - 1) / 2 + this.canvas.offsetTop + yshift;
        tooltip.style.top = top + "px";

        this._isTooltipVisible = true;
    }

    setLayout(){ 
        var layout = new Springy.Layout.ForceDirected(
            graph,
            400.0, // Spring stiffness
            400.0, // Node repulsion
            0.5 // Damping
        );

        var renderer = new Springy.Renderer(
            layout,
            function clear() {
              // code to clear screen
            },
            function drawEdge(edge, p1, p2) {
              // draw an edge
            },
            function drawNode(node, p) {
              // draw a node
            }
        );
        render.start()
    }

    //-- U --

    //-- V --

    view( canvas ) {
        if(this._renderer != null)
            return;

        if(typeof canvas === "string")
            this.canvas = document.getElementById(canvas) || document.querySelector("#"+canvas);
        else if(canvas instanceof HTMLElement)
            this.canvas = canvas
        
        var tooltip = document.createElement('div');
        tooltip.setAttribute("id", "g3-tooltip-"+this.uuid);
        tooltip.classList.add("g3-tooltip");
        document.body.appendChild(tooltip);
        if(!tooltip.hasOwnProperty("userData"))
            tooltip.userData = {};
        tooltip.userData.g3 = this;

        var that = this;
        var w = this.canvas.offsetWidth;
        var h = this.canvas.offsetHeight;

        //renderer
        this._renderer = new THREE.WebGLRenderer({ antialias: true });
        this._renderer.setSize(w, h);
        this._renderer.setPixelRatio(devicePixelRatio);
        this.canvas.innerHTML = "";
        this.canvas.appendChild( this._renderer.domElement );
        this.canvas.classList.add("g3-map");

        //camera
        const skyRadius = 50000;
        const fov = 25;
        const aspect = w / h;
        const near = 1;
        const far = skyRadius * 2.5;
        const dist = 1000;
        this._camera = new THREE.PerspectiveCamera( fov, aspect, near, far );
        this._camera.position.set(0, 0, dist);

        //scene
        this._scene = new THREE.Scene();
        this._scene.add(this._camera);
        this._scene.background = new THREE.Color( 0x000011 );

        //all elements to the scene
        for(var uuid in this.children){
            var elem = this.children[uuid];
            //console.log(uuid)
            //console.log(elem)
            var o = elem.three();
            this._scene.add(o);
            this._objects.push(o);
            var isClickable = elem.isDraggable() || elem.isClickable();
            if( elem instanceof Element && isClickable )
                this._draggableObjects.push(o);
            
        }
        
        Line.clickedPoint = new Sphere({style:{
            size: Sphere.defaultSize/3,
            color: "#fff"
        }});
        Line.clickedPoint.three().visible = false;
        Line.clickedPoint.data.isDraggable = false;
        Line.clickedPoint.data.isClickable = true;
        this.add(Line.clickedPoint);

        //light
        this._scene.add(new THREE.AmbientLight(0xbbbbbb));
        this._scene.add(new THREE.DirectionalLight(0xffffff, 0.5));
        this._scene.lookAt(this._scene.position);

        //orbit controls
        this._trackballControls = new TrackballControls( this._camera, this._renderer.domElement );
        this._trackballControls.enableZoom  = true;
        this._trackballControls.zoomSpeed   = 1.2;
        this._trackballControls.autoRotate  = false;
        this._trackballControls.rotateSpeed = 3;
        this._trackballControls.panSpeed    = 0.8;    
        this._trackballControls.enablePan   = true;
        this._trackballControls.minDistance = 0.1;
        this._trackballControls.maxDistance = skyRadius;
        this._trackballControls.addEventListener("change", changeOrbitControl);
        //this._trackballControls.addEventListener("end", endOrbitControl);
        this._trackballControls.update();
        
        //drag controls
        this._dragControls = new DragControls( this._draggableObjects, this._camera, this._renderer.domElement );
        this._dragControls.addEventListener('dragstart', Map._dragStart);
        this._dragControls.addEventListener('drag', Map._drag);
        this._dragControls.addEventListener('dragend', Map._dragEnd);
        this._dragControls.addEventListener('hoveron', Map._mouseOverOn);
        this._dragControls.addEventListener('hoveroff', Map._mouseOverOff);

        //raycaster
        //this._raycaster = new THREE.Raycaster();
        //this._raycaster.params.Line.threshold = 0.5;

        //rendering
        if(!this._renderer.domElement.hasOwnProperty("userData"))
            this._renderer.domElement.userData = {};
        this._renderer.domElement.userData.g3 = this;
        this._renderer.domElement.addEventListener('click', Map._mouseClick, false );
        //this._renderer.domElement.addEventListener('dblclick', Map._mouseDblClick, false );
        this._renderer.domElement.addEventListener('mousemove', Map._mouseMove, false);
        //this._renderer.domElement.addEventListener('mouseout', Map._mouseOut, true);
        this._renderer.render(this._scene, this._camera);

        //events
        window.addEventListener('resize', onWindowResize, false);
        function onWindowResize(event) {
            that._renderer.setSize(that.canvas.offsetWidth, that.canvas.offsetHeight);
            that._camera.aspect = that.canvas.offsetWidth / that.canvas.offsetHeight;
            that._camera.updateProjectionMatrix();
        }

        function changeOrbitControl(){
            that.hideTooltip();
            //that._dragControls.enabled = false;
            that._renderer.render(that._scene, that._camera);
        }

        // function endOrbitControl(){
        //     that._dragControls.enabled = true;
        // }

        //animate
        function animate() {
            requestAnimationFrame(animate);
            that._camera.updateMatrixWorld();
            that._renderer.render(that._scene, that._camera);
            that._trackballControls.update();
        }
        animate();

        if(this.data.layout == "force"){
            FORCE.forceLayout(this);
        }

        var text = 'Left-click: rotate, Mouse-wheel/middle-click: zoom, Right-click: pan';
    }
}
