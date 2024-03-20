<template>
    <h1>Hello {{ msg }}</h1>
  </template>
  
<script setup>
import { ref } from 'vue';

const msg = ref<string>('World');
</script>