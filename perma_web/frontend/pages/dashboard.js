import { createApp, ref } from 'vue'

createApp({
  setup() {
    const message = ref('Hello from Vue!')
    return {
      message
    }
  },
}).mount('#vue-app')
