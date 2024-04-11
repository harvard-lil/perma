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

  subscriptionStatus: '',
  updateSubscriptionStatus(status) {
    this.subscriptionStatus = status
  },

  userTypes: '',
  updateUserTypes(types) {
    this.userTypes = types
  }
})