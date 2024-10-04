<script setup>
import { useGlobalStore } from '../stores/globalStore'
import { computed, ref, watch } from 'vue'
import { showDevPlayground } from '../lib/consts'

const globalStore = useGlobalStore()

const props = defineProps({
    folders: Array,
    personalFolderId: Number,
    selectLabel: String
})

const handleSelect = (e) => {
    const selectedOption = e.target.options[e.target.selectedIndex];
    const { orgid: orgId, folderid: folderId } = selectedOption.dataset

    if (!folderId) {
        return
    }

    globalStore.additionalSubfolder = false

    const data = { folderId: JSON.parse(folderId), orgId: orgId ? parseInt(orgId) : null };
    if (showDevPlayground) {
        globalStore.jstreeInstance.handleSelectionChange(data)
    } else {
        // Call a custom event that triggers triggerOnWindow function
        const updateSelections = new CustomEvent("dropdown.selectionChange", { detail: { data } });
        window.dispatchEvent(updateSelections);
    }
}

const selectRef = ref('')
const defaultFolderSelection = 'Please select a folder'
const selectedOption = computed(() => !!globalStore.selectedFolder.folderId ? globalStore.selectedFolder.folderId : defaultFolderSelection)

watch(selectedOption, () => {
    if (selectedOption === defaultFolderSelection) {
        return
    }

    const selectIncludesOption = selectRef.value.querySelector(`option[value='${globalStore.selectedFolder.folderId}']`)

    if (!selectIncludesOption) {
        globalStore.additionalSubfolder = true
    }
})
</script>

<template>
    <label id="batch-target" for="batch-target-path" class="label-affil">{{ props.selectLabel }}</label>
    <select ref="selectRef" name="folders" id="batch-capture-select" :selected="selectedOption" :value="selectedOption"
        @change="handleSelect">
        <option value="Please select a folder">Please select a folder</option>
        <template v-if="globalStore.additionalSubfolder">
            <option :value="globalStore.selectedFolder.folderId">
                {{ globalStore.selectedFolder.path.join(" > ") }}
            </option>
        </template>
        <option v-for="folder in props.folders" :key="folder.folderId"
            :value="folder.sponsored_by ? folder.id : folder.shared_folder.id"
            :data-orgid="folder.sponsored_by ? null : folder.id"
            :data-folderid="folder.sponsored_by ? `[${folder.parent},${folder.id}]` : folder.shared_folder.id"
            :disabled="folder.read_only">
            {{ folder.name }}
        </option>
        <option :value="props.personalFolderId" :data-folderid="props.personalFolderId">
            Personal Links
        </option>
    </select>
</template>