var ErrorHandler = require('../error-handler.js');
var Helpers = require('./general.helpers.js');

// Duplicate from global.js: I can't work out how to avoid duplicating jquery between modules..
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

export function request (method, url, data, requestArgs){
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
    requestArgs.error = showError;

  return $.ajax(requestArgs);
}

// parse error results from API into string for display to user
export function getErrorMessage (jqXHR) {
  let message;

  if (jqXHR.status == 400 && jqXHR.responseText) {
    try {
      message = stringFromNestedObject(JSON.parse(jqXHR.responseText));
    } catch (SyntaxError) {
      // bad json in responseText
      ErrorHandler.airbrake.notify(SyntaxError);
    }
  } else if (jqXHR.status == 401) {
    message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
  } else if (jqXHR.status) {
    message = "Error " + jqXHR.status;
  }

  if (!message) {
    message = "We're sorry, we've encountered an error processing your request."
  }

  return message;
}

// Get the first string value from a nested object.
// For example, return "message" from {"url": "message"} or {"errors": ["message"]}
// Return null if no string is found.
export function stringFromNestedObject (object) {
  if (object) {
    if (typeof object === "object") {
      let keys = Object.keys(object);
      for(let i=0;i<keys.length;i++){
        let result = stringFromNestedObject(object[keys[i]]);
        if (result)
          return result;
      }
    } else if(typeof object === "string") {
      return object;
    }
  }
  return null;
}

// display error results from API
export function showError (jqXHR) {
  var message = getErrorMessage(jqXHR);
  Helpers.informUser(message, 'danger');
}
