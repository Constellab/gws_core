/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

export class Element{
    constructor(data = {}) {
        this.uuid               = uuidv4();
        this.parent             = null;
        this.data               = data; 
        this.data.id            = data.id || this.uuid;  
        this.data.name          = data.name || "";  
        this.data.description   = data.description || ""; 
        this.data.value         = data.value || null; 
        this.data.style         = this.data.style || {};
        
        this.data.isClickable  = data.isClickable || true;
        this.data.isDraggable   = data.isDraggable || true;

        this._isMouseOver          = false;
    }

    //-- G --
    
    getId(){
        return this.data.id;
    }

    getName(){
        return this.data.name;
    }

    getDescription(){
        return this.data.description;
    }

    getValue(){
        return this.data.value;
    }

    //-- M --

    _mouseClick( e ){
    }

    _mouseOverOn(e){
        this._isMouseOver = true;
    }

    _mouseOverOff(e){
        this._isMouseOver = false;
    }

    isDraggable(){
        return this.data.isDraggable;
    }

    isClickable(){
        return this.data.isClickable;
    }

    //-- N --
}