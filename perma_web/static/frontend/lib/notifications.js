import { ref } from 'vue';
import { useTimeoutFn } from '@vueuse/core';

const toasts = ref([]);

export const useToast = () => {
  const addToast = (message, status) => {
    const id = Date.now();
    toasts.value.push({id, message, status});

    useTimeoutFn(() => {
      toasts.value = toasts.value.filter(toast => toast.id !== id);
    }, 3000);
  };

  return {
    toasts,
    addToast
  };
}