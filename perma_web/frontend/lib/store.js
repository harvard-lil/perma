import { globalStore } from '../stores/globalStore'

export const getLinksRemainingStatus = (linksRemaining, isNonpaying) => {
    if (linksRemaining !== Infinity) {
        return globalStore.updateLinksRemainingStatus('metered')
    }

    else if (isNonpaying) {
        return globalStore.updateLinksRemainingStatus('unlimited_free')
    }

    return globalStore.updateLinksRemainingStatus('unlimited_paid')
}

export const getUserTypes = (isIndividual, user) => {
    if (isIndividual) {
        return globalStore.updateUserTypes('individual')
    }

    let userTypes = []

    const topLevelFolders = user.top_level_folders
    const isOrgAffiliated = topLevelFolders.some(folder => !!folder.organization)
    const isSponsored = topLevelFolders.some(folder => folder.is_sponsored_root_folder)

    if (isOrgAffiliated) {
        userTypes = userTypes.concat('orgAffiliated')
    }

    if (isSponsored) {
        userTypes = userTypes.concat('sponsored')
    }

    if (userTypes.length) {
        return globalStore.updateUserTypes(userTypes)
    }
}