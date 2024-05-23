<script setup>
import { useToast } from '../lib/notifications'

const { toasts } = useToast();
</script>

<template>
    <TransitionGroup name="fade">
        <div v-for="toast in toasts" :key="toast.id" :class="`alert alert-${toast.status} alert-dismissible
        popup-alert`" role="alert">
            {{ toast.message }}
            <button type="button" class="close"><span aria-hidden="true">&times;</span><span
                    class="sr-only">Close</span></button>
        </div>
    </TransitionGroup>
</template>