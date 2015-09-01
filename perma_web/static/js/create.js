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
    new_archive.url = 'http://' + settings.HOST  + '/' + data.guid;
    new_archive.guid = data.guid;
    new_archive.title = data.title;
    new_archive.static_prefix = settings.STATIC_URL;

    $('#preview-container').html(templates.success(new_archive));

    // Get our spinner going now that we're drawing it
    var target = document.getElementById('spinner');
    var spinner = new Spinner(opts).spin(target);

    $('#steps-container').html('');
    $('.preview-row').removeClass('hide');

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

    $('.preview-row').removeClass('hide');
}

/* Handle the the main action (enter url, hit the button) button - start */




/* Handle an upload - start */

function uploadNot(data) {
    // Display an error message in our upload modal
    var response = jQuery.parseJSON( data.responseText),
        reasons = [];
    $('.js-warning').remove();
    $('.has-error').removeClass('has-error');
    if(response.archives){
        // If error message comes in as {archive:{file:"message",url:"message"}},
        // show appropriate error message next to each field.
        for(var key in response.archives) {
            if(response.archives.hasOwnProperty(key)) {
                var input = $('#'+key);
                if(input.length){
                    input.after('<span class="help-block js-warning">'+response.archives[key]+'</span>');
                    input.closest('div').addClass('has-error');
                }else{
                    reasons.push(response.archives[key]);
                }
            }
        }
    }else if(response.reason){
        reasons.push(response.reason);
    }else{
        reasons.push(response);
    }

    $('#upload-error').text('Upload failed. ' + reasons.join(". "));
}

function uploadIt(data) {
    // If a user wants to upload their own screen capture, we display
    // a modal and the form in that modal is handled here

    $('#archive-upload').modal('hide');

    var upload_image_url = settings.STATIC_URL + '/img/upload-preview.jpg';
    new_archive.url = 'http://' + settings.HOST  + '/' + data.guid;

    $('#preview-container').html(templates.preview_available_no_upload_option({image_url: upload_image_url, archive_url: new_archive.url}));

    // Get our spinner going now that we're drawing it
    var target = document.getElementById('spinner');
    var spinner = new Spinner(opts).spin(target);

    $('#steps-container').html(templates.success_steps({url: new_archive.url,
                                                        userguide_url: userguide_url, vesting_privs: vesting_privs})).removeClass('hide');
}

function upload_form() {
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#archive_upload_form input[name="url"]').val($('#rawUrl').val());
    $('#archive-upload').modal('show');
    return false;
}

/* Handle an upload - end */




/* Handle the thumbnail fetching - start */

function get_thumbnail() {
    $('#preview-container').html(templates.preview_available({
        image_url: thumbnail_service_url.replace('GUID', new_archive.guid),
        archive_url: new_archive.url
    })).removeClass('hide');
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
        var capturesPending = false,
            capturesSucceeded = false;
        $.each(data.captures, function(i, capture){
            if(capture.role != 'favicon') {
                if (capture.status == 'pending') capturesPending = true;
                if (capture.status == 'success') capturesSucceeded = true;
            }
        });

        // We're done checking status when nothing is pending.
        if(capturesSucceeded || !capturesPending){

            // Clear out our pending jobs
            $.each(refreshIntervalIds, function(ndx, id) {
                clearInterval(id);
            });

            // If we have at least one success, show success message.
            if(capturesSucceeded){
                $('#steps-container').html(templates.success_steps({
                    url: new_archive.url,
                    userguide_url: userguide_url,
                    vesting_privs: vesting_privs
                })).removeClass('hide');

                $('#preview-container').html(templates.preview_available({
                    image_url: thumbnail_service_url.replace('GUID', new_archive.guid),
                    archive_url: new_archive.url
                })).removeClass('hide');

                // Catch failure to load thumbnail, and show thumbnail-not-available message
                $('.library-thumbnail img').on('error', function() {
                    $('#preview-container').html(templates.preview_available({
                        image_url: null,
                        archive_url: new_archive.url
                    }));
                });

            // Else show failure message/upload form.
            }else {
                $('#preview-container').html(templates.preview_failure({static_prefix: settings.STATIC_URL}));
                $('#steps-container').html(templates.error({
                    message: "Error: URL capture failed."
                }));
                $('.preview-row').removeClass('hide');
            }
        }
    });
}

/* Our polling function for the thumbnail completion - end */



/* Our spinner controller - start */

var opts = {
    lines: 17, // The number of lines to draw
    length: 2, // The length of each line
    width: 1.5, // The line thickness
    radius: 10, // The radius of the inner circle
    scale: 1.7, // Scales overall size of the spinner
    corners: 0, // Corner roundness (0..1)
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    color: '#2D76EE', // #rgb or #rrggbb or array of colors
    opacity: 0.25, // Opacity of the lines
    speed: 0.7, // Rounds per second
    trail: 100, // Afterglow percentage
    shadow: false, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    className: 'spinner', // The CSS class to assign to the spinner
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    top: 'auto', // Top position relative to parent in px
    left: 'auto' // Left position relative to parent in px
};

/* Our spinner controller - end */
