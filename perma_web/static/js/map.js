$(function(){
    /*** map drawing stuff ***/

    var paper = new ScaleRaphael('plot-map-container', 950, 590),
        map = paper.USMap();

    // handle resizing
    function resizePaper(){
        var newWidth = $("#plot-map-container").parent().width();
        paper.scaleAll(newWidth/map.width);
    }
    $(window).resize(resizePaper);
    resizePaper();

    // plot points
    for(var i = 0; i < partnerPoints.length; i++){
        //map.plot(partnerPoints[i][0], partnerPoints[i][1], partnerPoints[i][2]);
        map.plot(partnerPoints[i][0], partnerPoints[i][1]);
    }

});
