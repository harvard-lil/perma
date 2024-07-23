import { reactive } from 'vue'

export const globalStore = reactive({
  captureStatus: 'ready',
  updateCapture(state) {
    this.captureStatus = state
  },

  captureGUID: '', 
  updateCaptureGUID(value) {
    this.captureGUID = value
  },

  captureErrorMessage: '',
  updateCaptureErrorMessage(message) {
    this.captureErrorMessage = message
  },

  batchCaptureStatus: 'ready',
  updateBatchCapture(state) {
    this.batchCaptureStatus = state
  },

  batchCaptureErrorMessage: '',
  updateBatchCaptureErrorMessage(message) {
    this.batchCaptureErrorMessage = message
  },

  fetchErrorMessage: '',
  updateFetchErrorMessage(message) {
    this.fetchErrorMessage = message
  },

  linksRemaining: '',
  updateLinksRemaining(links) {
    this.linksRemaining = links
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
    path: [],
    folderId: '', 
    orgId: '',
    sponsorId: '',
    isPrivate: false,
    isReadOnly: false,
    isOutOfLinks: false,
  },

  updateFolderSelection(selection) {
    this.selectedFolder = selection
  },

  userOrganizations: [],
  updateUserOrganizations(orgs) {
    this.userOrganizations = orgs
  },

  sponsoredFolders: [], 
  updateSponsoredFolders(sponsoredFolders) {
    this.sponsoredFolders = sponsoredFolders
  },

  additionalSubfolder: false,
  updateAdditionalSubfolder(value) {
    this.additionalSubfolder = value
  },
})