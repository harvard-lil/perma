/* Our globals. Look out interwebs - start */

// Where we store our successfully created new archive data
var new_archive = {};

// Where we queue up our archive guids for polling
var refreshIntervalIds = [];

/* Our globals. Look out interwebs - end */



/* Everything that needs to happen at page load - start */

$(function() {

    $('#archive-upload-confirm').modal({show: false});
    $('#archive-upload').modal({show: false});

    // When a new url is entered into our form
    $('#linker').submit(function() {
        var $this = $(this);
        $.ajax($this.attr('action'), {
            method: $this.attr('method'),
            contentType: 'application/json',
            data: JSON.stringify({
                url: $this.find("input[name=url]").val()
            }),
            success: linkIt,
            error: linkNot
        });

        return false;
    });

    // When a user uploads their own capture
    $('#archive_upload_form').submit(function() {
        $(this).ajaxSubmit({
            success: uploadIt,
            error: uploadNot
        });

        return false;
    });

    // Toggle users dropdown
    $('#dashboard-users').click(function(){
        $('.users-secondary').toggle();
    });
});

/* Everything that needs to happen at page load - end */



/* Handle the the main action (enter url, hit the button) button - start */

function linkIt(data){
    new_archive.url = mirror_server_host  + '/' + data.guid;
    new_archive.guid = data.guid;
    new_archive.title = data.title;
    new_archive.static_prefix = settings.STATIC_URL;

    $('#preview-container').html(templates.success(new_archive));

    // Get our spinner going now that we're drawing it
    var target = document.getElementById('spinner');
    var spinner = new Spinner(opts).spin(target);

    $('#steps-container').html('');
    $('.preview-row').removeClass('hide').hide().slideDown();

    refreshIntervalIds.push(setInterval(check_status, 2000));
}

function linkNot(jqXHR){
    $('#preview-container').html(templates.preview_failure({static_prefix:settings.STATIC_URL}));

    var message = "";
    if (jqXHR.status == 400 && jqXHR.responseText){
        var errors = JSON.parse(jqXHR.responseText).archives;
        for (var prop in errors) {
            message += errors[prop] + " ";
        }
    }

    $('#steps-container').html(templates.error({
        message: message || "Error " + jqXHR.status
    }));

    $('.preview-row').removeClass('hide').hide().slideDown();
}

/* Handle the the main action (enter url, hit the button) button - start */




/* Handle an upload - start */

function uploadNot(data) {
    // Display an error message in our upload modal
    var response = jQuery.parseJSON( data.responseText );
    //$('#upload-error').text('The upload failed. Only gif, jpg, and pdf files supported. Max of 50 MB.');
    $('#upload-error').text('The upload failed. ' + response.reason);
}

function uploadIt(data) {
    // If a user wants to upload their own screen capture, we display
    // a modal and the form in that modal is handled here

    $('#archive-upload').modal('hide');

    var upload_image_url = settings.STATIC_URL + '/img/upload-preview.jpg';
    new_archive.url = mirror_server_host  + '/' + data.guid;

    $('#preview-container').html(templates.preview_available_no_upload_option({image_url: upload_image_url, archive_url: new_archive.url}));

    // Get our spinner going now that we're drawing it
    var target = document.getElementById('spinner');
    var spinner = new Spinner(opts).spin(target);

    $('#steps-container').html(templates.success_steps({url: new_archive.url,
                                                        userguide_url: userguide_url, vesting_privs: vesting_privs})).removeClass('hide').hide().slideDown();
}

function upload_form() {
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#archive-upload').modal('show');
    return false;
}

/* Handle an upload - end */




/* Handle the thumbnail fetching - start */

function get_thumbnail() {
    $.ajax({
        url: main_server_host + thumbnail_service_url + new_archive.guid,
        cache: false
    })
    .done(function(data) {
        $('#preview-container').html(templates.preview_available({
            image_url: settings.DIRECT_MEDIA_URL + data.thumbnail,
            archive_url: new_archive.url
        })).removeClass('hide').hide().slideDown();
    });
}

/* Handle the thumbnail fetching - end */




/* Our polling function for the thumbnail completion - start */

// The plan is to set a timer to periodically check if the thumbnail
// exists. Once it does, we append it to the page and clear the
// thumbnail. The reason we're keeping a list of interval IDs rather
// than just one is as a hacky solution to the problem of a user
// creating a Perma link for some URL and then immediately clicking
// the button again for the same URL. Since all these requests are
// done with AJAX, that results in two different interval IDs getting
// created. Both requests will end up completing but the old interval
// ID will be overwritten and never cleared, causing a bunch of copies
// of the screenshot to get appended to the page. We thus just append
// them to the list and then clear the whole list once the request
// succeeds.

function check_status() {

    // Check our status service to see if we have archiving jobs pending
    var request = apiRequest("GET", "/archives/" + new_archive.guid + "/", {'cache': false});

    request.done(function(data) {
        var asset = data.assets[0];

        if (asset.image_capture !== 'pending') {
            // Clear out our pending jobs
            $.each(refreshIntervalIds, function(ndx, id) {
                clearInterval(id);
            });

            // If we don't have an image capture for a preview ...
            if(asset.image_capture == 'failed'){

                // ... but another capture succeeded, show the success template with no image_url.
                if((asset.pdf_capture && asset.pdf_capture != 'failed') || (asset.warc_capture && asset.warc_capture != 'failed')) {
                    $('#preview-container').html(templates.preview_available({
                        image_url: null,
                        archive_url: new_archive.url
                    })).removeClass('hide').hide().slideDown();

                // ... and the other captures also failed, show an error message/upload form.
                }else{
                    $('#preview-container').html(templates.preview_failure({static_prefix:settings.STATIC_URL}));
                    $('#steps-container').html(templates.error({
                        message: "Error: URL capture failed."
                    }));
                    $('.preview-row').removeClass('hide').hide().slideDown();
                }

            }else {
                // Show success message and thumbnail.
                get_thumbnail();
                $('#steps-container').html(templates.success_steps({
                    url: new_archive.url,
                    userguide_url: userguide_url,
                    vesting_privs: vesting_privs
                })).removeClass('hide').hide().slideDown();
            }

        }
    });
}

/* Our polling function for the thumbnail completion - end */



/* Our spinner controller - start */

var opts = {
    lines: 9, // The number of lines to draw
    length: 9, // The length of each line
    width: 5, // The line thickness
    radius: 10, // The radius of the inner circle
    corners: 1, // Corner roundness (0..1)
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    color: '#ff4100', // #rgb or #rrggbb or array of colors
    speed: 1, // Rounds per second
    trail: 60, // Afterglow percentage
    shadow: false, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    className: 'spinner', // The CSS class to assign to the spinner
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    top: 'auto', // Top position relative to parent in px
    left: 'auto' // Left position relative to parent in px
};

/* Our spinner controller - end */
