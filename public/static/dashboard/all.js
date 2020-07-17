

/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

export { Dashboard } from './dashboard.js';
export { Stack } from "./panel.js";
export { Row } from "./panel.js";
export { Column } from "./panel.js";
export { Tab } from "./panel.js";

import { Dashboard } from './dashboard.js';
import { Row } from "./panel.js";
import { Column } from "./panel.js";
import { Tab } from "./panel.js";

export function init( canvas_id = "#gws-dashboard" ){

    window.addEventListener("load", function(){
        var board = new Dashboard({canvas: canvas_id});
        var row = new Row();
        board.setPanel(row);

        var t1 = new Tab({
            name: "explorer",
            title: "Explorer"
        });
        var col = new Column({name: "main"});
        row.add([t1,col]);

        var t2 = new Tab({
            name: "viewer",
            title: "Viewer"
        });
        var t3 = new Tab({
            name: "viewer",
            title: "Viewer"
        });
        col.add([t2, t3]);

        board.view();

        

        if(!window.hasOwnProperty("gws"))
            window.gws = {}

        window.gws.dashboard = board;
    });

}