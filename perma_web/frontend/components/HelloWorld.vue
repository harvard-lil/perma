<script setup>
import { globalStore } from '../stores/globalStore'

</script>

<template>
    <p>The current count for component A: {{ globalStore.count }}</p>

    <button @click="globalStore.increment()">
        Increment Counter
    </button>
</template>