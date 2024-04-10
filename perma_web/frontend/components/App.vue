<script setup>
import CreateLink from './CreateLink.vue';
import { onBeforeMount } from 'vue'
import { getSubscriptionStatus } from '../lib/subscriptions'

onBeforeMount(() => {
    getSubscriptionStatus()
})
</script>

<template>
    <CreateLink />
</template>