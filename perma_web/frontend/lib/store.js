import { globalStore } from '../stores/globalStore'

export const getSubscriptionStatus = (subscription_status) => {
    if (subscription_status === 'problem') {
        return globalStore.updateSubscriptionStatus('problem')
    }

    else if (links_remaining !== 'Infinity') {
        return globalStore.updateSubscriptionStatus('metered')
    }

    else if (userNonPaying) {
        return globalStore.updateSubscriptionStatus('unlimited_free')
    }

    return globalStore.updateSubscriptionStatus('unlimited_paid')
}

export const getUserTypes = (is_individual) => {
    let types = []

    if (is_individual) {
        types = types.concat('individual')
    }

    if (types.length) {
        return globalStore.updateUserTypes(types)
    }
}