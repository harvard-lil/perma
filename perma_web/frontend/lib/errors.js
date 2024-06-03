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