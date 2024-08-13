<script setup>
</script>

<template>
  <div class="container cont-fixed manage-links">
    <div class="row">
      <div class="col-md-3">
        <slot name="leftColumn"></slot>
      </div>
      <div class="col-md-9">
        <slot name="rightColumn"></slot>
      </div>
    </div>
  </div>
</template>
