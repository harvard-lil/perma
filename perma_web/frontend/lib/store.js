import { globalStore } from '../stores/globalStore'

export const getLinksRemainingStatus = (links_remaining, is_nonpaying) => {
    if (links_remaining !== 'Infinity') {
        return globalStore.updateLinksRemainingStatus('metered')
    }

    else if (is_nonpaying) {
        return globalStore.updateLinksRemainingStatus('unlimited_free')
    }

    return globalStore.updateLinksRemainingStatus('unlimited_paid')
}

export const getUserTypes = (is_individual) => {
    let types = []

    if (is_individual === "True") {
        types = types.concat('individual')
    }

    if (types.length) {
        return globalStore.updateUserTypes(types)
    }
}