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
  const {
    organization_id: orgId, 
    sponsor_id: sponsorId, 
    folder_id: folderId, 
    read_only: isReadOnly
  } = node.data;
  const org = orgId ? globalStore.userOrganizations.find(org => org.id === orgId) : null;
  const isOutOfLinks = !isReadOnly && !sponsorId && !orgId && !globalStore.linkCreationAllowed;
  globalStore.selectedFolder = {
    folderId,
    orgId,
    sponsorId,
    isReadOnly,
    isOutOfLinks,
    path: jstreeRef.value.getFolderTree().get_path(node) || [],
    isPrivate: org?.default_to_private || false,
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