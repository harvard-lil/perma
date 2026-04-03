import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { createTree } from "@headless-tree/core";

// Vue composable wrapping Headless Tree's createTree(); follows the contract described at
// https://headless-tree.lukasbach.com/contributing/new-frameworks/ and modeled upon the React hook:
// https://github.com/lukasbach/headless-tree/blob/main/packages/react/src/use-tree.tsx
export function useTree(config) {
  const tree = createTree(config);
  const internalState = ref(tree.getState());
  let syncing = false;

  function handleSetState(updater) {
    const newState =
      typeof updater === "function" ? updater(internalState.value) : updater;
    internalState.value = { ...internalState.value, ...newState };
    config.setState?.(internalState.value);
    syncConfig();
  }

  function syncConfig() {
    if (syncing) return;
    syncing = true;
    tree.setConfig((prev) => ({
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

  // Vue/React prop compatibility helpers
  function containerProps(treeLabel) {
    const { ref, onDragOver, onDrop, ...attrs } = tree.getContainerProps(
      treeLabel,
    );
    return {
      attrs,
      events: {
        dragover: (e) => {
          e.dataTransfer.dropEffect = "move";
          onDragOver(e);
        },
        drop: onDrop,
      },
    };
  }

  function itemProps(item) {
    const {
      ref,
      onDragStart,
      onDragEnd,
      onDragEnter,
      onDragOver,
      onDragLeave,
      onDrop,
      onDblClick,
      onKeyDown,
      ...attrs
    } = item.getProps();

    const events = {};
    if (onDragStart)
      events.dragstart = (e) => {
        e.dataTransfer.effectAllowed = "move";
        document.body.classList.add("dragging");
        onDragStart(e);
      };
    if (onDragEnd)
      events.dragend = (e) => {
        document.body.classList.remove("dragging");
        onDragEnd(e);
      };
    if (onDragEnter) events.dragenter = onDragEnter;
    if (onDragOver)
      events.dragover = (e) => {
        e.dataTransfer.dropEffect = "move";
        onDragOver(e);
      };
    if (onDragLeave) events.dragleave = onDragLeave;
    if (onDrop) events.drop = onDrop;
    if (onKeyDown) events.keydown = onKeyDown;

    return { attrs, events };
  }

  function vueRenameInputProps(item) {
    const { onChange, ref: _ref, ...rest } = item.getRenameInputProps();
    return { ...rest, onInput: onChange };
  }

  function renameInputRef(el) {
    if (el && document.activeElement !== el) {
      el.focus();
      requestAnimationFrame(() => el.select());
    }
  }

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

  return {
    tree,
    treeItems: items,
    treeState: internalState,
    containerProps,
    itemProps,
    vueRenameInputProps,
    renameInputRef,
  };
}
