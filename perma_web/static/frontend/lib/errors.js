// Returns the first error string nested within an API error response object
// For example, passing {"url":["URL cannot be empty."]} would return "URL cannot be empty."
export const getErrorFromNestedObject = (object) => {
  const getString = (obj) => {
    if (typeof obj === 'string') {
      return obj;
    }

    if (typeof obj === 'object' && obj !== null) {
      return Object.keys(obj)
        .map(key => getString(obj[key]))
        .find(result => result !== undefined);
    }

    return undefined;
  };

  return getString(object) || null;
}

export const getErrorFromStatus = (status) => {
  if (status === 401) {
    return loggedOutError
  }

  return `Error: ${status}`
}

export const getErrorFromStatusOrData = (status, response) => {
  let errorMessage

  switch (status) {
    case 400:
      errorMessage = getErrorFromNestedObject(response)
      break;
    case 401:
      errorMessage = loggedOutError
      break;
    default:
      errorMessage = `Error: ${status}`
      break;
  }

  if (errorMessage.includes("Error 0")) {
    errorMessage = "Perma.cc is temporarily unavailable"
  }

  return errorMessage
}

export const getErrorMessages = (error, data, response, formFields = []) => {
  /* 
    Process the output of fetchDataOrError, returning an object with formErrors and globalErrors.
    This has to handle a few states: we may or may not have a response object, and if we do, it may or may not have data.
    If there is data, it could be form-field-specific errors from Django that we want to render by their form fields,
    or it could be some other data that we want to render as a global error.
    formFields is an array of form field names that we want to check for in the data.

    This method should err towards showing more information to the user in cases of ambiguity, rather than less,
    so they can give us useful information if there's an error state we're not handling.

    Return value is an object with formErrors and globalError:
    - formErrors is an object with keys for each form field that has an error, and values of arrays of error messages.
    - globalError is a single string with a message to show to the user.
  */
  // no response received from server
  if (!response) {
    return {formErrors: {}, globalError: `${defaultError} ${error}`}
  }

  // logged out
  if (response.status === 401) {
    return {formErrors: {}, globalError: loggedOutError}
  }

  // response received from server, and it came with a json payload
  if (data && Object.keys(data).length > 0) {
    // form field errors
    if (formFields) {
      let matches = {};
      for (const field of formFields) {
        if (data.hasOwnProperty(field)) {
          matches[field] = data[field]
        }
      }
      if (Object.keys(matches).length > 0) {
        return {formErrors: matches, globalError: null}
      }
    }

    // some other data django sent us, such as status 405 with {"detail":"Method \"POST\" not allowed."}
    return {formErrors: {}, globalError: `${error} - ${getErrorFromNestedObject(data)}`}
  }

  // other error
  return {formErrors: {}, globalError: `${error} (${response.status})`}
}

export const getErrorResponse = async (response) => {
  try {
    const errorBody = await response.json();
    return {status: response.status, response: errorBody}
  } catch (error) {
    return {status: response.status};
  }
};

export const defaultError = "We're sorry, we've encountered an error processing your request."
export const loggedOutError = "You appear to be logged out."
export const folderError = "No folder selected: please select a folder."
export const missingUrlError = "Missing URLs: please submit a list of valid URLs."
