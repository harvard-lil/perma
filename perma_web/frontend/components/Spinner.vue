<script setup>
import { ref, onMounted } from 'vue'
import * as Spinner from 'spin.js'
import { prefersReducedMotion } from "../lib/helpers";

const { size, config } = defineProps({
  // spinner will be in a div with this length and width in pixels
  size: {
    type: Number,
    default: 32
  },
  // Configuration object to override default spinner options
  config: {
    type: Object,
    default: () => ({})
  }
})

const spinnerRef = ref(null)
const spinner = new Spinner({
  speed: prefersReducedMotion() ? 0 : 0.5,
  lines: 15,
  width: 2,
  corners: 0, 
  radius: Math.max(1, Math.floor(size / 2 - 2)),
  color: '#2D76EE',
  length: 2,
  ...config,
})

onMounted(() => {spinner.spin(spinnerRef.value)})
</script>

<template>
    <div 
      ref="spinnerRef"
      :style="{ width: `${size}px`, height: `${size}px`, position: 'relative', margin: 'auto' }"
      aria-label="Loading"
      aria-live="polite"
    ></div>
</template>
