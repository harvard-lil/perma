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
    <svg v-if="isChevron" aria-hidden="true" width="18" height="9" viewBox="0 0 18 9" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path v-if="props.icon === 'chevron-down'" d="M8.84746 9L18 2.03226L16.1695 0L8.84746 5.48474L1.83051 7.77811e-08L0 2.03226L8.84746 9Z" fill="#2E76EE"/>
      <path v-if="props.icon === 'chevron-up'" d="M8.84746 0L18 6.96774L16.1695 9L8.84746 3.51526L1.83051 9L0 6.96774L8.84746 0Z" fill="#2E76EE"/>
    </svg>
    <span class="sr-only">{{ props.name }}</span>
  </button>
</template>
