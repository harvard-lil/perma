// polyfill for IE8
// via https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/Trim
if (!String.prototype.trim) {
  String.prototype.trim = function () {
    // Make sure we trim BOM and NBSP
    rtrim = /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g;
    return this.replace(rtrim, "");
  };
}


// Initializations
$(document).ready(function() {
    // Add class to active text inputs
    $('.text-input').focus(function() { $(this).addClass('text-input-active'); });
    $('.text-input').blur(function() { $(this).removeClass('text-input-active'); });

    // Select the input text when the user clicks the element
    $('.select-on-click').click(function() { $(this).select(); });
    
    // clear popup alerts with a click
    $(document).on('click', '.popup-alert', function(){
        $(this).remove();
    });

    // show infinity button "Create perma archive" tooltip on hover
    $('.infinity-navbar').tooltip({'trigger': 'hover', 'placement': 'bottom', 'container':'body', 'delay': 350});
});

// Clear fields on focus
$(".clear-on-focus")
  .focus(function() { if (this.value === this.defaultValue) { this.value = ''; } })
  .blur(function() { if (this.value === '') { this.value = this.defaultValue; }
});


// set up jquery to properly set CSRF header on AJAX post
// via https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});


// check if this is a retina-style display
// via http://stackoverflow.com/a/20413768
function isHighDensity(){
    return (
        (window.matchMedia &&
            (window.matchMedia('only screen and (min-resolution: 124dpi), only screen and (min-resolution: 1.3dppx), only screen and (min-resolution: 48.8dpcm)').matches ||
             window.matchMedia('only screen and (-webkit-min-device-pixel-ratio: 1.3), only screen and (-o-min-device-pixel-ratio: 2.6/2), only screen and (min--moz-device-pixel-ratio: 1.3), only screen and (min-device-pixel-ratio: 1.3)').matches
        )) || (window.devicePixelRatio && window.devicePixelRatio > 1.3));
}


function informUser(message, alertClass){
    /*
        Show user some information at top of screen.
        alertClass options are 'success', 'info', 'warning', 'danger'
     */
    $('.popup-alert button.close').click();
    alertClass = alertClass || "info";
    $('<div class="alert alert-'+alertClass+' alert-dismissible popup-alert" role="alert" style="display: none">' +
          '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'+
          message +
      '</div>').prependTo('body').fadeIn('fast');
}


function apiRequest(method, url, data, requestArgs){
    // set up arguments for API request
    requestArgs = typeof requestArgs !== 'undefined' ? requestArgs : {};

    if(data){
        if(method == "GET"){
            requestArgs.data = data;
        }else {
            requestArgs.data = JSON.stringify(data);
            requestArgs.contentType = 'application/json';
        }
    }

    requestArgs.url = api_path + url;
    requestArgs.method = method;

    if(!('error' in requestArgs))
        requestArgs.error = showAPIError;

    return $.ajax(requestArgs);
}

// parse and display error results from API
function showAPIError(jqXHR){
    var message;

    if(jqXHR.status == 400 && jqXHR.responseText){
        try{
            var parsedResponse = JSON.parse(jqXHR.responseText);
            while(typeof parsedResponse == 'object'){
                for(var key in parsedResponse){
                    if (parsedResponse.hasOwnProperty(key)){
                        parsedResponse = parsedResponse[key];
                        break;
                    }
                }
            }
            message = parsedResponse;
        }catch(SyntaxError){}
    }else if(jqXHR.status == 401){
        message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
    }else{
        message = "Error " + jqXHR.status;
    }

    informUser(message, 'danger');
}

// set margins for modal windows
// currently set to hit only special elements

$(document).ready(function() {
	var windowHeight = $(window).height();
	var windowWidth = $(window).width();
	$('.modal-new').each(function() {
		var thisHeight = $(this).actual('height');
		var opticalOffset = (windowHeight - thisHeight) / 12;
		var marginTop = 0 - opticalOffset - (thisHeight / 2);
		if(windowWidth < 767) {}
		else if( opticalOffset > 0) {
			$(this).css('margin-top', marginTop);
		} else {
			$(this).addClass('_overflow');
		}
	});	
});

// initialize fastclick
$(function() {
    FastClick.attach(document.body);
});