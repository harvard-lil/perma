<script setup>
import { globalStore } from '../stores/globalStore'
</script>

<template>
    The current count for component B: {{ globalStore.count }}

    <button @click="globalStore.increment()">
        Increment Counter
    </button>
</template>