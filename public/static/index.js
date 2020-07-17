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

window.gws.code = function(){
    console.log("codes loaded")
}

window.gws.settings = function(){
    console.log("settings loaded")
}