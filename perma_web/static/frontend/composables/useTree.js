/**
 * Vue composable wrapping @headless-tree/core's createTree().
 * Named useTree to match @headless-tree/react's export.
 *
 * Follows the integration contract described at
 * https://headless-tree.lukasbach.com/contributing/new-frameworks/
 * using the React hook as reference implementation:
 * https://github.com/lukasbach/headless-tree/blob/main/packages/react/src/use-tree.tsx
 */
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { createTree } from '@headless-tree/core';

export function useTree(config) {
  const tree = createTree(config);
  const internalState = ref(tree.getState());
  let syncing = false;

  function handleSetState(updater) {
    const newState = typeof updater === 'function'
      ? updater(internalState.value)
      : updater;
    internalState.value = { ...internalState.value, ...newState };
    config.setState?.(internalState.value);
    syncConfig();
  }

  function syncConfig() {
    if (syncing) return;
    syncing = true;
    tree.setConfig(prev => ({
      ...prev,
      ...config,
      state: {
        ...internalState.value,
        ...config.state,
      },
      setState: handleSetState,
    }));
    syncing = false;
  }

  syncConfig();

  const items = computed(() => {
    void internalState.value;
    return [...tree.getItems()];
  });

  onMounted(() => {
    tree.setMounted(true);
    tree.rebuildTree();
  });

  onBeforeUnmount(() => {
    tree.setMounted(false);
  });

  return { tree, items, state: internalState };
}
