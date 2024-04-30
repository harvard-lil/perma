<script setup>
import CreateLink from './CreateLink.vue';
import { onBeforeMount, watchEffect } from 'vue'
import { getLinksRemainingStatus, getUserTypes, getOrganizationFolders, getSponsoredFolders } from '../lib/store'
import { globalStore } from '../stores/globalStore';

onBeforeMount(() => {
    globalStore.updateLinksRemaining(links_remaining)
    getLinksRemainingStatus(links_remaining, is_nonpaying)
    getUserTypes(is_individual, current_user)
})

watchEffect(() => {
    if (globalStore.userTypes.includes('orgAffiliated')) {
        getOrganizationFolders()
    }

    if (globalStore.userTypes.includes('sponsored')) {
        getSponsoredFolders()
    }
})
</script>

<template>
    <CreateLink />
</template>