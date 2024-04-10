import { globalStore } from '../stores/globalStore'

export const getSubscriptionStatus = () => {
    if (subscription_status === 'problem') {
        return globalStore.updateSubscriptionStatus('problem')
    }

    else if (links_remaining !== 'Infinity') {
        return globalStore.updateSubscriptionStatus('metered')
    }

    else if (userNonPaying) {
        return globalStore.updateSubscriptionStatus('free_unlimited')
    }

    return globalStore.updateSubscriptionStatus('paid_unlimited')
}