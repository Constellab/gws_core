
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

export function forceLayout( map ){
    if(map._layoutNodes.length == 0){
        for(let i in map.nodes){
            map._layoutNodes.push({
                id: map.nodes[i].data.id,
                x: map.nodes[i].data.position.x,
                y: map.nodes[i].data.position.y,
                z: map.nodes[i].data.position.z
            });
        }
    }

    if(map._layoutLinks.length == 0){
        for(let i in map.lines){
            let lineNodes = map.lines[i]._nodes;
            for(var j=0; j<lineNodes.length-1; j++){
                map._layoutLinks.push({
                    source: lineNodes[j].data.id,
                    target: lineNodes[j+1].data.id
                });
            }
        }
    }

    let ndim = 3;
    map._layoutSimulation = d3.forceSimulation(map._layoutNodes, ndim)
            .force("charge", 
                d3.forceManyBody().strength(ndim == 3 ? -30 : -30)
            )
            .force("link", 
                d3.forceLink(map._layoutLinks).id(function(d) {
                    return d.id
                })
            )
            .force("center", d3.forceCenter())
            .velocityDecay(0.2)
            .on("tick", updateLayout);

    setTimeout(function(){map._layoutSimulation.alphaDecay(0.75)},5000)

    function updateLayout(){
        map._layoutNodes.forEach(node =>{
            let id = node.id;
            map.nodes[id].data.position.x = node.x;
            map.nodes[id].data.position.y = node.y;
            map.nodes[id].data.position.z = node.z;
            map.nodes[id].updatePosition();
            //map._camera.updateMatrixWorld();
        })
    }
}
