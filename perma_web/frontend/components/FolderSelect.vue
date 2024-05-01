<script setup>
import { computed, ref } from 'vue'
import { globalStore } from '../stores/globalStore'
import { onClickOutside } from '@vueuse/core'

const selectLabel = computed(() => globalStore.selectedFolder.path.length ? globalStore.selectedFolder.path.join(" > ") : 'Please select a folder')
const isSelectExpanded = ref(false)

const folders = computed(() => globalStore.organizationFolders.concat(globalStore.sponsoredFolders))

// Folder names are only required for admin users locally
const personalFolderNames = ['Empty root folder', 'Personal Links']
const personalFolderId = current_user.top_level_folders[0].id

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

// Select Event Handlers
const selectContainerRef = ref(null)
const selectButtonRef = ref(null)

onClickOutside(selectContainerRef, () => {
    if (!isSelectExpanded) { return }
    isSelectExpanded.value = false
})

const handleFocus = (index) => {
    const itemToFocus = document.querySelector(`[data-index="${index}"]`);
    itemToFocus.focus();
};

const handleArrowDown = (e) => {
    const currentIndex = parseInt(e.srcElement.dataset?.index)

    if (!currentIndex) {
        handleFocus(0)
    }

    if (currentIndex < folders.value.length) {
        handleFocus(currentIndex + 1)
    }
}

const handleArrowUp = (e) => {
    const currentIndex = parseInt(e.srcElement.dataset.index)
    if (currentIndex > 0) {
        handleFocus(currentIndex - 1)
    }
}

const handleClose = () => {
    isSelectExpanded.value = false
    selectButtonRef.value.focus()
}
</script>

<template>
    <div id="organization_select_form">
        <span class="label-affil">This Perma Link will be affiliated with</span>
        <div ref="selectContainerRef" @keydown.home="handleFocus(0)" @keydown.esc="handleClose"
            @click="handleSelectToggle" class="dropdown dropdown-affil" :class="{ 'open': isSelectExpanded }">
            <button ref="selectButtonRef" @keydown.down.prevent="handleFocus(0)"
                class="dropdown-toggle selector selector-affil needsclick" type="button" id="dropdownMenu1"
                aria-haspopup="true" :aria-expanded="isSelectExpanded">
                {{ selectLabel }}
                <span v-if="globalStore.selectedFolder.isPrivate" class="ui-private"></span>
                <span v-if="showLinksRemaining" class="links-remaining">
                    {{ linksRemaining }}
                </span>
            </button>
            <ul @keydown.down="handleArrowDown" @keydown.up="handleArrowUp" role="listbox" aria-label="Folder options"
                class="dropdown-menu selector-menu" :class="{ 'open': isSelectExpanded }">
                <template v-for="(folder, index) in folders">
                    <li v-if="folder.registrar !== folders[index - 1]?.registrar" class="dropdown-header"
                        :class="{ 'sponsored': folder.sponsored_by }">
                        {{ getFolderHeader(folder) }}
                    </li>
                    <li tabindex="-1" class="dropdown-item" role="option" aria-selected="false" :data-index="index"
                        :data-orgid="folder.sponsored_by ? null : folder.id"
                        :data-folderid="folder.sponsored_by ? `[${folder.parent}, ${folder.id}]` : folder.shared_folder.id">
                        {{ folder.name }}
                        <span v-if="folder?.default_to_private" class="ui-private">(Private)</span>
                        <span v-if="folder.read_only" class="links-remaining">0</span>
                        <span v-else class='links-unlimited'
                            :class="{ 'sponsored': folder.sponsored_by }">unlimited</span>
                    </li>
                </template>
                <li class="dropdown-header personal">Personal Links</li>
                <li tabindex="-1" class="dropdown-item personal-links" role="option" aria-selected="false"
                    :data-index="folders.length" :data-folderid="personalFolderId">
                    Personal Links <span class="links-remaining">{{ globalStore.linksRemaining === Infinity ?
                'unlimited' :
                globalStore.linksRemaining }}</span>
                </li>
            </ul>
        </div>
    </div>
</template>