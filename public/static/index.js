import * as GBoard from '/static/gws/dashboard/all.js'

var board = new GBoard.Dashboard({canvas: "#gws-dashboard"});
var row = new GBoard.Row();
board.setPanel(row);

var t1 = new GBoard.Tab();
var col = new GBoard.Column();
row.add([t1,col]);

var t2 = new GBoard.Tab();
var t3 = new GBoard.Tab();
col.add([t2, t3]);

board.view();

if(!window.hasOwnProperty("gws"))
    window.gws = {}

window.gws.dashboard = board;