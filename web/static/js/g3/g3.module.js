/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import * as G3 from './_g3/all.js'
import { Color } from "../_utils/color.js";

window.g3 = {}
window.g3.render = function( canvas, data, width ){
    if(width == null){
        var w = window.innerWidth;
        width = Math.min(w,450)
    }
    var aspect = 4/3;
    canvas.style.width = width + "px"
    canvas.style.height = (width / aspect) + "px"
    canvas.style.display = "block"
    
    var map = new G3.Map({
        canvas: canvas,
        style: {}
    });
    
    var metNodes = {}
    for(var i in data.metabolites){
        var met = data.metabolites[i]
        var node = new G3.Sphere({
            name: met.name,
            description: "",
            position: {z: 0},
            style: {
                color: "green",
            }
        })
        metNodes[met.id] = node
        map.add(node)
    }
    
    for(var i in data.reactions){

        var reac = data.reactions[i]
        var reactionNode = new G3.Box({
            name: reac.name,
            description: "",
            position: {z: 0},
            style: {
                color: "red",
            }
        })

        map.add(reactionNode)

        for(var name in reac.metabolites){
            var stoich = reac.metabolites[name]
            var isProduct = (stoich > 0)
            var line = new G3.Line()
            map.add(line)

            if(isProduct){
                line.add(reactionNode)
                line.add(metNodes[name])
            }else{
                line.add(metNodes[name])
                line.add(reactionNode)
            }
        }
    }

    map.view()

}