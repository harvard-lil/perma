<script setup>
import { computed, ref, nextTick } from 'vue'
import { useGlobalStore } from '../stores/globalStore'
import { onClickOutside } from '@vueuse/core'
import { storeToRefs } from 'pinia'

const globalStore = useGlobalStore()
const { selectedFolder, currentUser } = storeToRefs(globalStore)

const folders = computed(() => {
  if (!currentUser.value) {
    return []
  }
  const folders = [...currentUser.value.top_level_folders];
  folders[0].personal = true;
  // rather than showing the sponsored root folder, show the sponsored folders individually
  if (folders[1].is_sponsored_root_folder) {
    folders.splice(1, 1);
    folders.push(...globalStore.sponsoredFolders);
  }
  return folders
})

const selectContainerRef = ref(null)
const selectButtonRef = ref(null)
const selectListRef = ref(null)
const isSelectExpanded = ref(false)
const selectedOption = computed(() => selectedFolder.value.path.length ? selectedFolder.value.path.join(" > ") : 'Please select a folder')

const getFolderHeader = (folder) => {
  if (folder.registrar) {
    return folder.registrar_name
  } else if (folder.sponsored_by) {
    return "Sponsored Links"
  }

  return "Personal Links"
}

const showLinksRemaining = computed(() => selectedFolder.value.folderId === currentUser.value.top_level_folders[0].id || !!selectedFolder.value.isReadOnly)
const linksRemaining = computed(() => {
  if (selectedFolder.value.isReadOnly) {
    return 0
  } else if (globalStore.linksRemaining === Infinity) {
    return "unlimited"
  }

  return globalStore.linksRemaining
})

// Select Event Handlers
onClickOutside(selectContainerRef, () => {
  if (!isSelectExpanded) {
    return
  }
  isSelectExpanded.value = false
})

const handleSelectToggle = () => {
  isSelectExpanded.value = !isSelectExpanded.value
}

const handleKeyboardSelectToggle = async (e) => {
  const isButton = e.target.matches('button')

  if (!isButton) {
    return
  }

  // close toggle
  if (isSelectExpanded.value) {
    if (e.key === 'ArrowDown') {
      handleFocus(0)
    } else {
      isSelectExpanded.value = false
    }
    return
  }

  // open toggle
  isSelectExpanded.value = true
  await nextTick()
  // focus on current folder
  if (selectedFolder.value.folderId) {
    const selectedItem = selectListRef.value.querySelector(`[data-id="${selectedFolder.value.folderId}"]`);
    if (selectedItem) {
      selectedItem.focus();
      return;
    }
  }
  // default focus on first folder
  handleFocus(0)
}

const handleFocus = (index) => {
  const itemToFocus = selectListRef.value.querySelector(`[data-index="${index}"]`);
  itemToFocus.focus();
};

const handleArrowDown = (e) => {
  const currentIndex = parseInt(e.srcElement.dataset?.index)

  if (!Number.isInteger(currentIndex)) {
    handleFocus(0)
    return
  }

  if (currentIndex < folders.value.length - 1) {
    handleFocus(currentIndex + 1)
  }
}

const handleArrowUp = (e) => {
  const currentIndex = parseInt(e.srcElement.dataset.index)
  if (currentIndex > 0) {
    handleFocus(currentIndex - 1)
  } else if (currentIndex === 0) {
    selectButtonRef.value.focus()
  }
}

const handleClose = () => {
  isSelectExpanded.value = false
  selectButtonRef.value.focus()
}

const handleSelection = (e) => {
  const isSpan = e.target.matches('span')
  const target = isSpan ? e.target.parentElement : e.target
  if (!target.dataset.index) {
    return handleClose()
  }
  const folder = folders.value[target.dataset.index]
  const orgId = folder.organization
  const folderId = folder.sponsored_by ? [folder.parent, folder.id] : folder.id
  globalStore.components.jstree.handleSelectionChange({orgId, folderId})
  handleClose()
}
</script>

<template>
  <div
      id="organization_select_form"
      ref="selectContainerRef"
      class="dropdown dropdown-affil"
      :class="{ 'open': isSelectExpanded }"
  >
    <button
        ref="selectButtonRef"
        @keydown.down.prevent.self="handleKeyboardSelectToggle"
        @keydown.enter.prevent.self="handleKeyboardSelectToggle"
        @keydown.space.prevent="handleKeyboardSelectToggle"
        @click="handleSelectToggle"
        class="dropdown-toggle selector selector-affil needsclick" type="button" aria-haspopup="listbox"
        :aria-expanded="isSelectExpanded" aria-owns="folder-select-list">
      {{ selectedOption }}
      <span v-if="selectedFolder.isPrivate" class="ui-private"></span>
      <span v-if="showLinksRemaining" class="links-remaining">
                {{ linksRemaining }}
            </span>
    </button>
    <ul 
      v-if="isSelectExpanded" 
      ref="selectListRef" 
      @keydown.down="handleArrowDown" 
      @keydown.up="handleArrowUp"
      @click.propagate="handleSelection" 
      @keydown.space="handleSelection"
      @keydown.enter.prevent="handleSelection" 
      @keydown.home.prevent="handleFocus(0)"
      @keydown.end.prevent="handleFocus(folders.length-1)"
      @keydown.esc.stop.prevent="handleClose"
      @keydown.tab="handleClose"
      role="listbox" 
      aria-label="Folder options"
      class="dropdown-menu selector-menu open"
    >
      <template v-for="( folder, index ) in folders ">
        <li v-if="folder.registrar !== folders[index - 1]?.registrar" 
          role="presentation"
          class="dropdown-header" 
          :class="{ 'sponsored': folder.sponsored_by, 'personal-links': folder.personal }"
        >
          {{ getFolderHeader(folder) }}
        </li>
        <li 
          tabindex="-1"
          class="dropdown-item"
          :data-index="index"
          :data-id="folder.id"
          role="option"
          :aria-selected="selectedFolder.folderId === folder.id"
        >
          {{ folder.name }}
          <span v-if="folder.default_to_private"
                class="dropdown-item-supplement ui-private">(Private)</span>
          <span v-if="folder.read_only" class="dropdown-item-supplement links-remaining">0</span>
          <span v-else-if="folder.personal" class="dropdown-item-supplement links-remaining">{{
            globalStore.linksRemaining === Infinity ? 'unlimited' : globalStore.linksRemaining
          }}</span>
          <span v-else class='dropdown-item-supplement links-unlimited'
                :class="{ 'sponsored': folder.sponsored_by }">unlimited</span>
        </li>
      </template>
    </ul>
  </div>
</template>
