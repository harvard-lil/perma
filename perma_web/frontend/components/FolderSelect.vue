<script setup>
import { computed } from 'vue'
import { globalStore } from '../stores/globalStore'

const selectedFolder = computed(() => {
    globalStore.organizationFoldersById[
        globalStore.selectedFolder.orgId]
})

</script>

<template>
    {{ selectedFolder }}
    <!-- Debug only -->
    <h2>Selected Folder Ids</h2>
    {{ globalStore.selectedFolder }}

    <!-- Debug only -->
    <h2>Sponsored Folders</h2>
    {{ globalStore.sponsoredFolders }}

    <!-- Debug only -->
    <h2>Organization Folders</h2>
    {{ globalStore.organizationFolders }}

    <!-- Placeholder for now -->
    <div id="organization_select_form">
        <span class="label-affil">This Perma Link will be affiliated with</span>
        <div class="dropdown dropdown-affil">
            <button class="dropdown-toggle selector selector-affil needsclick" type="button" id="dropdownMenu1"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                Please select a folder
            </button>
            <ul class="dropdown-menu selector-menu" aria-labelledby="dropdownMenu1" id="organization_select"></ul>
        </div>
    </div>
</template>