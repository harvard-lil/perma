import * as Sentry from "@sentry/browser";

if (settings.USE_SENTRY) {
  Sentry.init({
    dsn: settings.SENTRY_DSN,
    environment: settings.SENTRY_ENVIRONMENT,
    release: settings.SENTRY_RELEASE || undefined,
    // Report errors from Perma's own scripts: not from browser extensions,
    // the playback host, or copies of a page saved and opened from disk.
    // Strings match as substrings.
    allowUrls: [window.location.origin + '/'].concat(
      /^https?:\/\//.test(settings.STATIC_URL) ? [settings.STATIC_URL] : []
    ),
    ignoreErrors: [
      // Outlook's Safe Links scanner, visiting links in email
      'Object Not Found Matching Id',
      // browser extensions messaging their own background pages; Perma's
      // scripts make no such calls
      'Could not establish connection. Receiving end does not exist.',
      'Invalid call to runtime.sendMessage(). Tab not found.',
    ],

    // Set tracesSampleRate to 1.0 to capture 100%
    // of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: settings.SENTRY_TRACES_SAMPLE_RATE,

  });
}

var Helpers = require('./helpers/general.helpers.js');
require('./helpers/fix-links.js');  // https://github.com/harvard-lil/accessibility-tools/tree/master/code/fix-links


require('bootstrap-js/dropdown');  // make menus work
require('bootstrap-js/collapse');  // make menu toggle for small screen work
require('bootstrap-js/tab');       // make tabs work (used on /manage/stats)

// We used to use modernizr but have currently dropped it.
// If we want to include it again this is where to put it --
//    see https://github.com/Modernizr/Modernizr/issues/878#issuecomment-41448059
// https://www.npmjs.com/package/modernizr-webpack-plugin

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

// Put focus on the first text input when a Bootstrap form is revealed.
$('.collapse').on('shown.bs.collapse', function () {
  $(this).find('input[type="text"]').focus();
});

// add trap to contact and report forms
$('.contact-form form').submit(function() {
  $(this).append('<input type="hidden" name="javascript" value="true"> ');
});

// add trap to signup forms
$('.signup-learnMore-form form').submit(function() {
  $(this).append('<input type="hidden" name="javascript" value="true"> ');
});

