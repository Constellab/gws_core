/**
 * LICENSE
 * This software is the exclusive property of Gencovery SAS. 
 * The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
 * About us: https://gencovery.com
 */

import { palette } from '/static-dist/palette-js/palette.js'

export class Color {

    static randomColor() {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++) {
            color += letters[Math.round(Math.random() * (letters.length-1))];
        }
        return color;
    }

}

export class Palette {

    static palette(scheme = Palette.default, size = Palette.size){
        return palette(scheme, size).map(c => "#"+c);
    }

    static color(index = null, scheme = Palette.default, size = Palette.size){
        var tab = palette(scheme, size)
        return "#"+tab[index];
    }

    static randomColor(scheme = Palette.default, size = Palette.size){
        var tab = palette(scheme, size);
        return "#"+tab[Math.round(Math.random() * (size-1))];
    }
}

Palette.MISC              = "mpn65";
Palette.TOL_DIVERGING     = "tol-dv";
Palette.TOL_SEQUENTILA    = "tol-sq";
Palette.TOL_RAINBOW       = "tol-rainbow";
Palette.RAINBOW           = "rainbow";
Palette.default           = Palette.MISC;
Palette.size              = 64;
