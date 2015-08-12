var refreshIntervalId = 0;

var check_status = function() {

    // Check our status service to see if we have archiving jobs pending
    apiRequest("GET", "/archives/" + archive.guid + "/", null, {
        error: null, // cancel out the default error handling provided by apiRequest,
        xhrFields: {
            withCredentials: true
        }

    }).done(function(data) {
        $.each(data.captures, function(i, capture) {
            if ($('#image_cap_container_loading').is(":visible") && capture.role == 'screenshot' && capture.status != 'pending') {
                $('#image_cap_container_loading').hide();
                if (capture.status == 'success')
                    $('#image_cap_container_complete').show();
            }

            if ($('#warc_cap_container_loading').is(":visible") && capture.role == 'primary' && capture.status != 'pending') {
                $('#warc_cap_container_loading').hide();
                if (capture.status != 'failed')
                    $('#warc_cap_container_complete').show();
            }
        });

        // if no status is pending
        if (!$('.container-loading').is(":visible")) {
            clearInterval(refreshIntervalId);
        }
    });
};

$(document).ready(function() {

    if ($('.container-loading').is(":visible")) {
        refreshIntervalId = setInterval(check_status, 2000);
        $('.container-loading').each(function(){
            new Spinner({
                lines: 10, // The number of lines to draw
                length: 4, // The length of each line
                width: 3, // The line thickness
                radius: 3, // The radius of the inner circle
                corners: 1, // Corner roundness (0..1)
                rotate: 0, // The rotation offset
                direction: 1, // 1: clockwise, -1: counterclockwise
                color: '#fff', // #rgb or #rrggbb or array of colors
                speed: 0.7, // Rounds per second
                trail: 60, // Afterglow percentage
                shadow: false, // Whether to render a shadow
                hwaccel: false, // Whether to use hardware acceleration
                className: 'spinner', // The CSS class to assign to the spinner
                zIndex: 2e9, // The z-index (defaults to 2000000000)
                top: 'auto', // Top position relative to parent in px
                left: 'auto' // Left position relative to parent in px
            }).spin(this);
        });
    }

    adjustHeight();
    $('#collapse-refresh').on('shown.bs.collapse', function () {
        adjustHeight();
    });
    $('#collapse-refresh').on('hidden.bs.collapse', function () {
        adjustHeight();
    });
    function adjustHeight() {
        var headerHeight = $('header').height(),
        windowHeight = $(window).height();
        $('iframe').height(windowHeight - headerHeight - 0);
    }

    /* Hide our "needs to be vested" notice if the user clicks the "x" link */
    $(".glyphicon-remove").click(function() {
        $( ".watermark-container" ).fadeOut(250, function() {
        });
    });
});
