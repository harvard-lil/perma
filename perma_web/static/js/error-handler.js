var ErrorHandler = {};

ErrorHandler.notify = function(message, error) {
  var err = new Error(error);
  error_object = {
    'current_url': window.location.pathname,
    'user_agent': navigator.userAgent,
    'stack': err.stack,
    'name': err.name,
    'message': err.message,
    'custom_message': message
  }
  $.ajax({
    type: 'POST',
    url: '/manage/errors/new',
    data: error_object
  });
}

ErrorHandler.resolve = function(error_id) {
  $.ajax({
    type: 'POST',
    url: '/manage/errors/resolve',
    data: {'error_id':error_id}
  });
}

ErrorHandler.init = function () {
  window.onerror = function (e){
    ErrorHandler.notify('Caught exception:', e);
    return false;
  }
}


ErrorHandler.init();

/*
on backend
[title_key] =
  stack_trace: error.stack
  user: user_id
  extra_data: extra data
  useragent string
  url: url
*/
