/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import * as GBoard from '/static/gws/dashboard/all.js'

GBoard.init();

if(window.gws == undefined)
    window.gws = {};

// implement callback functions
window.gws.explorer = function(){
    console.log("explorer loaded")
}

window.gws.biox = function(){
    console.log("experiments loaded")
}

window.gws.biotadb = function(){
    console.log("databases loaded")
}

window.gws.collab = function(){
    console.log("users loaded")
}

window.gws.code = function(){
    console.log("codes loaded")
}

window.gws.settings = function(){
    console.log("settings loaded")
}