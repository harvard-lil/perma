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

  fetchErrorMessage: '',
  updateFetchErrorMessage(message) {
    this.fetchErrorMessage = message
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
  },

  organizationFolders: [],
  updateOrganizationFolders(orgFolders) {
    console.log(orgFolders)
    this.organizationFolders = orgFolders
  },

  organizationFoldersById: {},
  updateOrganizationFoldersById(orgFoldersById) {
    console.log(orgFoldersById)
    this.organizationFoldersById = orgFoldersById
  }, 

  sponsoredFolders: [], 
  updateSponsoredFolders(sponsoredFolders) {
    this.sponsoredFolders = sponsoredFolders
  }
})