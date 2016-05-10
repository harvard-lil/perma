var ErrorHandler = {};

var airbrake = new airbrakeJs.Client({
  reporter: 'xhr',
  host: '/errors/new?'
});

ErrorHandler.resolve = function(error_id) {
  $.ajax({
    type: 'POST',
    url: '/manage/errors/resolve',
    data: {'error_id':error_id}
  });
}

ErrorHandler.init = function () {
  window.onerror = airbrake.onerror;
  if (window.jQuery) {
    airbrakeJs.instrumentation.jquery(airbrake, jQuery);
  }
}

ErrorHandler.init();
