<script setup>
import { defineProps } from 'vue';

const props = defineProps({
    handleClose: Function
})
</script>

<template>
    <div id="batch-details-wrapper">
        <p id="batch-progress-report"></p>
        <div id="batch-details" aria-describedby="batch-progress-report"></div>
        <div class="form-buttons">
            <button class="btn cancel" @click.prevent="handleClose">Exit</button>
            <a href="#" id="export-csv" class="btn">Export list as
                CSV</a>
        </div>
    </div>
</template>