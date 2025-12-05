// Javascript functions for the District Map

/* eslint max-lines-per-function: ["warn", 1000], no-console: "off" */

/*jslint browser: true */
/*jshint esversion: 6 */
/*global $, L, */

'use strict';

L.Control.EdaMap = L.Control.extend({
    onAdd: function(map) {

        const classname = 'leaflet-control-edamap';

        var i;

        var container = L.DomUtil.create('div', `${classname}`);
        L.DomUtil.addClass(container, 'leaflet-control');

        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);

        // Number of bells

        var div = L.DomUtil.create('div', `${classname}-div`, container);
        div.innerHTML = 'Towers with ';

        //    exactly or at least

        var select1 = L.DomUtil.create('select', `${classname}-select`, div);
        select1.id = 'bell_type';
        L.DomUtil.addClass(select1, 'filter_control');
        L.DomEvent.on(select1, 'change', this._onchange, container);

        var opt1 = L.DomUtil.create('option', `${classname}-option`, select1);
        opt1.value = '>';
        opt1.defaultSelected = true;
        opt1.innerHTML = 'at least';

        var opt2 = L.DomUtil.create('option', `${classname}-option`, select1);
        opt2.value = '=';
        opt2.innerHTML = 'exactly';

        div.innerHTML += '  ';

        //    number

        var select2 = L.DomUtil.create('select', `${classname}-select`, div);
        select2.id = 'bell_number';
        L.DomUtil.addClass(select2, 'filter_control');

        var choices = ['3', '4', '5', '6', '8', '10', '12'];
        for (i = 0; i < choices.length; i++) {
            var opt = L.DomUtil.create('option', `${classname}-option`, select2);
            opt.value = choices[i];
            opt.innerHTML = choices[i];
            if (choices[i] === '5') {
                opt.defaultSelected = true;
            }
        }

        div.innerHTML += ' bells';

        // Check boxes

        var checkbox = [
            { id: 'all', label: 'Show other towers', checked: false},
            { id: 'unringable', label: 'Include towers with no ringing', checked: false },
            { id: 'parish', label: 'Show parish boundaries', checked: false },
            { id: 'benifice', label: 'Show benifice boundaries', checked: false },
            { id: 'county', label: 'Show county boundaries', checked: false },
        ];

        for (i = 0; i < checkbox.length; i++) {
            var checkbox_div = L.DomUtil.create('div', `${classname}-div`, container);
            var box = L.DomUtil.create('input', `${classname}-input`, checkbox_div);
            L.DomUtil.addClass(box, 'filter_control');
            box.type = 'checkbox';
            box.id = checkbox[i]['id'];
            // Hide the all checkbox except on a single tower map
            if (checkbox[i]['id'] === 'all' && !map_config.towerid) {
                    checkbox_div.hidden = true
            }

            checkbox_div.innerHTML += checkbox[i]['label'];
        }

        return container;

    },

    onRemove: function(map) {
        // Nothing to do here
    },

    _onchange(container) {
        console.log('On Change');
    }
});

L.control.edaMAp = function(opts) {
    return new L.Control.EdaMap(opts);
};

var map;
var map_config;

var tower_layer = L.featureGroup([], {
    attribution: 'Tower data &copy; <a href="https://elyda.org.uk/">Ely Diocesan Association</a>'
});
var hidden_tower_layer;

function highlight_benifice(feature, layer) {
    layer.on({
        mouseover: function(e) { e.target.setStyle({fillOpacity: 0.6}); },
        mouseout: function(e) { overlays.benifices.layer.resetStyle(); }
    });
    layer.bindPopup(benifice_as_text(feature.properties));
}

function highlight_parish(feature, layer) {
    layer.bindPopup(parish_as_text(feature.properties));
    layer.on({
        mouseover: function(e) {
            /* Highlight the parish itself  */
            e.target.setStyle({fillOpacity: 0.1});
            /* Find the corresponding Benefice and highlight that too */
            overlays.benifices.layer.eachLayer(function (benifice) {
                if (benifice.feature.properties.Benefice_Code === feature.properties.Benefice_Code) {
                    benifice.setStyle({fillOpacity: 0.6});
                }
            });
        },
        mouseout: function(e) { overlays.parishes.layer.resetStyle(); overlays.benifices.layer.resetStyle(); }
    });

}

var parishes_fg = L.featureGroup();
var association_fg = L.featureGroup();

