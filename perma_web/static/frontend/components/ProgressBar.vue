<script setup>

const props = defineProps({
  progress: String,
})

</script>
<template>
  <div position="relative" style="width: 100%; height: 0">
    <div class="progress" style="width: 100%; height: 0.6em; position: absolute; margin-bottom: 0">
      <div class="progress-bar" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100"
           style="background-color: #2D76EE; width: 90%"
           :style="{ 'background-color': '#2D76EE', width: progress }">
        <span class="sr-only">{{ progress }} Complete</span>
      </div>
    </div>
  </div>
</template>