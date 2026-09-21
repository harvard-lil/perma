<script setup>
const props = defineProps({
  name: String,
  handleClick: Function,
  iconFamily: {
    type: String,
    default: "fontAwesome",
    validator(value) {
      return ["fontAwesome", "none"].includes(value);
    },
  },
  icon: {
    type: String,
    validator(value) {
      return [
        "download-alt",
        "plus",
        "edit",
        "trash",
        "chevron-down",
        "chevron-up",
      ].includes(value);
    },
  },
});

const isChevron = props.icon === "chevron-down" || props.icon === "chevron-up";
</script>

<template>
  <button
    :onClick="props.handleClick"
    :class="`c-button c-button--icon ${
      props.iconFamily === 'fontAwesome' ? `icon-${props.icon}` : ''
    }`"
  >
    <svg v-if="isChevron" class="c-button__chevron" aria-hidden="true" width="14" height="7" viewBox="0 0 14 7" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path v-if="props.icon === 'chevron-down'" d="M6.88136 7L14 1.58065L12.5763 0L6.88136 4.26591L1.42373 0L0 1.58065L6.88136 7Z" fill="#2E76EE"/>
      <path v-if="props.icon === 'chevron-up'" d="M6.88136 0L14 5.41935L12.5763 7L6.88136 2.73409L1.42373 7L0 5.41935L6.88136 0Z" fill="#2E76EE"/>
    </svg>
    <span class="sr-only">{{ props.name }}</span>
  </button>
</template>
