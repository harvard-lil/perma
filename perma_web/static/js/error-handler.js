var airbrakeJs = require('airbrake-js');
var airbrakeJs_instrumentation_jquery = require('airbrake-js/instrumentation/jquery')

export function resolve(error_id) {
  $.ajax({
    type: 'POST',
    url: '/manage/errors/resolve',
    data: {'error_id':error_id},
  });
}

export var airbrake = undefined;

export function init() {
  airbrake = new airbrakeJs({reporter: 'xhr', host: '/errors/new?'});

  window.onerror = airbrake.onerror;

  // in debug mode, monkey-patch airbrake.notify() to log the error to the console
  if (typeof settings !== 'undefined' && settings.DEBUG) {
    airbrake.notify = function (err) {
      console.error(err.error ? err.error.stack : err);
      return this.__proto__.notify.apply(this, arguments);  // call real notify() method
    };
  }

  // add listener for jquery errors
  if (window.jQuery) {
    airbrakeJs_instrumentation_jquery(airbrake, jQuery);
  }
}
