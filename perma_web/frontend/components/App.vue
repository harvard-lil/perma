<script setup>
import CreateLink from './CreateLink.vue';
import { onBeforeMount } from 'vue'
import { getSubscriptionStatus, getUserTypes } from '../lib/store'

onBeforeMount(() => {
    getSubscriptionStatus(subscription_status)
    getUserTypes(is_individual)
})
</script>

<template>
    <CreateLink />
</template>