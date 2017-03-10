let Datamap = require('datamaps');

// show world map
let partnerMap = new Datamap({
  element: document.getElementById("plot-map-container"),
  geographyConfig: {
    popupOnHover: false,
    highlightOnHover: false
  },
  fills: {
    defaultFill: '#74bbfa',
    partner: '#DD671A',
  },
  responsive: true
});

// add partner circles
partnerMap.bubbles(partnerPoints.map((partner)=>({
    name: partner[2],
    radius: 5,
    latitude: partner[0],
    longitude: partner[1],
    fillKey: 'partner',
  })), {
  popupTemplate: function(geo, data) {
    return '<div class="hoverinfo">' + data.name + '</div>';
  },
  borderWidth: 1,
  fillOpacity: 1
});

// resize map on window change
$(window).on('resize', function() {
  partnerMap.resize();
});