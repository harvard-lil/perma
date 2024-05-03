<script setup>
import { computed, ref } from 'vue'
import { globalStore } from '../stores/globalStore'
import { onClickOutside } from '@vueuse/core'
import { triggerOnWindow } from '../../static/js/helpers/general.helpers'

const selectContainerRef = ref(null)
const selectButtonRef = ref(null)
const isSelectExpanded = ref(false)
const selectLabel = computed(() => globalStore.selectedFolder.path.length ? globalStore.selectedFolder.path.join(" > ") : 'Please select a folder')

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

const handleSelection = (e) => {
    const isSpan = e.target.matches('span')
    const target = isSpan ? e.target.parentElement : e.target

    const { orgid, folderid } = target.dataset

    if (!folderid) {
        return handleClose()
    }

    let folderId = JSON.parse(folderid)
    let orgId = null

    // Organization folder selections
    if (orgid) {
        orgId = parseInt(orgid)
    }

    // Sponsored folder selections
    if (Array.isArray(folderId)) {
        folderId = folderId[1]
    }

    // Debug only
    // Should output 
    // ƒ triggerOnWindow(message, data) {
    //     $(window).trigger(message, data);
    // }
    console.log(triggerOnWindow)

    // Calls triggerOnWindow function, but doesn't appear to fire Jquery-specific trigger event
    triggerOnWindow("dropdown.selectionChange", {
        folderId,
        orgId
    })

    // Call a custom event that triggers triggerOnWindow function
    const updateSelections = new CustomEvent("dropdown.selectionChange", { detail: { data: { folderId, orgId } } });
    window.dispatchEvent(updateSelections);

    handleClose()
}

</script>

<template>
    <div id="organization_select_form">
        <span class="label-affil">This Perma Link will be affiliated with</span>
        <div ref="selectContainerRef" @keydown.home.prevent="handleFocus(0)"
            @keydown.end.prevent="handleFocus(folders.length)" @keydown.esc="handleClose" @keydown.tab="handleClose"
            class="dropdown dropdown-affil" :class="{ 'open': isSelectExpanded }">
            <button ref="selectButtonRef" @keydown.down.prevent="handleFocus(0)" @click="handleSelectToggle"
                class="dropdown-toggle selector selector-affil needsclick" type="button" id="dropdownMenu1"
                aria-haspopup="listbox" :aria-expanded="isSelectExpanded">
                {{ selectLabel }}
                <span v-if="globalStore.selectedFolder.isPrivate" class="ui-private"></span>
                <span v-if="showLinksRemaining" class="links-remaining">
                    {{ linksRemaining }}
                </span>
            </button>
            <ul ref="selectListRef" v-if="isSelectExpanded" @keydown.down="handleArrowDown" @keydown.up="handleArrowUp"
                @click.propagate="handleSelection" @keydown.space="handleSelection"
                @keydown.enter.prevent="handleSelection" role="listbox" aria-label="Folder options"
                class="dropdown-menu selector-menu" :class="{ 'open': isSelectExpanded }">
                <template v-for="(folder, index) in folders">
                    <li v-if="folder.registrar !== folders[index - 1]?.registrar" role="presentation"
                        class="dropdown-header" :class="{ 'sponsored': folder.sponsored_by }">
                        {{ getFolderHeader(folder) }}
                    </li>
                    <li tabindex="-1" class="dropdown-item" role="option"
                        :aria-selected="globalStore.selectedFolder.orgId === folder.id || globalStore.selectedFolder.path[1] === folder.name"
                        :data-index="index" :data-orgid="folder.sponsored_by ? null : folder.id"
                        :data-folderid="folder.sponsored_by ? `[${folder.parent}, ${folder.id}]` : folder.shared_folder.id">
                        {{ folder.name }}
                        <span v-if="folder?.default_to_private" class="ui-private">(Private)</span>
                        <span v-if="folder.read_only" class="links-remaining">0</span>
                        <span v-else class='links-unlimited'
                            :class="{ 'sponsored': folder.sponsored_by }">unlimited</span>
                    </li>
                </template>
                <li class="dropdown-header personal" role="presentation" aria-hidden="true">Personal Links</li>
                <li tabindex="-1" class="dropdown-item personal-links" role="option"
                    :aria-selected="personalFolderNames.includes(globalStore.selectedFolder.path[0])"
                    :data-index="folders.length" :data-folderid="personalFolderId">Personal Links <span
                        class="links-remaining">{{ globalStore.linksRemaining ===
                Infinity ?
                'unlimited' :
                        globalStore.linksRemaining }}</span>
                </li>
            </ul>
        </div>
    </div>
</template>