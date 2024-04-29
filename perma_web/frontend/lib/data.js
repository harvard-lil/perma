import { reactive, toRefs } from "vue";

export async function useFetch(baseUrl, queryParams) {
  const state = reactive({
    isLoading: false,
    hasError: false,
    errorMessage: '',
    data: null
  })

  const url = queryParams ? `${baseUrl}?${new URLSearchParams(queryParams)}` : baseUrl

  const fetchData = async () => {
    state.isLoading = true;

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('error')
      }

      state.data = await response.json()

    } catch (err) {
      state.hasError = true
      state.errorMessage = err.message
    }
    state.isLoading = false
  }
  await fetchData()
  return {
    ...toRefs(state)
  }
}