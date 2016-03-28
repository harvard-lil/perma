var ErrorHandler = {};

ErrorHandler.notify = function(message, error) {
  var err = new Error(error);

  error_object = {
    'current_url': window.location.href,
    'user_agent': navigator.userAgent,
    'error_stack': JSON.stringify(err.stack),
    'error_name': err.name,
    'error_message': err.message,
    'error_custom_message': message
  }
  $.ajax({
    type: 'POST',
    url: '/manage/errors/new',
    data: error_object
  });
}


ErrorHandler.init = function () {
  window.onerror = function (e){
    ErrorHandler.notify('Caught exception:', {error:e});
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
