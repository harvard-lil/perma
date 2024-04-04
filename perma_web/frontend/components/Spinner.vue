<script setup>
import { ref, onMounted } from 'vue'
import * as Spinner from 'spin.js'

let spinnerRef = ref(null)
let spinner = new Spinner({ lines: 15, length: 2, width: 2, radius: 9, corners: 0, color: '#2D76EE', trail: 50, top: '-20px' })

onMounted(() => {
    spinner.spin(spinnerRef.value)
})

</script>
<template>
    <div ref="spinnerRef"></div>
</template>