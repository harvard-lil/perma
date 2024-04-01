import { reactive } from 'vue'

export const globalStore = reactive({
  captureStatus: 'ready',
  updateCapture(state) {
    captureStatus = state
  },

  count: 0,
  increment() {
    this.count++
  }
})