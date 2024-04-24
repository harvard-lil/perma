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
  },

  selectedFolder: {
    id: [], 
    orgId: ''
  },

  updateFolderSelection({folderId, orgId}) {
    this.selectedFolder.id = folderId,
    this.selectedFolder.orgId = orgId
  }
})