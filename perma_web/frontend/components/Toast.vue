<script setup>
import { useToast } from '../lib/notifications'

const { toasts } = useToast();
</script>

<template>
    <template v-for="toast in toasts" :key="toast.id">
        <div :class="`alert alert-${toast.status} alert-dismissible popup-alert`" role="alert">
            {{ toast.message }}
            <button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span
                    class="sr-only">Close</span></button>
        </div>
    </template>
</template>