/****************************************************
* Create page stuff start
****************************************************/

var refreshIntervalId = 0;

var check_status = function() {

// Check our status service to see if we have archiving jobs pending
    var request = $.ajax({
        url: status_url,
        type: "GET",
        dataType: "jsonp"
    });

    request.done(function(data) {

        if ($('#image_cap_container_loading').is(":visible") && data.image_capture != 'pending') {
            $('#image_cap_container_loading').hide();
            $('#image_cap_container_complete').show();

            // A kludge to reload iframe
            $('iframe').attr('src', $('iframe').attr('src'));
        }

        if ($('#warc_cap_container_loading').is(":visible") && data.source_capture != 'pending') {
            $('#warc_cap_container_loading').hide();
            $('#warc_cap_container_complete').show();

            // A kludge to reload iframe
            $('iframe').attr('src', $('iframe').attr('src'));
        }

        if ($('#pdf_cap_container_loading').is(":visible") && data.pdf_capture != 'pending') {
            $('#pdf_cap_container_loading').hide();
            $('#pdf_cap_container_complete').show();

            // A kludge to reload iframe
            $('iframe').attr('src', $('iframe').attr('src'));
        }

        // if no status is pending
        if (data.image_capture != 'pending' && data.source_capture != 'pending' && data.pdf_capture != 'pending' && data.text_capture != 'pending') {
            clearInterval(refreshIntervalId);
        }
    });
}

/* We have to do some funky height measurement stuff with our
collapsable header since we "height: auto;" isn't an option
when we expand our collapsed header */

var original_header_height = 0;

var collapsed = false;

function collapse_header() {
    /* A helper that rolls our header up */

    if (!collapsed) {

        collapsed = true;

        $('.overlay').hide();
        $('#full-header').fadeOut(100);
        $('#compact-header').fadeIn(100);

        $('.navbar').animate({height: '35px'},{
            duration: 200,
            complete: function() {
                adjustHeight();
            }
        });
    }
}

function expand_header() {
    /* A helper that rolls down header up */

    $('#compact-header').fadeOut(100);
    $('#full-header').fadeIn(100);
    $('.overlay').show();

    $('.navbar').animate({height: original_header_height}, {
        duration: 200,
        complete: function() {
            adjustHeight();
            collapsed = false;
        }
    });
}

function adjustHeight() {
    var headerHeight = $('header').height(),
    windowHeight = $(window).height();
    $('iframe').height(windowHeight - headerHeight - 0);
}

$(document).ready(function() {

    if ($('#image_cap_container_loading').is(":visible") ||
        $('#warc_cap_container_loading').is(":visible") ||
        $('#pdf_cap_container_loading').is(":visible")) {
        refreshIntervalId = setInterval(check_status, 2000);
    }


    adjustHeight();
    $('#collapse-refresh').on('shown.bs.collapse', function () {
        adjustHeight();
    });
    $('#collapse-refresh').on('hidden.bs.collapse', function () {
        adjustHeight();
    });


    /* Control the expand/collapse of the header  - start*/

    // We need to redraw the header to the same height
    // if the header is expanded

    original_header_height = $('#full-header').height();


    // We need to set an overlay on top of our iframe
    var iframe_height = $(window).height() - original_header_height;

    $('.overlay').css({'height': iframe_height,
        'top': iframe_height,
         'margin-top': 0 - iframe_height});


    $('header #compact-header .expand-button').click(function() {
        expand_header();
    });

    $('.navbar').on('DOMMouseScroll mousewheel', function () {
        collapse_header();
    });

    $('.overlay').on('DOMMouseScroll mousewheel click', function () {
        collapse_header();
    });

    /* Control the expand/collapse of the header  - end */


});

/****************************************************
* Create page stuff end
****************************************************/