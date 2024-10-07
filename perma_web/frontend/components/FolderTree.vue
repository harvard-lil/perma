<script setup>
import { ref, onMounted } from 'vue';
import { useGlobalStore } from '../stores/globalStore';
import JSTree from './JSTree.vue';

/*
   TODO: We are migrating from an old jstree jquery structure to Vue. Conceptually, this file is for all of our
   business logic, and the <JSTree /> component is a third party component that could be replaced with a different
    tree component in the future (even though in this case we wrote it as a wrapper for jstree). Eventually anything
    "business logic" should be done here, and use a clean API to interact with <JSTree />.
 */


const globalStore = useGlobalStore();
const jstreeRef = ref(null);

onMounted(() => {
  globalStore.components.jstree = jstreeRef.value;
});

const onNodeSelect = (node) => {
  updateSelectedFolder(node);
};

const updateSelectedFolder = (node) => {
  globalStore.selectedFolder = {
    path: jstreeRef.value.getFolderTree().get_path(node) || [],
    folderId: node.data.folder_id || '',
    orgId: node.data.organization_id || '',
    sponsorId: node.data.sponsor_id || '',
    isPrivate: node.data.is_private || false,
    isReadOnly: node.data.read_only || false,
    isOutOfLinks: node.data.out_of_links || false,
  };
};
</script>

<template>
  <div>
    <div class="panel-heading">
      Folders
      <span class="buttons">
        <a href="#" class="pull-right delete-folder icon-trash" aria-label="Delete Selected Folder" title="Delete Selected Folder" @click.prevent="deleteFolder"></a>
        <a href="#" class="pull-right edit-folder icon-edit" aria-label="Rename Selected Folder" title="Rename Selected Folder" @click.prevent="editFolder"></a>
        <a href="#" class="pull-right new-folder icon-plus" aria-label="New Folder" title="New Folder" @click.prevent="newFolder"></a>
      </span>
    </div>
    <JSTree
      ref="jstreeRef"
      @nodeSelect="onNodeSelect"
    />
  </div>
</template>