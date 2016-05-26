var Helpers = {};

Helpers.apiRequest = function (method, url, data, requestArgs){
  // set up arguments for API request
  requestArgs = typeof requestArgs !== 'undefined' ? requestArgs : {};

  if(data){
    if (method == 'GET') {
      requestArgs.data = data;
    } else {
      requestArgs.data = JSON.stringify(data);
      requestArgs.contentType = 'application/json';
    }
  }

  requestArgs.url = api_path + url;
  requestArgs.method = method;

  if(!('error' in requestArgs))
    requestArgs.error = Helpers.showAPIError;

  return $.ajax(requestArgs);
}

// parse and display error results from API
Helpers.showAPIError = function (jqXHR) {
  var message;

  if (jqXHR.status == 400 && jqXHR.responseText) {
    try {
      var parsedResponse = JSON.parse(jqXHR.responseText);
      while(typeof parsedResponse == 'object') {
        for (var key in parsedResponse) {
          if (parsedResponse.hasOwnProperty(key)) {
            parsedResponse = parsedResponse[key];
            break;
          }
        }
      }
      message = parsedResponse;
    } catch (SyntaxError) {
      airbrake.notify(SyntaxError);
    }
  } else if (jqXHR.status == 401) {
    message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
  } else {
    message = 'Error ' + jqXHR.status;
  }
  Helpers.informUser(message, 'danger');
}

Helpers.informUser = function (message, alertClass) {
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


// set up jquery to properly set CSRF header on AJAX post
// via https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax

Helpers.getCookie = function (name) {
  var cookieValue;
  if (document.cookie) {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = $.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) == (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

Helpers.csrfSafeMethod = function (method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

// check if this is a retina-style display
// via http://stackoverflow.com/a/20413768
Helpers.isHighDensity = function() {
  return (
    (window.matchMedia &&
      (window.matchMedia('only screen and (min-resolution: 124dpi), only screen and (min-resolution: 1.3dppx), only screen and (min-resolution: 48.8dpcm)').matches ||
       window.matchMedia('only screen and (-webkit-min-device-pixel-ratio: 1.3), only screen and (-o-min-device-pixel-ratio: 2.6/2), only screen and (min--moz-device-pixel-ratio: 1.3), only screen and (min-device-pixel-ratio: 1.3)').matches
    )) || (window.devicePixelRatio && window.devicePixelRatio > 1.3));
}

Helpers.getWindowLocationSearch = function() {
  return window.location.search;
}
