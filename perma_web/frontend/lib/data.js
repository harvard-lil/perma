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
      "Content-Type": "application/json"
    };
  }

  try {
    const response = await fetch(url, options);
    if (!response?.ok) {
      throw new Error(response.statusText);
    }
    return {data: await response.json(), error: ''}
  } catch (err) {
    return {data: null, error: err?.message || defaultError}
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
