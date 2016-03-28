var ErrorHandler = {};

ErrorHandler.notify = function(message, error) {
  var err = new Error(error);
  user = this.user || 'anonymous';
  errorObj = {}
  $.ajax({
    type: 'POST',
    url: '/manage/errors/new',
    data: errorObj
  });
}


ErrorHandler.init = function () {
  window.onerror = function (e){
    ErrorHandler.notify("dskjfh", {error:'yes'});
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
