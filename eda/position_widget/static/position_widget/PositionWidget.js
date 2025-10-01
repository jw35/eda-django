// Position_widget.js //

/*jslint browser: true */
/*jshint esversion: 6 */
/*global L, init_position_widget */

function init_position_widget (widget_name, lat1, lng1, lat2, lng2, zoom, static_url) {

    var map = L.map(widget_name + '_map');

    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>',
        maxZoom: 20,
        trackResize: true,
    });
    osm.addTo(map);

    var icon = L.icon({
        iconUrl: static_url + 'position_widget/marker.png',
        iconSize: [36, 36],
        iconAnchor: [18, 36],
    });
    var marker = L.marker((0, 0), { icon: icon, draggable: true, autoPan: true }).addTo(map);

    marker.on('dragstart', function(e) {
        console.log('Drag start');
    });
    marker.on('dragend', function(e) {
        console.log('Drag end');
        var m = e.target;
        var position = m.getLatLng();
        document.getElementById('id_' + widget_name).value = position.lat.toFixed(5) + ',' + position.lng.toFixed(5);
    });

    map.on('click', function(e) {
        console.log('Map click');
        var position = e.latlng;
        marker.setLatLng(position);
        document.getElementById('id_' + widget_name).value = position.lat.toFixed(5) + ',' + position.lng.toFixed(5);
    });

    var initial_value = document.getElementById('id_' + widget_name).value;
    if (initial_value) {
        var values = initial_value.split(',');
        marker.setLatLng(values);
        map.setView(values, zoom);
    }
    else {
        map.fitBounds([[lat1, lng1], [lat2, lng2]]);
    }

}
