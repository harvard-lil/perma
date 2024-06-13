import { globalStore } from '../stores/globalStore'
import { useFetch } from '../lib/data'
import { computed } from 'vue'

export const getLinksRemainingStatus = (linksRemaining, isNonpaying) => {
    if (linksRemaining !== Infinity) {
        return globalStore.updateLinksRemainingStatus('metered')
    }

    else if (isNonpaying) {
        return globalStore.updateLinksRemainingStatus('unlimited_free')
    }

    return globalStore.updateLinksRemainingStatus('unlimited_paid')
}

export const getUserTypes = (isIndividual, isOrganizationUser, isRegistrarUser, isSponsoredUser, isStaff) => {
    if (isIndividual) {
        return globalStore.updateUserTypes('individual')
    }

    let userTypes = []

    if (isOrganizationUser || isRegistrarUser) {
        userTypes = userTypes.concat('orgAffiliated')
    }

    if (isSponsoredUser) {
        userTypes = userTypes.concat('sponsored')
    }

    if (isStaff) {
        userTypes = userTypes.concat('staff')
    }

    if (userTypes.length) {
        return globalStore.updateUserTypes(userTypes)
    }
}

export const getUserOrganizations = async () => {
    const { data, error, errorMessage } = await useFetch('/api/v1/organizations', {
        limit: 300,
        order_by: 'registrar, name'
    })

    if (error) {
        globalStore.updateFetchErrorMessage(errorMessage)
    }

    if (data?.value?.objects.length) {
        globalStore.updateUserOrganizations(data.value.objects)
    }
}

export const getSponsoredFolders = async () => {
    const { data, error, errorMessage } = await useFetch(`/api/v1/folders/${current_user.top_level_folders[1].id}/folders/`)

    if (error) {
        globalStore.updateFetchErrorMessage(errorMessage)
    }

    if (data?.value?.objects.length) {
        globalStore.updateSponsoredFolders(data.value.objects)
    }
}

export const isStaff = computed(() => { return globalStore.userTypes.includes('staff') })
