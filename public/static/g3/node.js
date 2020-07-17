/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import { Element } from './element.js'
import * as THREE from '/static/extern/three-js/build/three.module.js';

export class Node extends Element{

    constructor(data = {}) {
        super(data)
        this.data.style.size    = data.style.size || 4;
        this.data.style.color   = data.style.color || "#689c99";

        this.data.group         = data.group || 0;
        this.data.position      = data.position || {x: 0, y: 0, z: 0};
        this.data.position.x    = data.position.x || 50 * (Math.random() - Math.random());
        this.data.position.y    = data.position.y || 50 * (Math.random() - Math.random());
        this.data.position.z    = data.position.z || 50 * (Math.random() - Math.random());
        this._lines = {};
        this._three = null;
    }

    //-- C --

    //-- G --

    getPosition(){
        return this.data.position;
    }

    getPositionAsVector3(){
        if(this._three != null)
            return this._three.position;
        else
            return null;
    }

    //-- I --
    
    isLinkedTo( node ){
        for(var i in this._lines){
            var line = this._lines[i];
            if( line.getNodes().includes(node)  ){
                return true;
            }
        }
        return false;
    }

    //-- M --

    _mouseClick( e ){
        super._mouseClick(e)
    }

    _mouseOverOn(e){
        super._mouseOverOn(e)
        this._savedEmissiveHex = this._three.material.emissive.getHex();
        this._three.material.emissive.set(0xff0000);
    }

    _mouseOverOff(e){
        super._mouseOverOff(e)
        this._three.material.emissive.set(this._savedEmissiveHex);
    }

    //-- S --

    setPosition(position){
        this.data.position.x = position.x; 
        this.data.position.y = position.y;
        this.data.position.z = position.z;

        if(this._three != null)
            this._three.position.set(this.data.position.x, this.data.position.y, this.data.position.z);
    }

    //-- T --

    three(){
        throw "Node is an abstract class";
    }

    //-- U --

    updatePosition(){
        this._three.position.set(this.data.position.x, this.data.position.y, this.data.position.z);
        this.updateLinePositions();
    }

    updateLinePositions(){
        for(var i in this._lines){
            this._lines[i].updatePosition();
        }
    }
}

export class Box extends Node{

    constructor(data = {}) {
        super(data);
    }

    //-- G --


    //-- T -- 

    three(){
        if(this._three != null)
            return this._three;

        const geometry = new THREE.BoxGeometry(this.data.style.size, this.data.style.size, this.data.style.size);
        const material = new THREE.MeshPhysicalMaterial({
            color: this.data.style.color,
            transparent: true,
            opacity: 0.75
        });
        this._three = new THREE.Mesh(geometry, material);
        this._three.position.set(this.data.position.x, this.data.position.y, this.data.position.z);
        this._three.userData.g3 = this;
        return this._three;
    }
}

export class Sphere extends Node{

    constructor(data = {}) {
        super(data);
        this.data.size = data.size || Sphere.defaultSize;

        this._widthSegments = 8;
    }

    //-- T -- 

    three(){
        if(this._three != null)
            return this._three;

        const geometry = new THREE.SphereGeometry(this.data.style.size, this._widthSegments, this._widthSegments);
        const material = new THREE.MeshPhysicalMaterial({
            color: this.data.style.color,
            transparent: true,
            opacity: 0.75
        });
        this._three = new THREE.Mesh(geometry, material);
        this._three.position.set(this.data.position.x, this.data.position.y, this.data.position.z);
        this._three.userData.g3 = this;
        return this._three;
    }
}

Sphere.defaultSize = 1;

// export class HTMLElement extends Node{

//     constructor(data = {}) {
//         super(data);
//         this.data.content = data.content || "";
//         this.data.style.width = this.data.style.width || "100px";
//         this.data.style.height = this.data.style.height || "100px";
//         this.data.style.opacity = this.data.style.opacity || 0.75;
//     }

//     //-- C -- 

//     three(){
//         if(this._three != null)
//             return this._three;
        
//         var element = document.createElement( 'div' );
//         element.style.width = this.data.style.width;
//         element.style.height = this.data.style.height;
//         element.style.opacity = this.data.style.opacity;

//         element.innerHTML = this.data.content
//         this._three = new THREE.CSS3DObject( element );
//         this._three.userData.g3 = this;
//         return this._three;
//     }
// }