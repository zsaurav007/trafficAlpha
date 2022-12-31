/* globals Chart:false, feather:false */
lstMap = []

function create_map(id) {
    return L.map(id, {
        center: [23.7696, 90.3576],
        zoom: 15
    });
}

function add_tile(map) {
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: false,
        subdomains: ['a', 'b', 'c']
    }).addTo(map)
}


function add_marker(map) {
    let marker = L.marker([23.7696, 90.3576], {
        draggable: true,
        autoPan: true
    })

    marker.addTo(map).bindPopup('Map for RTSP');
    return marker
}

function add_search(map) {
    const provider = new window.GeoSearch.OpenStreetMapProvider();

    const search = new GeoSearch.GeoSearchControl({
        provider: provider,
        style: 'button',
        showMarker: true,
        showPopup: true,
        marker: new L.marker({draggable: true}),
        updateMap: true,
        autoClose: false

    });
    map.addControl(search)
}


function execute_call_back(target, latlng, desc) {
    lstMap.every(function (val) {
        if (val.id == target.id && val.fnc) {
            fnc = val.fnc
            fnc(latlng, desc)
            return false
        }
        return true
    })
}


function addMarker(e) {
    marker.setLatLng(e.latlng)
    execute_call_back(e.sourceTarget._container, e.latlng);
}

function location_update(e) {
    marker._popup.setContent(e.location.label)
    execute_call_back(e.sourceTarget._container, {lat:e.location.x, lng: e.location.y}, e.location.label);
}

function addMap(map_id, isSearchable, isAddMarker, fnc) {
    map = create_map(map_id);
    add_tile(map);
    marker = add_marker(map);
    if (isSearchable)
        add_search(map)
    map.on('geosearch/showlocation', location_update);
    if (isAddMarker)
        map.on('click', addMarker);
    setTimeout(function () {
        map.invalidateSize(true);
    }, 10);

    lstMap.push({
        map: map,
        id: map_id,
        fnc: fnc
    })

    return map
}


(function () {
    'use strict'

})()
