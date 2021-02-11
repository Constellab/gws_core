/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import * as G3 from '/static/gview/src/g3/all.js'
import { Color } from "/static/gview/src/utils/color.js";

document.querySelector("#line").addEventListener("click",function(){
    lineMap();
});

document.querySelector("#random-small").addEventListener("click",function(){
    randomMap(2, 10)
})

document.querySelector("#random-large").addEventListener("click",function(){
    randomMap(20, 50)
})

document.querySelector("#miserables").addEventListener("click",function(){
    fileMap("./data/miserables.json");
})

document.querySelector("#block").addEventListener("click",function(){
    fileMap("./data/block.json");
})


function lineMap() {

    var map = new G3.Map({
        canvas: "#graph-3d",
        style: {
            width: "100%",
            height: "100%",
        }
    });

    var box = new G3.Box({
        position: { x: 3, y: 2, z: -1 },
        name: "The red box",
        description: "I'm the red box!",
        style: {
            color: "red",
        }
    })

    var sphere = new G3.Sphere({
        position: { x: 5, y: 5, z: 5 },
        name: "The  blue sphere",
        description: "I'm the blue sphere!",
        style: {
            color: "blue",
        }
    })

    var sphere2 = new G3.Sphere({
        position: { x: -5, y: 0, z: 8 },
        name: "The  green sphere",
        description: "I'm the green sphere!",
        style: {
            color: "green",
        }
    })

    //link
    var line = new G3.Line()
    line.add(box)
    line.add(sphere)
    line.add(sphere2)

    map.add(sphere);
    map.add(sphere2);
    map.add(box);
    map.add(line);

    map.view();
}

function randomMap( nbClusters = 20, nbNodesPerCluster = 50 ) {
    var map = new G3.Map({
        canvas: "#graph-3d",
        style: {
            width: "100%",
            height: "100%",
        }
    });

    for(var j=1; j<=nbClusters; j++){
        var nodeList = [];
        for (var i = 0; i <= nbNodesPerCluster; i++) {
            var sphere = new G3.Sphere({
                position: {
                    x: 20 * (Math.random() - Math.random()),
                    y: 20 * (Math.random() - Math.random()),
                    z: 20 * (Math.random() - Math.random()),
                },
                name: "The  blue sphere",
                description: "I'm a clored sphere!",
                style: {
                    color: Color.randomColor(),
                }
            })
            nodeList.push(sphere);
            map.add(sphere);
        }

        for (var i = 0; i <= 2*nbNodesPerCluster; i++) {
            var source = nodeList[Math.round(Math.random()*nbNodesPerCluster)];
            var target = nodeList[Math.round(Math.random()*nbNodesPerCluster)];
            
            if( source.isLinkedTo(target) ){
                continue;
            }
            var line = new G3.Line({
                nodes: [source, target]
            });
            map.add(line);
        }
    }

    map.view();
}

function fileMap(filePath) {
    var nodeColor;
    if( filePath == "./data/miserables.json"){
        nodeColor = "group";
    } else{
        nodeColor = "user";
    }

    var map = new G3.Map({
        canvas: "#graph-3d",
        style: {
            width: "100%",
            height: "100%",
        },
        nodeColor: "group"
    });

    G3.Map.loadJSONFile(filePath, function(data){
        map.loadJSON(data);
        map.view();
    })
}