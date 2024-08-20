<script setup>
import { ref, onMounted } from 'vue'
import * as Spinner from 'spin.js'
import { usePreferredReducedMotion } from '@vueuse/core'

const props = defineProps({
    top: String,
    length: String,
    color: String,
    classList: String,
})

let spinnerRef = ref(null)
let spinner = new Spinner({ lines: 15, length: props.length ? parseInt(props.length) : 2, width: 2, radius: 9, corners: 0, color: props.color ? props.color : '#2D76EE', trail: 50, top: props.top ? props.top : '-20px' })

const motionPreferences = usePreferredReducedMotion()
const showLoader = motionPreferences.value === 'no-preference'

onMounted(() => {
    if (showLoader) {
        spinner.spin(spinnerRef.value)
    }
})
</script>
<template>
    <div v-if="showLoader" ref="spinnerRef" :class="!!props.classList && props.classList"></div>
    <div v-else>Loading</div>
</template>