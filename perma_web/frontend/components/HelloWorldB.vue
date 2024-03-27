<script setup>
import { globalStore } from '../stores/globalStore'
</script>

<template>
    <p>The current count for component B: {{ globalStore.count }}</p>

    <button @click="globalStore.increment()">
        Increment Counter
    </button>
</template>