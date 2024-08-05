export const getUniqueErrorValues = (formData, errors) => {
  return Object.keys(errors).reduce((acc, key) => {
      if (!(key in formData)) {
          return [...acc, ...errors[key]];
      }
      return acc;
  }, []);
}

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

 export const getErrorFromResponseStatus = (status, response) => {
    let errorMessage

    switch (status) {
        case 400:
            errorMessage = getErrorFromNestedObject(response)
            break;
        case 401:
            errorMessage = "You appear to be logged out."
            break;
        default:
            errorMessage = `Error: ${status}`
            break;
    }

    if (errorMessage.includes("Error 0")) {
        errorMessage = "Perma.cc Temporarily Unavailable"
    }

    return errorMessage
}

export const getErrorResponse = async (response) => {
  try {
      const errorBody = await response.json();
      return { status: response.status, response: errorBody }
  } catch (error) {
      return { status: response.status };
  }
};

export const defaultError = "We're sorry, we've encountered an error processing your request."
export const folderError = "Missing folder selection. Please select a folder."
export const missingUrlError = "Missing urls. Please submit valid urls."
