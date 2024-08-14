<script setup>
  import SectionHeading from './SectionHeading.vue'
  import IconButton from './IconButton.vue'
</script>

<template>
  <div class="container cont-fixed manage-links">
    <div class="row">
      <div class="col-md-3">
        <SectionHeading name="Link Batch History">
          <template #iconButton>
            <IconButton
              icon="chevron-down"
              iconFamily="none"
              :handleClick="() => {console.log('Expand Link Batch History');}"
            />
          </template>
        </SectionHeading>
        <SectionHeading name="Folders">
          <template #iconButton>
            <IconButton
              icon="plus"
              name="New Folder"
              :handleClick="() => {console.log('New Folder');}"

            />
            <IconButton
              icon="edit"
              name="Rename Selected Folder"
              :handleClick="() => {console.log('Rename Selected Folder');}"
            />
            <IconButton
              icon="trash"
              name="Delete Selected Folder"
              :handleClick="() => {console.log('Delete Selected Folder');}"
            />
          </template>
        </SectionHeading>
      </div>
      <div class="col-md-9">
        <SectionHeading name="Another Journal Links" icon="organization">
          <template #iconButton>
            <IconButton
              icon="download-alt"
              name="Export Links"
              :handleClick="() => {console.log('Export Links');}"

            />
          </template>
        </SectionHeading>
      </div>
    </div>
  </div>
</template>
