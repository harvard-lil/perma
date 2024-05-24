<script setup>
import { computed } from 'vue'
import { globalStore } from '../stores/globalStore'
import FolderCustomSelect from './FolderCustomSelect.vue';
import FolderNativeSelect from './FolderNativeSelect.vue';

const props = defineProps({
    option: String,
    selectLabel: String
})

const folders = computed(() => globalStore.userOrganizations.concat(globalStore.sponsoredFolders))
const personalFolderId = current_user.top_level_folders[0].id
</script>

<template>
    <FolderCustomSelect v-if="props.option === 'customSelect'" :folders :personalFolderId :selectLabel />
    <FolderNativeSelect v-else :folders :personalFolderId :selectLabel />
</template>