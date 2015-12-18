/* Our globals. Look out interwebs - start */

// Where we store our successfully created new archive data
var new_archive = {};

// Where we queue up our archive guids for polling
var refreshIntervalIds = [];

var spinner;

/* Our globals. Look out interwebs - end */



/* Everything that needs to happen at page load - start */

$(function() {

	$organization_select = $("#organization_select");

    $('#archive-upload-confirm').modal({show: false});
    $('#archive-upload').modal({show: false});


    // When a new url is entered into our form
    $('#linker').submit(function() {
        var $this = $(this);
        var linker_data = {};

				var selectedFolder = getSelectedFolder();

        if(selectedFolder){
		    	linker_data = {
		          url: $this.find("input[name=url]").val(),
		          organization: selectedFolder.orgID,
		          folder: selectedFolder.folderID
					}
		    } else {
	        	linker_data = {
	        		url: $this.find("input[name=url]").val()
	        	};
	      }
        // Start our spinner and disable our input field with just a tiny delay
        window.setTimeout(toggleCreateAvailable, 150);

        $.ajax($this.attr('action'), {
            method: $this.attr('method'),
            contentType: 'application/json',
            data: JSON.stringify(linker_data),
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


    /* Org affiliation dropdown logic */

    // Toggle users dropdown
    $('#dashboard-users').click(function(){
        $('.users-secondary').toggle();
    });
    
    apiRequest("GET", "/user/organizations/", {limit: 300, order_by:'registrar'})
        .success(function(data) {
            var sorted = [];
            Object.keys(data.objects).sort(function(a,b){
                return data.objects[a].registrar < data.objects[b].registrar ? -1 : 1;
            }).forEach(function(key){
                sorted.push(data.objects[key]);
            });
            data.objects = sorted;
            if (data.objects.length > 0) {
            	var optgroup = data.objects[0].registrar;
                data.objects.map(function (organization) {
                    if(organization.registrar !== optgroup) {
                    	$organization_select.prepend("<li class='dropdown-header'>" + optgroup + "</li>");
                        optgroup = organization.registrar;
                        $organization_select.append("<li class='dropdown-header'>" + optgroup + "</li>");
                    }
                    var opt_text = organization.name;
                    if (organization.default_to_private) {
                    	opt_text += ' <span class="ui-private">(Private)</span>';	
                    }
                    if(selected_organization == organization.id) {
                    	$('#organization_select_form').find('.dropdown-toggle').html(opt_text);
                    }
                    else {
                    	$organization_select.append("<li><a onClick='appendURL("+organization.id+")'>" + opt_text + "</a></li>");
                    }
                });
								$organization_select.append("<li><a onClick='appendURL()'> My Links <span class='links-remaining'>" + links_remaining + "<span></a></li>");
            }
        });

    /* Org affiliation dropdown logic - end */
});

/* Everything that needs to happen at page load - end */

function getSelectedFolder () {
	var selectedFolder = localStorage.getItem("perma_selected_folder");

	if(selectedFolder){
		var folderObj = JSON.parse(selectedFolder);
	}
	return folderObj
}

/* Handle the the main action (enter url, hit the button) button - start */

function linkIt(data){
    // Success message from API. We should have a GUID now (but the
    // archive is still be generated)


    // Clear any error messages out
    $('.error-row').remove();

    new_archive.guid = data.guid;

    refreshIntervalIds.push(setInterval(check_status, 2000));
}

function toggleCreateAvailable() {
    // Get our spinner going and display a "we're working" message
    $addlink = $('#addlink');
    if ($addlink.hasClass('_isWorking')) {
        $addlink.html('Create Perma Link').removeAttr('disabled').removeClass('_isWorking');
        spinner.stop();
        $('#rawUrl, #organization_select_form button').removeAttr('disabled');
        $('#links-remaining-message').removeClass('_isWorking');
    } else {
        $addlink.html('<div id="capture-status">Creating your Perma Link</div>').attr('disabled', 'disabled').addClass('_isWorking');
        spinner = new Spinner(opts);
        spinner.spin($addlink[0]);
        $('#rawUrl, #organization_select_form button').attr('disabled', 'disabled');
        $('#links-remaining-message').addClass('_isWorking');
    }
}


function linkNot(jqXHR){
    // The API told us something went wrong.

    if(jqXHR.status == 401){
    // special handling if user becomes unexpectedly logged out
        showAPIError(jqXHR);
    }else {

        var message = "";
        if (jqXHR.status == 400 && jqXHR.responseText) {
            var errors = JSON.parse(jqXHR.responseText).archives;
            for (var prop in errors) {
                message += errors[prop] + " ";
            }
        }

        var upload_allowed = true;
        if (message.indexOf("limit") > -1) {
            $('.links-remaining').text('0');
            upload_allowed = false;
        }

        $('#error-container').html(templates.error({
            message: message || "Error " + jqXHR.status,
            upload_allowed: upload_allowed,
            contact_url: contact_url
        }));

        $('.create-errors').addClass('_active');
        $('#error-container').hide().fadeIn(0);
    }

    toggleCreateAvailable();
}

/* Handle the the main action (enter url, hit the button) button - start */




/* Handle an upload - start */

function uploadNot(jqXHR) {
    // Display an error message in our upload modal

    // special handling if user becomes unexpectedly logged out
    if(jqXHR.status == 401){
        showAPIError(jqXHR);
        return;
    }

    var response = jQuery.parseJSON( jqXHR.responseText),
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
    window.location.href = '/' + data.guid;
}

function upload_form() {
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#archive_upload_form input[name="url"]').val($('#rawUrl').val());
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
        if(!capturesPending){

            // Clear out our pending jobs
            $.each(refreshIntervalIds, function(ndx, id) {
                clearInterval(id);
            });

            // If we have at least one success, forward to the new archive
            if(capturesSucceeded){

                window.location.href = "/" + new_archive.guid;

            // Else show failure message/upload form.
            } else {
                $('#error-container').html(templates.error({
                    message: "Error: URL capture failed."
                }));
                $('.error-row').removeClass('hide _error _success _wait').addClass('_error');

                // Toggle our create button
                toggleCreateAvailable();
            }
        }
    });
}

/* Our polling function for the thumbnail completion - end */


/* URL appending */

/* Org selection is link based, so if the user selects an org from
   the dropdown, we link to that page (reloading and losing state on the
    create page). Here, let's grab the URL from the form field and append
it to the org's href (in the org selection dropdown) */

function setNewSelectedPath (orgID) {
	var folder = {'orgID':orgID}
	localStorage.setItem("perma_selected_folder",JSON.stringify(folder));
	$(window).trigger("dropdown.selectionChange");
}
function appendURL(elem) {
	setNewSelectedPath(elem);
  if ($('#rawUrl').val().length > 0) {
      var link_to_create = $(elem).attr("href") + "?url=" + $('#rawUrl').val();
      $(elem).attr("href", link_to_create);
  }
}

/* URL appending - end */

/* Catch incoming URLs as param values. Both from the bookmarklet or from the create page */

// Get parameter by name
// from https://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

// Populate the URL field and submit the "create link" form
$(document).ready(function() {
    var bookmarklet_url = getParameterByName('url');
    if (bookmarklet_url) {
        $('.bookmarklet-button').hide();
        $('#rawUrl').val(bookmarklet_url);
    }
});


/* Catch incoming URLs as param values. Both from the bookmarklet or from the create page - end */




/* Our spinner controller - start */

var opts = {
    lines: 15, // The number of lines to draw
    length: 2, // The length of each line
    width: 2, // The line thickness
    radius: 9, // The radius of the inner circle
    scale: 1, // Scales overall size of the spinner
    corners: 0, // Corner roundness (0..1)
    color: '#2D76EE', // #rgb or #rrggbb or array of colors
    opacity: 0.25, // Opacity of the lines
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    speed: 1, // Rounds per second
    trail: 50, // Afterglow percentage
    fps: 20, // Frames per second when using setTimeout() as a fallback for CSS
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    className: 'spinner', // The CSS class to assign to the spinner
    top: '12px', // Top position relative to parent
    left: '50%', // Left position relative to parent
    shadow: false, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    position: 'absolute' // Element positioning
};

/* Our spinner controller - end */
