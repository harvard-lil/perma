<script setup>
import { useGlobalStore } from '../stores/globalStore'
import { storeToRefs } from 'pinia'

const { toasts } = storeToRefs(useGlobalStore())
</script>

<template>
  <TransitionGroup name="fade">
    <div 
      v-for="toast in toasts" 
      :key="toast.id" 
      :class="`alert alert-${toast.level} alert-dismissible popup-alert`" 
      role="alert" 
      aria-live="assertive"
    >
      {{ toast.message }}
      <span v-if="toast.message.includes('logged out')">
        Please <a href='/login' class="u-underline">log in</a> to continue.
      </span>
      <button type="button" class="close">
        <span aria-hidden="true">&times;</span>
        <span class="sr-only">Close</span>
      </button>
    </div>
  </TransitionGroup>
</template>
