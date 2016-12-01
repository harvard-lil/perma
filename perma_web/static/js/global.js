var FastClick = require('fastclick');

var ErrorHandler = require('./error-handler.js');
var Helpers = require('./helpers/general.helpers.js');

require('bootstrap-js/dropdown');  // make menus work
require('bootstrap-js/collapse');  // make menu toggle for small screen work
require('bootstrap-js/carousel');  // make carousels work

// We used to use modernizr but have currently dropped it.
// If we want to include it again this is where to put it --
//    see https://github.com/Modernizr/Modernizr/issues/878#issuecomment-41448059
// https://www.npmjs.com/package/modernizr-webpack-plugin

// initialize fastclick
FastClick.attach(document.body);

// initialize airbrake
ErrorHandler.init();

// set up jquery to properly set CSRF header on AJAX post
// via https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax
$.ajaxSetup({
  crossdomain: false, // obviates need for sameOrigin test
  beforeSend: function(xhr, settings) {
    if (!Helpers.csrfSafeMethod(settings.type)) {
      xhr.setRequestHeader('X-CSRFToken', Helpers.getCookie('csrftoken'));
    }
  }
});

/*** event handlers ***/

// Add class to active text inputs
$('.text-input')
  .focus(function() { $(this).addClass('text-input-active'); })
  .blur(function() { $(this).removeClass('text-input-active'); });

// Select the input text when the user clicks the element
$('.select-on-click').click(function() { $(this).select(); });

// clear popup alerts with a click
$(document).on('click', '.popup-alert', function() {
  $(this).remove();
});

// put focus on first form input element when a form is revealed by bootstrap UI
$('.collapse').on('shown.bs.collapse', function () {
  $(this).find('input[type="text"]').focus();
});

