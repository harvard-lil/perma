var Raphael = require('raphael');
require('./helpers/mapping/usmap.js');

var width=950,
    height=590,
    paperContainer = $('#plot-map-container'),
    paper = new Raphael(paperContainer.attr('id'), width, height),
    map = paper.USMap();


// via http://bertanguven.com/raphael-js-setsize-function
paper.setViewBox(0, 0, width, height);
paper.canvas.setAttribute('preserveAspectRatio', 'none');  // allow resizing svg

// handle resizing
$(window).resize(()=>{
  var newWidth = paperContainer.parent().width();
  paperContainer.find("svg").attr('width', newWidth).attr('height', newWidth/width*height);
}).trigger('resize');

// plot points
for(var point of partnerPoints){
  map.plot(...point);
}

// show bootstrap tooltips? not working ...
/*
require('bootstrap/js/tooltip');
paperContainer.find("svg circle").tooltip({
  'container': 'body',
  'placement': 'bottom',
});
*/
