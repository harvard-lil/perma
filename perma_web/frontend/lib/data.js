import { ref } from "vue";
import { defaultError } from './errors'
import { rootUrl } from './consts'
import { getCookie } from './helpers'

export const fetchDataOrError = async (url, options = {}) => {
  /* return {data, error} for a json fetch call*/
  url = rootUrl + url;

  // add query string from options.params
  if (options.params) {
    url += `?${new URLSearchParams(options.params)}`;
    delete options.params;
  }
  
  // add csrf and content type headers
  if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(options.method)) {
    options.headers = {
      ...options.headers,
      "X-CSRFToken": getCookie("csrftoken"),
    };

    // process options.data
    if (options.data) {
      if (options.data instanceof FormData) {
        // For FormData, let the browser set the Content-Type
        options.body = options.data;
      } else {
        // For JSON data
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.data);
      }
      delete options.data;
    }
  }

  let response = null;
  try {
    response = await fetch(url, options);
    if (!response?.ok) {
      throw new Error(response.statusText);
    }
    return {data: await response.json(), error: null, response}
  } catch (err) {
    return {data: await response?.json().catch(() => null), error: err?.message || defaultError, response}
  }
}

export const useFetch = (url) => {
  const isLoading = ref(false);
  const hasError = ref(false);
  const error = ref('');
  const data = ref(null);

  const fetchData = async (options = {}) => {
    data.value = null;
    error.value = '';
    hasError.value = false;
    isLoading.value = true;

    const {data: dataValue, error: errorValue} = await fetchDataOrError(url, options);
    
    data.value = dataValue;
    error.value = errorValue;
    hasError.value = !!errorValue;
    isLoading.value = false;
  };

  return { isLoading, hasError, error, data, fetchData }
}
