// Position_widget.js //

/*jslint browser: true */
/*jshint esversion: 6 */
/*global L, init_position_widget */

function init_position_widget (div_id, value, lat1, lng1, lat2, lng2, zoom) {

    var map = L.map(div_id);

    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a></a>',
        maxZoom: 20,
        trackResize: true,
    });
    osm.addTo(map);

    map.fitBounds([[lat1, lng1], [lat2, lng2]]);

}