const overlays = {
    parishes:
    {
        name: 'Parishes',
        show: false,
        file: 'Parishes.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'parish_boundary',
                attribution: 'Boundary data &copy; <a href="https://www.churchofengland.org/about/data-services">Church of England Data Services</a>',
                style:
                {
                    color: '#000000',
                    opacity: 1,
                    weight: 1,
                    fill: true,
                    fillOpacity: 0
                },
                onEachFeature: highlight_parish
            }
        ),
        add_to: parishes_fg
    },
    deaneries:
    {
        name: 'Deaneries',
        show: false,
        file: 'Deaneries.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'parish_boundary',
                attribution: 'Boundary data &copy; <a href="https://www.churchofengland.org/about/data-services">Church of England Data Services</a>',
                style:
                {
                    color: '#000000',
                    opacity: 1,
                    weight: 3,
                    fill: false
                }
            }
        ),
        add_to: parishes_fg

    },
    benifices:
    {
        name: 'Benifices',
        show: false,
        file: 'Benifices.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'benifice_boundary',
                attribution: 'Boundary data &copy; <a href="https://www.churchofengland.org/about/data-services">Church of England Data Services</a>',
                style:
                {
                    color: '#1ab2ff',
                    fillCcolor: '#1ab2ff',
                    opacity: 1,
                    weight: 5,
                    fill: true,
                    fillOpacity: 0
                },
                onEachFeature: highlight_benifice,
            }
        )
    },
    counties:
    {
        name: 'Counties',
        show: false,
        file: 'BoundaryCeremonial.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'county_boundary',
                attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a></a>',
                style:
                {
                    color: ' #0033cc',
                    opacity: 1,
                    weight: 6,
                    fill: false
                }
            }
        )
    },
    association:
    {
        name: 'Association',
        show: true,
        file: 'Association.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'association_boundary',
                attribution: 'Boundary data &copy; <a href="https://www.churchofengland.org/about/data-services">Church of England Data Services</a>',
                style:
                {
                    color: '#ff0000',
                    opacity: 1,
                    weight: 3,
                    fill: false
                }
            }
        ),
        add_to: association_fg,
    },
    districts:
    {
        name: 'Districts',
        show: true,
        file: 'Districts.geojson',
        layer: L.geoJSON(null,
            {
                pane: 'association_boundary',
                attribution: 'Boundary data &copy; <a href="https://www.churchofengland.org/about/data-services">Church of England Data Services</a>',
                style:
                {
                    color: '#ff0000',
                    opacity: 1,
                    weight: 2,
                    fill: false
                }
            }
        ),
        add_to: association_fg
    },
};

function make_icon(district, bells, status, selected) {

    var prefix = district.charAt(0).toUpperCase();
    var suffix = 'p';
    if (status === 'O') {
        suffix = 'n';
    }
    else if (status === 'N') {
        suffix = 'u';
    }

    var url = `${map_config.static_root}/Markers/${prefix}${bells}${suffix}.png`;
    /* var shadow_url = 'https://cambridgeringing.info/images/shadow.png'; */

    var size = 36;
    if (selected) {
        size = 54;
    }

    return L.icon({
        iconUrl: url,
        iconSize: [size, size],
        iconAnchor: [size/2, size],
        /*shadowUrl: shadow_url,
        shadowSize: [53, 29],
        shadowAnchor: [12, 25],*/
        popupAnchor: [0, -size],
        tooltipAnchor: [8, -27]
    });


}

function toggle_display(layer) {

    var tower = layer.feature.properties;
    var show = 1;

    if (this.limit_type === '=' && tower.bells !== parseInt(this.limit_number)) {
        show = 0;
    }
    else if (this.limit_type === '>' && tower.bells < parseInt(this.limit_number)) {
        show = 0;
    }

    if (!this.unringable && tower.ringing_status === 'N') {
        show = 0;
    }

    // Given a selected tower, always show it but show nothing else
    // unless 'all' is set
    if (map_config.towerid) {
        if (!this.all) {
            show = 0;
        }
        if (map_config.towerid === layer.feature.id) {
            show = 1;
        }
    }

    if (show) {
        layer.addTo(tower_layer);
    }
    else {
        layer.removeFrom(tower_layer);
    }

}

function bring_to_top(towerid) {

    // Bring the layer with id=towerid to the top

    if (towerid) {
        tower_layer.eachLayer(function (layer) {
            if (layer.feature.id === towerid) {
                layer.setZIndexOffset(1000)
            }
        });
    }

}


