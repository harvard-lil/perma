import { reactive } from 'vue'

export const globalStore = reactive({
  captureStatus: 'ready',
  updateCapture(state) {
    this.captureStatus = state
  },

  captureErrorMessage: '',
  updateCaptureErrorMessage(message) {
    this.captureErrorMessage = message
  },

  linksRemainingStatus: '',
  updateLinksRemainingStatus(status) {
    this.linksRemainingStatus = status
  },

  userTypes: [],
  updateUserTypes(types) {
    this.userTypes = types
  }
})