<script setup>
import { useToast } from '../lib/notifications'

const { toasts } = useToast();
</script>

<template>
    <div>
        <div v-for="toast in toasts" :key="toast.id">
            {{ toast.message }}
        </div>
    </div>
</template>
