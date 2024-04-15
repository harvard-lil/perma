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

export const getUserTypes = (isIndividual) => {
    let types = []

    if (isIndividual) {
        types = types.concat('individual')
    }

    if (types.length) {
        return globalStore.updateUserTypes(types)
    }
}