function filter_towers() {

    var context = {
        limit_type: document.getElementById('bell_type').value,
        limit_number: document.getElementById('bell_number').value,
        all: document.getElementById('all').checked,
        unringable: document.getElementById('unringable').checked,
    };

    hidden_tower_layer.eachLayer(toggle_display, context);
    bring_to_top(map_config.towerid);

    if (document.getElementById('parish').checked) {
        parishes_fg.addTo(map);
    } else {
        parishes_fg.removeFrom(map);
    }

    if (document.getElementById('benifice').checked) {
        overlays.benifices.layer.addTo(map);
    } else {
        overlays.benifices.layer.removeFrom(map);
    }

    if (document.getElementById('county').checked) {
        overlays.counties.layer.addTo(map);
    } else {
        overlays.counties.layer.removeFrom(map);
    }

}


function tower_as_text(feature) {

    var result = '';
    var tower = feature.properties

    result += `<h1>${tower.place} - ${tower.dedication}</h1>`;


    result += '<table>';

    result += '<tr><th align="right" valign="top">Bells:</th><td valign="top">';
    if (tower.bells) {
        result += `${tower.bells}`;
    }
    if (tower.weight) {
        result += `, ${tower.weight}`;
    }
    if (tower.note) {
        result += ` in ${tower.note}`;
    }
    if (tower.ringing_status == 'N') {
        result += ' (No ringing)';
    }
    result += '</td></tr>';

    if (tower.service) {
        result += `<tr><th align="right" valign="top">Service:</th><td valign="top">${tower['service']}</td></tr>`;
    }

    if (tower.practice) {
        result += `<tr><th align="right" valign="top">Practice:</th><td valign="top">${tower['practice']}</td></tr>`;
    }

    if (tower.postcode) {
        result += `<tr><th align="right" valign="top">Postcode:</th><td valign="top">${tower['postcode']}</td></tr>`;
    }

    if (tower['os_grid']) {
        result += `<tr><th align="right" valign="top">Grid:</th><td valign="top">${tower['os_grid']}</td></tr>`;
    }

    if (feature.geometry.coordinates) {
        result += `<tr><th align="right" valign="top">Lat, Lng:</th><td valign="top">${feature.geometry.coordinates[1]}, ${feature.geometry.coordinates[0]}</td></tr>`;
    }

    if (tower.primary_contact) {
        var contact = tower.primary_contact;

        if (contact.title || contact.forename || contact.name) {
            result += `<tr><th align="right" valign="top">Secretary:</th><td valign="top">${[contact.title, contact.forename, contact.name].join(' ')}`;
            if (contact.role === 'BL') {
                result += ' (Bells Only)';
            }
            if (contact.role === 'BA') {
                result += ' (Band Only)';
            }
            result += '</td></tr>';
        }

        if (contact.email) {
            result += `<tr><th align="right" valign="top">Email:</th><td valign="top"><a href="mailto:${contact.email}">${contact.email}</a></td></tr>`;
        }

        if (contact.phone1 || contact.phone2) {
            result += `<tr><th align="right" valign="top">Telephone:</th><td valign="top">${[contact.phone1, contact.phone2].filter((word) => word).join(' / ')}</td></tr>`;
        }

    }

    var rpt;
    if (tower.report) {
        rpt = 'Yes';
    }
    else {
        rpt = 'No';
    }
    result += `<tr><th align="right" valign="top">Annual Report:</th><td valign="top">${rpt}</td></tr>`;

    result += '<table>';

    if (tower.notes) {
        result += `<p>${tower['notes']}</p>`;
    }

    if (tower.websites) {
        result += '<p>'
        for (var i = 0; i < tower.websites.length; i++) {
            var website = tower.websites[i];
            var link_text = website.link_text || 'Website';
            result += `<a href="${website.url}">${link_text}</a> `;
        }
        result += '</p>'
    }

    return result;

}

function parish_as_text(parish) {

    var result = '';

    result += `<h1>${parish.Legal_Name}</h1>`;

    result += '<table>';

    if (parish.Benefice_Name) {
        result += `<tr><th align="right" valign="top">Benifice:</th><td valign="top">${parish['Benefice_Name']}</td></tr>`;
    }

    if (parish.Deanery_Name) {
        result += `<tr><th align="right" valign="top">Deanary:</th><td valign="top">${parish['Deanery_Name']}</td></tr>`;
    }

    if (parish.Archdeaconry_Name) {
        result += `<tr><th align="right" valign="top">Archdeaconry:</th><td valign="top">${parish['Archdeaconry_Name']}</td></tr>`;
    }

    result += '<table>';

    return result;

}

