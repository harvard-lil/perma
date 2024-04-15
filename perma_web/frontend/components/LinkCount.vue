<script setup>
import { globalStore } from '../stores/globalStore'

const subscriptionLink = "/settings/usage-plan/"
const linkRenewalPeriod = links_remaining_period === 'monthly' ? ' this month.' : links_remaining_period === 'annually' ? ' this year.' : '.'

const getLinksRemainingText = () => {
    switch (globalStore.linksRemainingStatus) {
        case 'unlimited_paid':
            return `Your <a href=${subscriptionLink}>subscription</a> includes the creation of unlimited Perma Links.</a>`

        case 'unlimited_free':
            return `Your account has been upgraded to unlimited personal Perma Links.`

        case 'metered':
        default:
            return `You have <span class="links-remaining">${links_remaining}</span> remaining Perma Links${linkRenewalPeriod}</span><br />`
    }
}
</script>

<template>
    <p class="links-remaining-message">
        <span v-if="subscription_status === 'problem'">
            Your subscription is on hold due to a <a :href="subscriptionLink">problem with
                your credit card</a>.<br>
        </span>
        <span v-html="getLinksRemainingText()"></span>
        <a v-if="globalStore.linksRemainingStatus === 'metered' && subscription_status !== 'problem'"
            :href="subscriptionLink">View your subscription details or get more Perma Links.</a>
    </p>
</template>