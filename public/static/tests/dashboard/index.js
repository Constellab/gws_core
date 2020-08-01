/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import * as GWS from '/static/gws/dashboard/all.js'

// Dashboard

function loadJsFile(filename){
    var fileref=document.createElement('script')
    fileref.setAttribute("type","text/javascript")
    fileref.setAttribute("src", filename)
    if (typeof fileref!="undefined")
        document.getElementsByTagName("head")[0].appendChild(fileref)
}

function loadCssFile(filename){
    var fileref=document.createElement("link")
    fileref.setAttribute("rel", "stylesheet")
    fileref.setAttribute("type", "text/css")
    fileref.setAttribute("href", filename)
    if (typeof fileref!="undefined")
        document.getElementsByTagName("head")[0].appendChild(fileref)
}

var board = new GWS.Dashboard({canvas: "#dashboard"});
var row = new GWS.Row();
board.setPanel(row);

var t1 = new GWS.Tab();
var col = new GWS.Column();
row.add([t1,col]);

var t2 = new GWS.Tab();
var t3 = new GWS.Tab();
col.add([t2, t3]);

board.view();

t3.setHTMLContent("Yeah!")

