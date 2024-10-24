import '@/css/style-responsive.scss';
import '@/vendors/font-awesome/font-awesome.min.css';

import * as Sentry from "@sentry/browser";

if (settings.USE_SENTRY) {
  Sentry.init({
    dsn: settings.SENTRY_DSN,
    environment: settings.SENTRY_ENVIRONMENT,
    denyUrls: ['^https\:\/\/' + settings.PLAYBACK_HOST + '\/.*$'],

    // Set tracesSampleRate to 1.0 to capture 100%
    // of transactions for performance monitoring.
    // We recommend adjusting this value in production
    tracesSampleRate: settings.SENTRY_TRACES_SAMPLE_RATE,

  });
}

import * as Helpers from './helpers/general.helpers.js';
import './helpers/fix-links.js';  // https://github.com/harvard-lil/accessibility-tools/tree/master/code/fix-links

import 'bootstrap-js/dropdown';  // make menus work
import 'bootstrap-js/collapse';  // make menu toggle for small screen work
import 'bootstrap-js/carousel';  // make carousels work
import 'bootstrap-js/tab';       // make tabs work (used on /manage/stats)

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

// put focus on first form input element when a form is revealed by bootstrap UI
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

