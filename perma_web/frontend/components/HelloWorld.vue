<script setup>
import { ref } from 'vue'
const message = ref('Hello World!')
</script>

<template>
    <p class="hello">{{ message }}</p>
</template>