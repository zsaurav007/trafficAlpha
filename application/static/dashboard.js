/* globals Chart:false, feather:false */
lstMap = []

function create_map(id) {
    return L.map(id, {
        center: [23.7696, 90.3576],
        zoom: 19
    });
}

function add_tile(map) {
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: false,
        subdomains: ['a', 'b', 'c']
    }).addTo(map)
}


function add_marker(map, options) {

    let marker = L.marker([23.7696, 90.3576], {
        draggable: false,
        autoPan: true
    })

    if (options.icon) {
        marker.setIcon(options.icon);
    }

    return marker
}

function add_search(map) {
    const provider = new window.GeoSearch.OpenStreetMapProvider();

    const search = new GeoSearch.GeoSearchControl({
        provider: provider,
        style: 'button',
        showMarker: true,
        showPopup: true,
        marker: new L.marker({draggable: true, autoPan: true}),
        updateMap: true,
        autoClose: false
    });
    map.addControl(search)
}


function execute_call_back(target, latlng, desc) {
    lstMap.every(function (val) {
        if (val.id == target.id) {
            if(!val.noMarkerOption){

                val.marker.addTo(val.map).bindPopup(val.text);
                //val.marker.setIcon(val.icon)
            }
            if(val.marker) {
                val.marker.setLatLng(latlng);
            }
            if (val.fnc) {
                let fnc = val.fnc
                fnc(latlng, desc)
            }
            return false;
        }
        return true
    })
}


function updateMarker(e) {
    execute_call_back(e.sourceTarget._container, e.latlng);
}

function location_update(e) {
    let lab = e.location.label;
    execute_call_back(e.sourceTarget._container, {lat: e.location.x, lng: e.location.y}, lab);
}

function pan_map(map, latlng) {
    map.panTo(latlng);
}

function addMap(map_id, options, fnc) {
    let map = create_map(map_id)
    add_tile(map);
    let marker = null
    let noMarkerOption = true
    if(options.icon) {
        marker = add_marker(map, options);
        noMarkerOption = false
    }
    if (options.isSearchable) {
        add_search(map);
        map.on('geosearch/showlocation', location_update);
    }
    if (options.isAddMarker) {
        map.on('click', updateMarker);
    }
    setTimeout(function () {
        map.invalidateSize(true);
    }, 10);

    lstMap.push({
        map: map,
        id: map_id,
        fnc: fnc,
        marker: marker,
        text: options.text,
        noMarkerOption: noMarkerOption
    })

    return map
}


(function () {
    'use strict'

})()
