/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import { Element } from './element.js'
import { Node } from './node.js'
import * as THREE from '/static/dis/three-js/build/three.module.js';

export class Line extends Element{
    
    constructor(data = {}) {
        super(data)
        this.data.style.width           = data.style.width || 0.3;
        this.data.style.hoverWidth      = data.style.hoverWidth || 0.6;
        this.data.style.color           = this.data.style.color || "#aaaaaa";
        this.data.style.hoverColor      = this.data.style.hoverColor || "#ffffff";
        this.data.nb_points             = data.nb_points || 0;

        this.data.isDraggable           = false;
        this.data.isClickable          = true;

        this._nodes             = [];
        this._three             = null;
        this._catmull           = null;
        this._geometryRadialSegments = 6;
        this._geometryTubularSegments = 30;
        this._effectiveGeometryTubularSegments = 30;

        var that = this;
        if(data.nodes != undefined){
            data.nodes.forEach(elm => {
                that.add(elm);
            });
        }

    }

    //-- A -- 

    add( node ){
        if(node instanceof Node){
            this._nodes.push(node);
            node._lines[this.getId()] = this;
        } else{
            throw "The element must be a node";
        }
    }

    //-- C --

    //-- G --

    
    
    getPositions(){
        var positions = [];
        for(var node of this._nodes){
            positions.push(node.getPosition());
        }
        return positions;
    }

    getPositionsAsVector3(){
        var points = [];
        for(var node of this._nodes){
            points.push(node.getPositionAsVector3());
        }
        return points;
    }

    getNodes(){
        return this._nodes;
    }

    //-- H --

    

    //-- I --

    isDraggable(){
        return false;
    }

    //-- M --

    _mouseClick( e ){
        super._mouseClick(e)
    }

    _mouseOverOn(e){
        super._mouseOverOn(e)
        this.three().material.color = new THREE.Color(this.data.style.hoverColor);
        this.three().geometry.size = new THREE.Color(this.data.style.hoverWidth);         
        this.three().material.needsUpdate = true;
    }

    _mouseOverOff(e){
        super._mouseOverOff(e)
        this.three().material.color = new THREE.Color(this.data.style.color);
        this.three().geometry.size = new THREE.Color(this.data.style.width);
        this.three().material.needsUpdate = true;
    }

    //-- R --

    remove( node ){
        for(var i=0; i<this._nodes.length; i++){
            elm = this._nodes[i];
            if(elm == node){
                this._nodes.splice(i,1);
                delete node._lines[this.getId()];
            }
        }
    }

    //-- T --

    three(){
        if(this._three != null)
            return this._three;

        var positions = [];
        for(var point of this._nodes){
            positions.push(point.position);
        }
        
        this._catmull = new THREE.CatmullRomCurve3(this.getPositionsAsVector3());
        this._catmull.curveType = "centripetal";
        this._catmull.tension = 0.2;
        
        const geometry = new THREE.TubeBufferGeometry(this._catmull, this._catmull.points.length == 2 ? 1 : this._geometryTubularSegments, this.data.style.width, this._geometryRadialSegments);
        const material = new THREE.MeshBasicMaterial({
            color: this.data.style.color, 
            transparent: true,
            opacity: 0.75
        })
        this._three = new THREE.Mesh( geometry, material );
        this._three.userData.g3 = this;
        return this._three;
    }

    //-- U --

    updatePosition(){
        this._catmull.points = this.getPositionsAsVector3();
        const geometry = new THREE.TubeBufferGeometry(this._catmull, this._catmull.points.length == 2 ? 1 : this._geometryTubularSegments, this.data.style.width, this._geometryRadialSegments);
        this._three.geometry.dispose();
        this._three.geometry = geometry;
        this._three.geometry.needsUpdate = true;
        this._three.geometry.verticesNeedUpdate = true;
    }
}