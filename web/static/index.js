
/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */


window.addEventListener("load", function(){

    document.querySelectorAll(".gws-big-number").forEach( elm => {
        elm.innerHTML = elm.innerHTML.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    })

});