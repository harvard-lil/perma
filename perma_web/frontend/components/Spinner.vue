<script setup>
import { ref, onMounted } from 'vue'
import * as Spinner from 'spin.js'

const props = defineProps({
    top: String,
    isDisabled: Boolean
})

let spinnerRef = ref(null)
let spinner = new Spinner({ lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: top })

onMounted(() => {
    spinner.spin(spinnerRef.value)

    if (!props.isDisabled) {
        spinner.stop(spinnerRef.value)
    }
})
</script>
<template>
    <div v-if="!isDisabled" ref="spinnerRef"></div>
    <div v-if="isDisabled">Loading</div>
</template>