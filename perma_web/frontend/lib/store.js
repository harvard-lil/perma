import { globalStore } from '../stores/globalStore'
import { useFetch } from '../lib/data'

export const getLinksRemainingStatus = (linksRemaining, isNonpaying) => {
    if (linksRemaining !== Infinity) {
        return globalStore.updateLinksRemainingStatus('metered')
    }

    else if (isNonpaying) {
        return globalStore.updateLinksRemainingStatus('unlimited_free')
    }

    return globalStore.updateLinksRemainingStatus('unlimited_paid')
}

export const getUserTypes = (isIndividual, isOrganizationUser, isSponsoredUser) => {
    if (isIndividual) {
        return globalStore.updateUserTypes('individual')
    }

    let userTypes = []

    if (isOrganizationUser) {
        userTypes = userTypes.concat('orgAffiliated')
    }

    if (isSponsoredUser) {
        userTypes = userTypes.concat('sponsored')
    }

    if (userTypes.length) {
        return globalStore.updateUserTypes(userTypes)
    }
}

export const getOrganizationFolders = async () => {
    const { data, error, errorMessage } = await useFetch('/api/v1/organizations', {
        limit: 300,
        order_by: 'registrar, name'
    })

    if (error) {
        globalStore.updateFetchErrorMessage(errorMessage)
    }

    if (data?.value?.objects.length) {
        const organizationsById = data.value.objects.reduce((acc, currentValue) => {
            return { ...acc, [currentValue.id]: currentValue }
        }, {})
        globalStore.updateOrganizationFolders(data.value.objects)
        globalStore.updateOrganizationFoldersById(organizationsById)
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