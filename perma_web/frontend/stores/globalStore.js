import { defineStore } from 'pinia'
import { fetchDataOrError } from '../lib/data'

export const useGlobalStore = defineStore('global', {
  state: () => ({
    fetchErrorMessage: '',
    linkCreationAllowed: false,
    linksRemaining: Infinity,
    linksRemainingStatus: '',
    userTypes: [],
    selectedFolder: {
      path: [],
      folderId: '', 
      orgId: '',
      sponsorId: '',
      isPrivate: false,
      isReadOnly: false,
      isOutOfLinks: false,
    },
    userOrganizations: [],
    sponsoredFolders: [],
    additionalSubfolder: false,
    subscriptionStatus: '',
    maxSize: 0,
    components: {
      createLink: null,
      batchDialog: null,
      jstree: null,
      linkList: null,
    },
  }),
  actions: {
    setLinksRemainingFromGlobals(linksRemaining, isNonpaying) {
      this.linksRemaining = linksRemaining;
      if (linksRemaining !== Infinity)
        this.linksRemainingStatus = 'metered';
      else if (isNonpaying)
        this.linksRemainingStatus = 'unlimited_free';
      else
        this.linksRemainingStatus = 'unlimited_paid';
    },
    setUserTypesFromGlobals(isIndividual, isOrganizationUser, isRegistrarUser, isSponsoredUser, isStaff) {
      if (isIndividual)
        this.userTypes = ['individual'];
      else {
        let userTypes = [];
        if (isOrganizationUser || isRegistrarUser)
          userTypes = userTypes.concat('orgAffiliated');
        if (isSponsoredUser)
          userTypes = userTypes.concat('sponsored');
        if (isStaff)
          userTypes = userTypes.concat('staff');
        if (userTypes.length)
          this.userTypes = userTypes;
      }

      if (this.userTypes.includes('orgAffiliated') || this.userTypes.includes('staff')) {
        this.setFromAPI('userOrganizations', fetchDataOrError('/organizations', {
          params: {
            limit: 300,
            order_by: 'registrar, name',
          }
        }))
      }
      if (this.userTypes.includes('sponsored')) {
        this.setFromAPI('sponsoredFolders', fetchDataOrError(`/folders/${current_user.top_level_folders[1].id}/folders/`))
    }
    },
    async setFromAPI(attribute, fetchPromise) {
      const { data, error } = await fetchPromise

      if (error) {
          this.fetchErrorMessage = error
      }

      this[attribute] = data.objects
    },
  },
})
