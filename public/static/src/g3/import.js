/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import * as G3 from '/static/gws/src/g3/all.js'
import { Color } from "/static/gws/src/utils/color.js";


window.loadG3Data = function( canvas, data ){
    //var canvas = document.getElementsByClassName("gview:cell-g3")[0]
    //canvas.innerHTML = "<div id='map-canvas'></div>"
    canvas.style.width = "100%"
    canvas.style.height = "600px"
    canvas.style.display = "block"
    
    var map = new G3.Map({
        canvas: canvas,
        style: {}
    });
        
    //console.log(data)

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