function benifice_as_text(benifice) {

    var result = '';

    result += `<p>${benifice.Benefice_Name}</p>`;

    return result;

}

function set_bounds(name, overlay) {

    // Set the map to display just the district if displaying a district
    // and the entire association otherwise

    if (map_config.towerid) {
        return;
    }

    if (map_config.district) {
        if (name == 'districts') {
            overlay.layer.eachLayer(function (layer) {
                if (layer.feature.properties.District === map_config.district) {
                    map.fitBounds(layer.getBounds());
                }
            });
        }
    }
    else if (name === 'association') {
        map.fitBounds(overlay.layer.getBounds(), {paddingTopLeft: [-20, -20], paddingBottomRight: [-20, -20]});
    }

}

function load_boundary_data() {

    for (let [name, overlay] of Object.entries(overlays)) {

        var url = `${map_config.static_root}/${overlay.file}`

        $.ajax({url: url, dataType: 'json'}
        ).done(
            function (data) {
                overlay.layer.addData(data);
                if (overlay.add_to) {
                    overlay.layer.addTo(overlay.add_to);
                }
                set_bounds(name, overlay);
            }
        ).fail(
            function (ignore, ignore1, error_thrown) {
                alert('Loading boudary data failed - see Javascript console for details');
            }
        );

    }

}

function load_tower_data(map) {

    /*
    Load the towers into a GeoJSON layer that we don't actually add to the map.
    Instead, filter_towers() adds or removes layers from the hidden layer
    to and from a layer that is added to them.

    This mess is all because you can't just show/hide a layer in a GoJSON layer.
    */

    function setup_tower_listeners() {
        var filter_fields = document.getElementsByClassName('filter_control');
        for (var i = 0; i < filter_fields.length; i++) {
            filter_fields[i].addEventListener('change', filter_towers);
        }
    }

    function create_marker(feature, latlng) {
        var selected = map_config.towerid && (feature.id === map_config.towerid);
        var icon = make_icon(feature.properties.district, feature.properties.bells, feature.properties.ringing_status, selected);
        return L.marker(latlng, { icon: icon });
    }


    function add_popup(feature, layer) {
        var name = feature.properties.place;
        if (feature.properties['Include dedication'] === 'Yes') {
            name = `${feature.properties.place} - ${feature.properties.dedication}`;
        }
        layer.bindPopup(tower_as_text(feature))
            .bindTooltip(`<b>${name}</b><br>(click for more)`);
        if (map_config.towerid && map_config.towerid === feature.id) {
            map.setView([feature.geometry.coordinates[1], feature.geometry.coordinates[0]], 12);
        }
    }

    var url = map_config.towers_json;

    $.ajax({url: url, dataType: 'json'}
    ).done(
        function (data) {
            hidden_tower_layer = L.geoJSON(
                data,
                {   pane: 'towers',
                    pointToLayer: create_marker,
                    onEachFeature: add_popup
                }
            );
            filter_towers();
            setup_tower_listeners();
        }
    ).fail(
        function (ignore, ignore1, error_thrown) {
            alert('Loading tower data failed - see Javascript console for details');
        }
    );

}

function setup_panes(map) {

    var panes =
    [
        { name: 'benifice_boundary', zIndex: 420 },
        { name: 'parish_boundary', zIndex: 430 },
        { name: 'county_boundary', zIndex: 440 },
        { name: 'association_boundary', zIndex: 450 },
        { name: 'towers', zIndex: 625 }
    ];

    for (var i = 0; i < panes.length; i++) {
        const pane = panes[i];
        map.createPane(pane.name).style.zIndex = pane.zIndex;
    }

}

$(document).ready(function () {

    map_config = JSON.parse(
        document.getElementById('map_config').textContent
    );

    map = L.map('map', {minZoom: 8, zoomSnap: 0.25, zoomDelta: 0.5});

    setup_panes(map);

    L.control.edaMAp({ position: 'topright' }).addTo(map);

    association_fg.addTo(map);

    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a></a>',
        maxZoom: 20,
        trackResize: true,
    });
    osm.addTo(map);

    tower_layer.addTo(map);
    load_tower_data(map);
    load_boundary_data();

});

