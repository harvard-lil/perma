var linkyUrl = '';
var rawUrl = '';
var newLinky = {};
var all_links = new Array();

$(document).ready(function() {
  $('#linky-confirm').modal({show: false});
  $('#linky-upload-confirm').modal({show: false});
  $('#linky-upload').modal({show: false});
  $('#rawUrl').focus();
  
  $('#linker').submit(function() {
		linkIt();
		return false;
	});
	
	$('#email_request').keyup(function() {                   
    if(!$(this).val()) {
      $('#saveLinky').text('Save this Linky');    
    }
    else {
      $('#saveLinky').text('Save and send this Linky');
    }
  });
  
  drawLinks();

  $('#linky_upload_form').submit(function(){
	  $('#linky-upload').modal('hide');
	  $('#linky-upload-confirm').modal({show: true});
	  $(this).ajaxSubmit(function(data){
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
      drawLinks();
	  });
	  return false;
    });
  });

function linkIt(){
  var source = $("#loading-template").html();
    var template = Handlebars.compile(source);
    $('#linky-confirm .modal-body').html(template({'src': web_base + '/static/img/infinity_500_400.gif'}));
    $('#upload-option').hide();

  rawUrl = $("#rawUrl").val();
  $('#url').val(rawUrl);
  var request = $.ajax({
    url: web_base + "/api/linky/",
    type: "POST",
    data: {url: rawUrl},
    dataType: "json"
  });
  request.done(function(data) {
    $('#linky_generation_message').html('Your linky has been created at');
    $('#linky-desc').removeClass('unavailable');
    $('#upload-option').fadeIn();
    linkyUrl = web_base  + '/' + data.linky_id;
    newLinky.url = linkyUrl;
    newLinky.original = rawUrl;
    newLinky.title = data.linky_title;
    newLinky.favicon_url = data.favicon_url;

    var source = $("#list-template").html();
    var template = Handlebars.compile(source);
    $('#stored-ul').prepend(template(newLinky));

    addToStorage(newLinky);
    $('#linkyUrl a').html(web_base  + '/' + data.linky_id).attr('href', web_base + '/' + data.linky_id);
    //$('#linky_title').text(data.linky_title);
    $('#linky-preview img').attr('src', data.linky_url);
  });
  request.fail(function(jqXHR, responseText) {
    var source = $("#error-template").html();
    var template = Handlebars.compile(source);
    $('#linky-confirm .modal-body').html(template({url: rawUrl}));
    $('#linky-desc').removeClass('unavailable');
  });
  
  $('#linky-confirm').modal('show');
  $('#saveLinky').on('click', function(event){
            
    var request = $.ajax({
      url: web_base + "/service/email-confirm/",
      type: "POST",
      data: {email_address: $('#email_request').val(), linky_link: $('#linkyUrl a').attr('href')},
      dataType: "json"
    });
      
    event.preventDefault();
    $('#linky-confirm').modal('hide');
  });
  
  $('#linky-confirm').on('hidden', function () {
    $('#rawUrl').val('').focus();
    $('#local-list').fadeIn();
  
    $('#linky_generation_message').html('Creating your Linky. Hold tight.');
    $('#linkyUrl a').html('').attr('');
    $('#linky-desc').addClass('unavailable');
    drawLinks();
  });
}

function drawLinks() {
  if(('localStorage' in window) && window['localStorage'] !== null){
    storedLinkies = JSON.parse(localStorage.getItem('linky-list'));
  }
  if(storedLinkies) {
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
    $('#local-list').fadeIn();
  }
}

function addToStorage(new_link) {
  if(JSON.parse(localStorage.getItem('linky-list'))){
    all_links = JSON.parse(localStorage.getItem('linky-list'));
    if(all_links.length >= 10) {
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
    $('#linky-upload').modal('show');
    return false;  
};
