// polyfill for IE8
// via https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/Trim
if (!String.prototype.trim) {
  String.prototype.trim = function () {
    // Make sure we trim BOM and NBSP
    rtrim = /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g;
    return this.replace(rtrim, "");
  };
}

// Set CSRF on every local request
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type == 'POST' || settings.type == 'PUT' || settings.type == 'DELETE') {
            var hostname = $('<a>').prop('href', settings.url).prop('hostname');
            if ( hostname == location.hostname) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    }
});

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
});

// Clear fields on focus
$(".clear-on-focus")
  .focus(function() { if (this.value === this.defaultValue) { this.value = ''; } })
  .blur(function() { if (this.value === '') { this.value = this.defaultValue; }
});

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
