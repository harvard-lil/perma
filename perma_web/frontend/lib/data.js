import { reactive, toRefs } from "vue";
import { defaultError } from './errors'

export const useFetch = async (baseUrl, options) => {
  const state = reactive({
    isLoading: false,
    hasError: false,
    errorMessage: '',
    data: null
  })

  const url = options ? `${baseUrl}?${new URLSearchParams(options)}` : baseUrl

  const fetchData = async () => {
    state.isLoading = true;

    try {
      const response = await fetch(url); 
      if (!response?.ok) {
        throw new Error(response.statusText) 
      }

      state.data = await response.json()

    } catch (err) {
      state.hasError = true
      state.errorMessage = err?.message.length ? err.message : defaultError
    }
    state.isLoading = false
  }
  await fetchData()
  return {
    ...toRefs(state)
  }
}