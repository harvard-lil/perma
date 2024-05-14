<script setup>
import { ref } from 'vue'
import FolderSelect from './FolderSelect.vue';

const dialogRef = ref('')
const handleDialogOpen = () => {
    dialogRef.value.showModal();
}

const handleDialogClose = () => {
    dialogRef.value.close();
}

const handleDialogClick = (e) => {
    if (e.target.classList.contains('c-dialog')) {
        dialogRef.value.close();
    }
}

defineExpose({
    handleDialogClose,
    handleDialogClick,
    handleDialogOpen
});

</script>

<template>
    <dialog class="c-dialog" ref="dialogRef" @click="handleDialogClick">
        <div class="modal-dialog modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" @click.prevent="handleDialogClose">
                    <span aria-hidden="true">&times;</span>
                    <span class="sr-only" id="loading">Close</span>
                </button>
                <h3 id="batch-modal-title" class="modal-title">Create A Link Batch</h3>
            </div>
            <!-- <div class="spinner _hide">
                <span class="sr-only" id="loading" tabindex="-1">Loading</span>
            </div> -->
            <div class="modal-body">
                <div id="batch-create-input">
                    <div class="form-group">
                        <FolderSelect />
                    </div>
                    <div class="form-group">
                        <textarea aria-label="Paste your URLs here (one URL per line)"
                            placeholder="Paste your URLs here (one URL per line)"></textarea>
                    </div>
                    <div class="form-buttons">
                        <button id="start-batch" class="btn" disabled="disabled">Create Links</button>
                        <button class="btn cancel" @click.prevent="handleDialogClose">Cancel</button>
                    </div>
                </div>

                <div id="batch-details-wrapper">
                    <p id="batch-progress-report"></p>
                    <div id="batch-details" aria-describedby="batch-progress-report"></div>
                    <div class="form-buttons">
                        <button class="btn cancel" data-dismiss="modal">Exit</button>
                        <a href="#" id="export-csv" class="btn _hide" @click.prevent="handleDialogClose">Export list as
                            CSV</a>
                    </div>
                </div>
            </div>
        </div>
    </dialog>
</template>