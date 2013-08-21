var linkyUrl = '';
var rawUrl = '';
var newLinky = {};
var all_links = new Array();

$(document).ready(function() {
  $('#linky-upload-confirm').modal({show: false});
  $('#linky-upload').modal({show: false});
  //$('#rawUrl').focus();

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
  var source = $("#loading-template").html();
  var template = Handlebars.compile(source);
  $('#linky-confirm .modal-body').html(template({'src': web_base + '/static/img/infinity_500_400.gif'}));
  $('#upload-option').hide();
  $('#links').empty();
  $('.add-links-list').slideDown();
  $('#spinner').slideDown();

  rawUrl = $("#rawUrl").val();
  $('#url').val(rawUrl);
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

    var source = $("#list-template").html();
    var template = Handlebars.compile(source);
    $('#stored-ul').prepend(template(newLinky));
    $('#linky-list').fadeIn();

    addToStorage(newLinky);
    drawLinks();
      str = '<li id="link-short-slug" class="library-link-item" style="display: none;">'; // TODO move inline styles to style.css
      str += '<div class="library-thumbnail"><a href="/' + linkyUrl + '" target="_blank"><img src="' + data.linky_cap + '" /></a></div>'
      str += '<div class="link-results">'; // to keep everything on the same line during jQuery shake
      str += '<a href="' + linkyUrl + '" class="anchor-short-slug" target="_blank">' + linkyUrl + '</a>';
      str += '<input type="text" class="url-extension url-extension-form-';
      str += 'short-slug" value="short-slug" />';
      str += '<input type="hidden" class="slug-short-slug" value="short-slug" />';

      // BREAK
      str += '<p class="library-link-title">' + data.linky_title + '</p>'
      str += '<p class="library-link-url"><a href="' + rawUrl + '">' + rawUrl + '</a></p>'
      str += '<p class="library-link-meta">';
      str += '<a class="copy-button" data-clipboard-text="' + linkyUrl + '" title="Copy Linky Link">Copy Perma &infin;</a>';
      str += '</p>';
      // END BREAK
            
      // TODO update static url
      str += '<form class="form-inline" id="emailPerma">';
      str += '<input id="email_request" type="text" placeholder="user@example.com">';
      str += '<button type="submit" class="btn">Email this Perma</button>';
      str += '</form>'
      str += '<p id="upload-option">Perma capture not right? <a href="" onclick="return upload_form();">Upload your own</a>.</p>';
      str += '</div><!--/.link-results-->'; 
      str += '</li>';
      
      $('#links').prepend(str);
      $('#spinner').slideUp();
      $('#link-short-slug').slideDown();
      var clip = new ZeroClipboard( document.getElementsByClassName("copy-button"), {
        moviePath: web_base + "/static/js/ZeroClipboard/ZeroClipboard.swf"
      });

      clip.on( 'complete', function(client, args) {
        $(this).next('.copy-confirm').html('copied').fadeIn(100).fadeOut(3000);
      });
      
      $('#emailPerma').on('submit', function(event){
        //var email_address = ;
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

      var clip = new ZeroClipboard( document.getElementsByClassName("copy-button"), {
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

Handlebars.registerHelper ('http_it', function (str) {
        if (str.substring(0,4) != 'http') {
            return new Handlebars.SafeString ( 'http://' + str );
        }
        return str;
    });

var upload_form = function(){
    $('#linky-confirm').modal('hide');
    $('#upload-error').text('');
    $('#linky-upload').modal('show');
    return false;
};
