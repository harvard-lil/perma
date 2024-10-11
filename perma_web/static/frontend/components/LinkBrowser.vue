<script setup>
import LinkBatchHistory from './LinkBatchHistory.vue';
import FolderTree from './FolderTree.vue';
import LinkList from './LinkList.vue';
</script>

<template>
  <div class="container cont-fixed manage-links">
    <div class="row">
      <div class="col-md-3 col-folders">
        <LinkBatchHistory/>
        <FolderTree/>
      </div>
      <div class="col-md-9 col-links">
        <LinkList/>
      </div>
    </div>
  </div>
</template>