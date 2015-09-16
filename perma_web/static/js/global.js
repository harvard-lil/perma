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
    
    $('.preview-row').on('click', '#report-error', function() {
        var brokenLink = $('#rawUrl').val();
        $('#broken-link-report').html('<strong id="broken-link">' + brokenLink + '</strong> is causing an error.');
    });
    
    $('#feedbackModal').on('hidden.bs.modal', function (e) {
        $('.feedback-form-inputs').show();
        $('.feedback-form-submitted').hide();
        $('#broken-link-report').html('');
        $('form.feedback').find("input[type=email], textarea").val("");
        $('#user_email').val(user_email);
    });

    
    $("input#submit-feedback").click(function(){
      var data = $('form.feedback').serializeArray();

      // todo -- is this necessary with our global csrf cookie js?
      var csrftoken = getCookie('csrftoken');
      data.push({name: 'csrfmiddlewaretoken', value: csrftoken});

      data.push({name: 'visited_page', value: $(location).attr('href')});
      var brokenLink = $('#broken-link').text();
      if(brokenLink)
        data.push({name: 'broken_link', value: brokenLink});
        $.ajax({
            type: "POST",
            url: feedback_url, //process to mail
            data: data,
            success: function(msg){
                //$("#feedbackModal").modal('hide'); //hide popup 
                $('.feedback-form-inputs').slideUp();
                $('.feedback-form-submitted').fadeIn();
            },
            error: function(){
                alert("failure");
            }
        });
      return false;
    });

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
    }

    if(!message){
        message = "Error " + jqXHR.status;
    }

    informUser(message, 'danger');
}


// jquery plugin to allow finding actual dims of hidden elements

/*! Copyright 2012, Ben Lin (http://dreamerslab.com/)
 * Licensed under the MIT License (LICENSE.txt).
 *
 * Version: 1.0.16
 *
 * Requires: jQuery >= 1.2.3
 */
;( function ( factory ) {
if ( typeof define === 'function' && define.amd ) {
    // AMD. Register module depending on jQuery using requirejs define.
    define( ['jquery'], factory );
} else {
    // No AMD.
    factory( jQuery );
}
}( function ( $ ){
  $.fn.addBack = $.fn.addBack || $.fn.andSelf;

  $.fn.extend({

    actual : function ( method, options ){
      // check if the jQuery method exist
      if( !this[ method ]){
        throw '$.actual => The jQuery method "' + method + '" you called does not exist';
      }

      var defaults = {
        absolute      : false,
        clone         : false,
        includeMargin : false,
        display       : 'block'
      };

      var configs = $.extend( defaults, options );

      var $target = this.eq( 0 );
      var fix, restore;

      if( configs.clone === true ){
        fix = function (){
          var style = 'position: absolute !important; top: -1000 !important; ';

          // this is useful with css3pie
          $target = $target.
            clone().
            attr( 'style', style ).
            appendTo( 'body' );
        };

        restore = function (){
          // remove DOM element after getting the width
          $target.remove();
        };
      }else{
        var tmp   = [];
        var style = '';
        var $hidden;

        fix = function (){
          // get all hidden parents
          $hidden = $target.parents().addBack().filter( ':hidden' );
          style   += 'visibility: hidden !important; display: ' + configs.display + ' !important; ';

          if( configs.absolute === true ) style += 'position: absolute !important; ';

          // save the origin style props
          // set the hidden el css to be got the actual value later
          $hidden.each( function (){
            // Save original style. If no style was set, attr() returns undefined
            var $this     = $( this );
            var thisStyle = $this.attr( 'style' );

            tmp.push( thisStyle );
            // Retain as much of the original style as possible, if there is one
            $this.attr( 'style', thisStyle ? thisStyle + ';' + style : style );
          });
        };

        restore = function (){
          // restore origin style values
          $hidden.each( function ( i ){
            var $this = $( this );
            var _tmp  = tmp[ i ];

            if( _tmp === undefined ){
              $this.removeAttr( 'style' );
            }else{
              $this.attr( 'style', _tmp );
            }
          });
        };
      }

      fix();
      // get the actual value with user specific methed
      // it can be 'width', 'height', 'outerWidth', 'innerWidth'... etc
      // configs.includeMargin only works for 'outerWidth' and 'outerHeight'
      var actual = /(outer)/.test( method ) ?
        $target[ method ]( configs.includeMargin ) :
        $target[ method ]();

      restore();
      // IMPORTANT, this plugin only return the value of the first element
      return actual;
    }
  });
}));


// set margins for modal windows
// currently set to hit only special elements

$(function() {
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