<script setup>
import CreateLink from './CreateLink.vue';
import Toast from './Toast.vue';
import LinkBrowser from './LinkBrowser.vue'
import { onBeforeMount } from 'vue'
import { useGlobalStore } from '../stores/globalStore';
import { showDevPlayground } from '../lib/consts'

const globalStore = useGlobalStore()

onBeforeMount(() => {
    // handle globals set by Django
    globalStore.setLinksRemainingFromGlobals(links_remaining, is_nonpaying)
    globalStore.setUserTypesFromGlobals(is_individual, is_organization_user, is_registrar_user, is_sponsored_user, is_staff)
    globalStore.subscriptionStatus = subscription_status;
})
</script>

<template>
    <Toast />
    <CreateLink />
    <LinkBrowser v-if="showDevPlayground" />
</template>