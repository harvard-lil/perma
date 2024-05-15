<script setup>
import { defineProps, ref } from 'vue';

const props = defineProps({
    handleClick: Function,
    handleClose: Function,
})

const dialogRef = ref('')

const handleDialogOpen = () => {
    dialogRef.value.showModal()
}

const handleDialogClose = () => {
    dialogRef.value.close()
}

defineExpose({
    handleDialogClose,
    handleDialogOpen
});


</script>

<template>
    <dialog class="c-dialog" ref="dialogRef" @click="handleClick" @keydown.esc="handleClose" id="batch-modal">
        <slot></slot>
    </dialog>
</template>