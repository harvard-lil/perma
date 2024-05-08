<script setup>
import CreateLink from './CreateLink.vue';
import { onBeforeMount, watchEffect } from 'vue'
import { getLinksRemainingStatus, getUserTypes, getUserOrganizations, getSponsoredFolders } from '../lib/store'
import { globalStore } from '../stores/globalStore';

onBeforeMount(() => {
    globalStore.updateLinksRemaining(links_remaining)
    getLinksRemainingStatus(links_remaining, is_nonpaying)
    getUserTypes(is_individual, is_organization_user, is_registrar_user, is_sponsored_user, is_staff)
})

watchEffect(() => {
    if (globalStore.userTypes.includes('orgAffiliated') || globalStore.userTypes.includes('staff')) {
        getUserOrganizations()
    }

    if (globalStore.userTypes.includes('sponsored')) {
        getSponsoredFolders()
    }
})

</script>

<template>
    <CreateLink />
</template>