var ErrorHandler = {};
var airbrake;

ErrorHandler.resolve = function(error_id) {
  $.ajax({
    type: 'POST',
    url: '/manage/errors/resolve',
    data: {'error_id':error_id},
  });
}

ErrorHandler.init = function () {
  airbrake = new airbrakeJs.Client({
    reporter: 'xhr',
    host: '/errors/new?'
  });

  // in debug mode, monkey-patch airbrake.notify() to log the error to the console
  if (settings.DEBUG) {
    airbrake.notify = function (err) {
      console.error(err.error ? err.error.stack : err);
      return this.__proto__.notify.apply(this, arguments);  // call real notify() method
    };
  }

  // add listener for jquery errors
  if (window.jQuery) {
    airbrakeJs.instrumentation.jquery(airbrake, jQuery);
  }

};

ErrorHandler.init();
