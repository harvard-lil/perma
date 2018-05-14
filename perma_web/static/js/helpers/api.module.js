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
  let message;

  if (jqXHR.status == 400 && jqXHR.responseText) {
    try {
      message = stripDataStructure(JSON.parse(jqXHR.responseText));
    } catch (SyntaxError) {
      ErrorHandler.airbrake.notify(SyntaxError);
    }
  } else if (jqXHR.status == 401) {
    message = "<a href='/login'>You appear to be logged out. Please click here to log back in</a>.";
  } else if (jqXHR.status) {
    message = "Error " + jqXHR.status;
  } else {
    message = "We're sorry, we've encountered an error processing your request."
  }

  return message;
}

export function stripDataStructure (object){
  let parsedResponse = object;
  while(typeof parsedResponse == 'object') {
    for (let key in parsedResponse) {
      if (parsedResponse.hasOwnProperty(key)) {
        parsedResponse = parsedResponse[key];
        break;
      }
    }
  }
  return parsedResponse;
}

// display error results from API
export function showError (jqXHR) {
  var message = getErrorMessage(jqXHR);
  Helpers.informUser(message, 'danger');
}
