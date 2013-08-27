var linkyUrl = '';
var rawUrl = '';
var newLinky = {};
var all_links = new Array();

$(document).ready(function() {
  $('#linky-upload-confirm').modal({show: false});
  $('#linky-upload').modal({show: false});

  $('#linker').submit(function() {
		linkIt();
		return false;
	});

  drawLinks();

  $('#linky_upload_form').submit(function(){
	  $(this).ajaxSubmit({success: uploadIt, error: uploadNot});
	    return false;
    });
  });

function uploadNot() {
  $('#upload-error').text('The upload failed');
}

function uploadIt(data) {
  if(data.status == 'success') {
    $('#linky-upload').modal('hide');
	  $('#linky-upload-confirm').modal({show: true});
    var linkyUrl = web_base  + '/' + data.linky_hash;
		$('#linky_upload_success').text('Your linky has been created at');
		$('#uploadedLinkyUrl a').attr('href', linkyUrl).text(linkyUrl);
		newLinky.url = linkyUrl;
    newLinky.original = $('#url').val();
    newLinky.title = $('#title').val();
    newLinky.favicon_url = data.favicon_url;
    addToStorage(newLinky);
    var source = $("#list-template").html();
    var template = Handlebars.compile(source);
    $('#stored-ul').prepend(template(newLinky));
    $('#linky-list').fadeIn();
    drawLinks();
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
    url: web_base + "/api/linky/",
    type: "POST",
    data: {url: rawUrl},
    dataType: "json"
  });
  request.done(function(data) {
    $('#upload-option').fadeIn();
    linkyUrl = web_base  + '/' + data.linky_id;
    newLinky.url = linkyUrl;
    newLinky.original = rawUrl;
    newLinky.title = data.linky_title;
    newLinky.favicon_url = data.favicon_url;
    newLinky.preview = data.linky_cap;
    $('#url').val(rawUrl);
    $('#title').val(data.linky_title);
    
    var source = $("#success-template").html();
    var template = Handlebars.compile(source);
    $('#links').html(template(newLinky));

    var source = $("#list-template").html();
    var template = Handlebars.compile(source);
    $('#stored-ul').prepend(template(newLinky));
    $('#linky-list').fadeIn();

    addToStorage(newLinky);
    drawLinks();
    
    $('#spinner').slideUp();
    $('#link-short-slug').slideDown();
    var clip = new ZeroClipboard( $(".copy-button"), {
      moviePath: web_base + "/static/js/ZeroClipboard/ZeroClipboard.swf"
    });

    clip.on( 'complete', function(client, args) {
      $(this).next('.copy-confirm').html('copied').fadeIn(100).fadeOut(3000);
    });
      
    $('#emailPerma').on('submit', function(event){
      var request = $.ajax({
        url: web_base + "/service/email-confirm/",
        type: "POST",
        data: {email_address: $('#email_request').val(), linky_link: linkyUrl},
        dataType: "json"
      });
    
      return false;
    });
  });
  request.fail(function(jqXHR, responseText) {
    var source = $("#error-template").html();
    var template = Handlebars.compile(source);
    $('#links').html(template({url: rawUrl}));
    $('#spinner').slideUp();
    $('#link-short-slug').slideDown();
  });

}

function drawLinks() {
  if(('localStorage' in window) && window['localStorage'] !== null){
    storedLinkies = JSON.parse(localStorage.getItem('linky-list'));
  }
  if(storedLinkies) {
    $('#home-description').hide();
    allLinkies = storedLinkies;
    storedLinkies.reverse();
    $('#local-ul').html('');
    $.each( storedLinkies, function( key, value ) {
    	//workaround, why isn't Handlebars Helper working?
    	value.url = value.url.replace(/.*?:\/\//g, "");
    	value.original = value.original.replace(/.*?:\/\//g, "");
    	if (value.favicon_url) {
        	value.favicon_url = value.favicon_url.replace(/.*?:\/\//g, "");
    	}
    	//
      var source = $("#list-template").html();
      var template = Handlebars.compile(source);
      $('#local-ul').append(template(value));

      var clip = new ZeroClipboard( $(".copy-button"), {
        moviePath: web_base + "/static/js/ZeroClipboard/ZeroClipboard.swf"
      });

      clip.on( 'complete', function(client, args) {
        $(this).next('.copy-confirm').html('copied').fadeIn(100).fadeOut(3000);
      });
    });
    $('#local-list, #linky-list').fadeIn();
  }
}

function addToStorage(new_link) {
  if(JSON.parse(localStorage.getItem('linky-list'))){
    all_links = JSON.parse(localStorage.getItem('linky-list')) || [];
    if(all_links.length >= 5) {
      all_links.splice(0,1);
    }
  }
  all_links.push(new_link);
  if(('localStorage' in window) && window['localStorage'] !== null){
    localStorage.setItem( 'linky-list', JSON.stringify(all_links));
  }
}

Handlebars.registerHelper ('truncate', function (str, len) {
        if (str.length > len) {
            var new_str = str.substr (0, len+1);

            while (new_str.length) {
                var ch = new_str.substr ( -1 );
                new_str = new_str.substr ( 0, -1 );

                if (ch == ' ') {
                    break;
                }
            }

            if ( new_str == '' ) {
                new_str = str.substr ( 0, len );
            }

            return new Handlebars.SafeString ( new_str +'...' );
        }
        return str;
    });

var upload_form = function(){
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#linky-upload').modal('show');
    return false;
};
