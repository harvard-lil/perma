<script setup>
import { ref, onMounted } from 'vue'
// spin.js 4 exports Spinner as a named export only, and moved its animation out
// of JavaScript into these keyframes -- without the stylesheet the spinner
// renders static, with no error raised.
import { Spinner } from 'spin.js'
import 'spin.js/spin.css'
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
  // Name the keyframes rather than passing speed: 0, which reached the same
  // no-motion outcome only by emitting an invalid duration the browser dropped.
  animation: prefersReducedMotion() ? 'none' : 'spinner-line-fade-default',
  speed: 0.5,
  lines: 15,
  width: 2,
  corners: 0,
  radius: Math.max(1, Math.floor(size / 2 - 2)),
  color: '#2D76EE',
  length: 2,
  ...config,
})

onMounted(() => {
  spinner.spin(spinnerRef.value)
})
</script>

<template>
  <div
      ref="spinnerRef"
      :style="{ width: `${size}px`, height: `${size}px`, position: 'relative', margin: 'auto' }"
      aria-label="Loading"
      aria-live="polite"
  ></div>
</template>
