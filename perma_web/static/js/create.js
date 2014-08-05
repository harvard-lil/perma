var linkyUrl = '';
var rawUrl = '';
var newLinky = {};
var all_links = new Array();


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
var refreshIntervalIds = [];

function check_status() {
	
// Check our status service to see if we have archiving jobs pending
	var request = $.ajax({
		url: status_url + newLinky.linky_id,
		type: "GET",
		dataType: "json",
		cache: false
	});

	request.done(function(data) {	
		// if no status is pending
		if (data.image_capture !== 'pending') {
	        $('#spinner').slideUp();
	        $('.thumbnail-placeholder').append('<div class="library-thumbnail"><img src="' + 
	            MEDIA_URL + data.path + '/' + data.image_capture + '"></div>');
            $.each(refreshIntervalIds, function(ndx, id) {
			    clearInterval(id);
			});
            $('.library-link-title').text(data.submitted_title);
		}	
	});
}
/* Our polling function for the thumbnail completion - end */


$(document).ready(function() {
  $('#linky-upload-confirm').modal({show: false});
  $('#linky-upload').modal({show: false});

  $('#linker').submit(function() {
		linkIt();
		return false;
	});

  $('#linky_upload_form').submit(function(){
	  $(this).ajaxSubmit({success: uploadIt, error: uploadNot});
	    return false;
    });
  });

function uploadNot() {
  $('#upload-error').text('The upload failed. Only gif, jpg, and pdf files supported. Max of 50 MB.');
}

function uploadIt(data) {
  if(data.status == 'success') {
    $('#linky-upload').modal('hide');

    var linkyUrl = mirror_server_host  + '/' + data.linky_hash;
    var source = $("#upload-confirm-template").html();
    var template = Handlebars.compile(source);
    $('#links').html(template({url: linkyUrl}));
    $('#spinner').slideUp();
    $('#link-short-slug').slideDown();


    //$('#linky-upload-confirm').modal({show: true});
    //var linkyUrl = mirror_server_host  + '/' + data.linky_hash;
    //$('#linky_upload_success').text('Your linky has been created at');
    //$('#uploadedLinkyUrl a').attr('href', linkyUrl).text(linkyUrl);
  }
  else {
    return xhr.abort();
  }
}

function linkIt(){
  $('#upload-option').hide();
  $('#links').empty();
  $('.add-links-list').slideDown();
  $('#spinner').slideDown();

  rawUrl = $("#rawUrl").val();
  
  var request = $.ajax({
    url: main_server_host + "/manage/create/",
    type: "POST",
    data: {url: rawUrl, 'csrfmiddlewaretoken': csrf_token},
    dataType: "json"
  });
  
  request.done(function(data) {
    $('#upload-option').fadeIn();
    linkyUrl = mirror_server_host  + '/' + data.linky_id;
    newLinky.url = linkyUrl;
    newLinky.linky_id = data.linky_id;
    newLinky.original = rawUrl;
    newLinky.title = data.linky_title;
    newLinky.favicon_url = data.favicon_url;
    newLinky.preview = data.linky_cap;
    newLinky.message_pdf = data.message_pdf;
    newLinky.static_prefix = static_prefix;
    $('#url').val(rawUrl);
    $('#title').val(data.linky_title);
    
    var source = $("#success-template").html();
    var template = Handlebars.compile(source);
    $('#links').html(template(newLinky));



    if (newLinky.message_pdf = data.message_pdf) {
        $('#spinner').slideUp();
    } else {
		refreshIntervalIds.push(setInterval(check_status, 2000));
    }
    $('#link-short-slug').slideDown();
    var clip = new ZeroClipboard( $(".copy-button"), {
      moviePath: mirror_server_host + "/static/js/ZeroClipboard/ZeroClipboard.swf"
    });

    clip.on( 'complete', function(client, args) {
      $(this).prev('.copy-confirm').fadeIn(100).fadeOut(3000);
    });
    
      
    if(!swfobject.hasFlashPlayerVersion("1")) {
      $('.copy-button').hide();
    }
  });
  request.fail(function(jqXHR) {
    var source = $("#error-template").html();
    var template = Handlebars.compile(source);
    var message = jqXHR.status==400 && jqXHR.responseText ? jqXHR.responseText : "Error "+jqXHR.status;
    $('#links').html(template({
      url: rawUrl,
      static_prefix: static_prefix,
      message: message
    }));
    $('#spinner').slideUp();
    $('#link-short-slug').slideDown();
  });
}

function upload_form() {
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#linky-upload').modal('show');
    return false;
}