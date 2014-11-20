/* Our globals. Look out interwebs - start */

// Where we store our successfully created new archive data
var new_archive = {};

// Where we queue up our archive guids for polling
var refreshIntervalIds = [];

/* Our globals. Look out interwebs - end */



/* Everything that needs to happen at page load - start */

$(document).ready(function() {
    $('#archive-upload-confirm').modal({show: false});
    $('#archive-upload').modal({show: false});

    // When a new url is entered into our form
    $('#linker').submit(function() {
        linkIt();
        return false;
    });

    // When a user uploads their own capture
    $('#archive_upload_form').submit(function() {
        $(this).ajaxSubmit({success: uploadIt, error: uploadNot});
        return false;
    });

    // Toggle users dropdown
    $('#dashboard-users').click(function(){
        $('.users-secondary').toggle();
    });
});

/* Everything that needs to happen at page load - end */



/* Handle the the main action (enter url, hit the button) button - start */

function linkIt(){
    // This does the "get url and exchange it for an archive" through
    // an AJAX post work.

    var rawUrl = $("#rawUrl").val();

    var request = $.ajax({
        url: "/manage/create/",
        type: "POST",
        data: {
            url: rawUrl,
            folder: $('#linker select').val(),
            'csrfmiddlewaretoken': csrf_token
        },
        dataType: "json"
    });

    request.done(function(data) {
        new_archive.url = mirror_server_host  + '/' + data.linky_id;
        new_archive.linky_id = data.linky_id;
        new_archive.original = rawUrl;
        new_archive.title = data.linky_title;
        new_archive.favicon_url = data.favicon_url;
        new_archive.preview = data.linky_cap;
        new_archive.message_pdf = data.message_pdf;
        new_archive.static_prefix = static_prefix;

        var source = $("#success-template").html();
        var template = Handlebars.compile(source);
        $('#preview-container').html(template(new_archive));

        // Get our spinner going now that we're drawing it
        var target = document.getElementById('spinner');
        var spinner = new Spinner(opts).spin(target);

        $('#steps-container').html('');
        $('.preview-row').removeClass('hide').hide().slideDown();

        refreshIntervalIds.push(setInterval(check_status, 2000));

    });
    request.fail(function(jqXHR) {
        var source = $("#preview-failure-template").html();
        var template = Handlebars.compile(source);
        $('#preview-container').html(template({static_prefix:static_prefix}));

        var source = $("#error-template").html();
        var template = Handlebars.compile(source);
        var message = jqXHR.status==400 && jqXHR.responseText ? jqXHR.responseText : "Error "+jqXHR.status;
        $('#steps-container').html(template({
            url: rawUrl,
            message: message
        }));

        $('.preview-row').removeClass('hide').hide().slideDown();
    });
}

/* Handle the the main action (enter url, hit the button) button - start */




/* Handle an upload - start */

function uploadNot() {
    // Display an error message in our upload modal

    $('#upload-error').text('The upload failed. Only gif, jpg, and pdf files supported. Max of 50 MB.');
}

function uploadIt(data) {
    // If a user wants to upload their own screen capture, we display
    // a modal and the form in that modal is handled here

    if(data.status == 'success') {
        $('#archive-upload').modal('hide');

        var upload_image_url = static_prefix + '/img/upload-preview.jpg';
        new_archive.url = mirror_server_host  + '/' + data.linky_id;

        var source = $("#preview-available-no-upload-option-template").html();
        var template = Handlebars.compile(source);
        $('#preview-container').html(template({image_url: upload_image_url, archive_url: new_archive.url}));

        // Get our spinner going now that we're drawing it
        var target = document.getElementById('spinner');
        var spinner = new Spinner(opts).spin(target);

        var source = $("#success-steps-template").html();
        var template = Handlebars.compile(source);
        $('#steps-container').html(template({url: new_archive.url,
            userguide_url: userguide_url, vesting_privs: vesting_privs})).removeClass('hide').hide().slideDown();
    }
    else {
        return xhr.abort();
    }
}

function upload_form() {
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#archive-upload').modal('show');
    return false;
}

/* Handle an upload - end */



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
	var request = $.ajax({
		url: status_url + new_archive.linky_id,
		type: "GET",
		dataType: "json",
		cache: false
	});

	request.done(function(data) {

		// if no status is pending
		if (data.image_capture !== 'pending') {

            // Replace our Archive Pending spinner and message
            // with our new thumbnail
            var image_url = data.thumbnail;

            var source = $("#preview-available-template").html();
            var template = Handlebars.compile(source);
            $('#preview-container').html(template({image_url: image_url,
                archive_url: new_archive.url})).removeClass('hide').hide().slideDown();
                
            var source = $("#success-steps-template").html();
            var template = Handlebars.compile(source);
            $('#steps-container').html(template({url: new_archive.url, userguide_url: userguide_url,
                vesting_privs: vesting_privs})).removeClass('hide').hide().slideDown();

            // Clear out our pending jobs
            $.each(refreshIntervalIds, function(ndx, id) {
			    clearInterval(id);
			});

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