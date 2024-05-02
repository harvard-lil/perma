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

// Debug only
window.addEventListener('dropdown.selectionChange', function (event) {
    console.log('Custom event triggered:', event);
});
</script>

<template>
    <CreateLink />
</template>