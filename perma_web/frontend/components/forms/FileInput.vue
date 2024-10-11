<script setup>
import { useFileDialog } from '@vueuse/core'
import BaseInput from './BaseInput.vue'

const props = defineProps({
  modelValue: [File],
  name: String,
  description: String,
  placeholder: String,
  error: Array,
  id: String,
  required: {
    type: Boolean,
    default: false
  },
  accept: String,
})

const emit = defineEmits(['update:modelValue'])

const {files, open, onChange} = useFileDialog({
  accept: props.accept,
  multiple: false,
})

onChange((fileList) => {
  if (fileList && fileList.length > 0) {
    emit('update:modelValue', fileList[0])
  }
})
</script>

<template>
  <BaseInput v-bind="props">
    <button type="button" @click="open">Choose file</button>
    <span v-if="files && files.length > 0" style="margin-left: 10px"> {{ files[0].name }}</span>
  </BaseInput>
</template>