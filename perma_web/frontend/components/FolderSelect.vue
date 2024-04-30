<script setup>
import { computed } from 'vue'
import { globalStore } from '../stores/globalStore'

const personalFolderNames = ['Empty root folder', 'Personal Links']
const showLinkCount = computed(() => personalFolderNames.includes(globalStore.selectedFolder.path[0]) || !!globalStore.selectedFolder.isReadOnly)

const folderLabel = computed(() => globalStore.selectedFolder.path.length ? globalStore.selectedFolder.path.join(" > ") : 'Please select a folder')

const selectedLinkCount = computed(() => {
    if (globalStore.selectedFolder.isReadOnly) {
        return 0
    }

    else if (globalStore.linksRemaining === Infinity) {
        return "unlimited"
    }

    return globalStore.linksRemaining
})

</script>

<template>
    <!-- Just a label for now -->
    <div id="organization_select_form">
        <span class="label-affil">This Perma Link will be affiliated with</span>
        <div class="dropdown dropdown-affil">
            <button class="dropdown-toggle selector selector-affil needsclick" type="button" id="dropdownMenu1"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                {{ folderLabel }}
                <span v-if="globalStore.selectedFolder.isPrivate" class="ui-private"></span>
                <span v-if="showLinkCount" class="links-remaining">
                    {{ selectedLinkCount }}
                </span>
            </button>
            <ul class="dropdown-menu selector-menu" aria-labelledby="dropdownMenu1" id="organization_select">
            </ul>
        </div>
    </div>
</template>