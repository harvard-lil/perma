<script setup>
import CreateLink from './CreateLink.vue';
import { onBeforeMount } from 'vue'
import { getLinksRemainingStatus, getUserTypes } from '../lib/store'

onBeforeMount(() => {
    getLinksRemainingStatus(links_remaining, is_nonpaying)
    getUserTypes(is_individual)
})
</script>

<template>
    <CreateLink />
</template>