<script setup>
import { computed, ref } from 'vue'
import { globalStore } from '../stores/globalStore'

const selectLabel = computed(() => globalStore.selectedFolder.path.length ? globalStore.selectedFolder.path.join(" > ") : 'Please select a folder')
const isSelectExpanded = ref(false)

const folders = computed(() => globalStore.organizationFolders.concat(globalStore.sponsoredFolders))

// Only required for admin users locally
const personalFolderNames = ['Empty root folder', 'Personal Links']

const getFolderHeader = (folder) => {
    if (folder.registrar) {
        return folder.registrar
    }

    if (folder.sponsored_by) {
        return "Sponsored Links"
    }

    return "Personal Links"
}

const showLinksRemaining = computed(() => personalFolderNames.includes(globalStore.selectedFolder.path[0]) || !!globalStore.selectedFolder.isReadOnly)
const linksRemaining = computed(() => {
    if (globalStore.selectedFolder.isReadOnly) {
        return 0
    }

    else if (globalStore.linksRemaining === Infinity) {
        return "unlimited"
    }

    return globalStore.linksRemaining
})

const handleSelectToggle = () => {
    isSelectExpanded.value = !isSelectExpanded.value
}

</script>

<template>
    <div id="organization_select_form">
        <span class="label-affil">This Perma Link will be affiliated with</span>
        <div @click="handleSelectToggle" class="dropdown dropdown-affil" :class="{ 'open': isSelectExpanded }">
            <button class="dropdown-toggle selector selector-affil needsclick" type="button" id="dropdownMenu1"
                aria-haspopup="true" :aria-expanded="isSelectExpanded">
                {{ selectLabel }}
                <span v-if="globalStore.selectedFolder.isPrivate" class="ui-private"></span>
                <span v-if="showLinksRemaining" class="links-remaining">
                    {{ linksRemaining }}
                </span>
            </button>
            <!-- <div v-if="isSelectExpanded" class="dropdown-backdrop"></div> -->
            <ul class="dropdown-menu selector-menu" :class="{ 'open': isSelectExpanded }"
                aria-labelledby="dropdownMenu1">
                <template v-for="(  folder, index  ) in   folders  ">
                    <li class="dropdown-header" :class="{ 'sponsored': folder.sponsored_by }"
                        v-if="folder.registrar !== folders[index - 1]?.registrar">
                        {{ getFolderHeader(folder) }}
                    </li>
                    <li class="dropdown-item">
                        {{ folder.name }}
                        <span v-if="folder?.default_to_private" class="ui-private">(Private)</span>

                        <span v-if="folder.read_only" class="links-remaining">0</span>
                        <span v-else class='links-unlimited'
                            :class="{ 'sponsored': folder.sponsored_by }">unlimited</span>
                    </li>
                </template>
                <li class="dropdown-header personal">Personal Links</li>
                <li class="dropdown-item personal-links">
                    Personal Links <span class="links-remaining">{{ globalStore.linksRemaining === Infinity ?
            'unlimited' :
                        globalStore.linksRemaining }}</span>
                </li>
            </ul>
        </div>
    </div>
</template>