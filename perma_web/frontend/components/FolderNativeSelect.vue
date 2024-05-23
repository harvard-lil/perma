<script setup>
import { globalStore } from '../stores/globalStore'
import { computed, ref, watch } from 'vue'

const props = defineProps({
    folders: Array,
    personalFolderId: Number
})

const handleSelect = (e) => {
    const selectedOption = e.target.options[e.target.selectedIndex];
    const { orgid: orgId, folderid: folderId } = selectedOption.dataset

    if (!folderId) {
        return
    }

    globalStore.updateAdditionalSubfolder(false)

    // Call a custom event that triggers triggerOnWindow function
    const updateSelections = new CustomEvent("dropdown.selectionChange", { detail: { data: { folderId: JSON.parse(folderId), orgId: orgId ? parseInt(orgId) : null } } });
    window.dispatchEvent(updateSelections);
}

const selectRef = ref('')
const selectedOption = computed(() => globalStore.selectedFolder ? globalStore.selectedFolder.folderId : 'Please select a folder')

watch(selectedOption, () => {
    const selectIncludesOption = selectRef.value.querySelector(`option[value='${globalStore.selectedFolder.folderId}']`);

    if (!selectIncludesOption) {
        globalStore.updateAdditionalSubfolder(true)
    }
})
</script>

<template>
    <label id="batch-target" for="batch-target-path" class="label-affil">These Perma Links will be affiliated
        with</label>
    <select ref="selectRef" name="pets" id="batch-capture-select" :selected="selectedOption" :value="selectedOption"
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