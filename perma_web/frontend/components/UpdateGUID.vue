<script setup>
import { ref } from 'vue';
import { globalStore } from '../stores/globalStore'

const testGUID = ref('');

const updateGUID = () => {
    triggerError()
    globalStore.updateCaptureGUID(testGUID.value)
};

const clearGUID = () => {
    globalStore.updateCaptureGUID('');
    testGUID.value = ''
};

const triggerError = () => {
    globalStore.updateCapture('captureError')
    globalStore.updateCaptureErrorMessage('testing')
};
</script>

<template>
    <div>
        <p>Current GUID in store: {{ globalStore.captureGUID ? globalStore.captureGUID : "None" }}</p>

        <label for="guid-input">GUID</label>
        <input id="guid-input" v-model="testGUID" />
        <button @click="updateGUID">Update GUID</button>
        <button @click="clearGUID">Clear GUID</button>
        <button @click="triggerError">Trigger Error</button>
    </div>
</template>