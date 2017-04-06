var ErrorHandler = require('../error-handler.js');
var Helpers = require('./general.helpers.js');

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
      ErrorHandler.airbrake.notify(SyntaxError);
    }
  } else if (jqXHR.status == 401) {
    message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
  } else {
    message = 'Error ' + jqXHR.status;
  }

  return message;
}

// display error results from API
export function showError (jqXHR) {
  var message = getErrorMessage(jqXHR);
  Helpers.informUser(message, 'danger');
}
