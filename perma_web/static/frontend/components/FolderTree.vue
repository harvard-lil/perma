<script setup>
import {
  asyncDataLoaderFeature,
  dragAndDropFeature,
  keyboardDragAndDropFeature,
  hotkeysCoreFeature,
  renamingFeature,
  selectionFeature,
} from "@headless-tree/core";
import { useLocalStorage, useUrlSearchParams } from "@vueuse/core";
import { computed, onBeforeUnmount, onMounted } from "vue";
import { useTree } from "../composables/useTree";
import { fetchDataOrError } from "../lib/data";
import { useGlobalStore } from "../stores/globalStore";

const globalStore = useGlobalStore();
const currentUser = globalStore.currentUser;

const localStorageKey = "perma_selection";
const savedFoldersState = useLocalStorage(localStorageKey, {});
const urlParams = useUrlSearchParams("history");

// Tree spacing constants
const indentPixels = 20;
const iconSizePixels = 16;

const privateOrgIds = computed(() =>
  globalStore.currentUser.top_level_folders
    .filter((folder) => folder.default_to_private)
    .map((folder) => folder.organization),
);

const getUrlFolderIds = () => {
  const raw = urlParams.folder;
  if (!raw) return null;
  const ids = raw.split("-").map((s) => parseInt(s, 10));
  return ids.every(id => !isNaN(id)) ? ids : [];
}

// Mapping of folder ID (string) to folder data object
const folderCache = {};

const makeFolderCacheEntry = (folder) => {
  return {
    id: folder.id,
    name: folder.name,
    organization: folder.organization,
    sponsored_by: folder.sponsored_by,
    is_sponsored_root_folder: folder.is_sponsored_root_folder,
    read_only: folder.read_only,
    has_children: folder.has_children,
    parent: folder.parent,
    is_shared_folder: !!(folder.organization && !folder.parent),
  };
};

const cacheFolders = (apiFolders) => {
  for (const folder of apiFolders) {
    folderCache[String(folder.id)] = makeFolderCacheEntry(folder);
  }
}

cacheFolders(currentUser.top_level_folders);

// Custom click behavior for folders
const customClickBehavior = {
  itemInstance: {
    getProps: ({ tree, item, prev }) => ({
      ...prev?.(),
      onClick: (e) => {
        const itemId = item.getItemMeta().itemId;
        const data = item.getItemData();

        // Sponsored root folders: toggle expand/collapse without selecting
        if (data.is_sponsored_root_folder) {
          item.setFocused();
          if (data.has_children) {
            if (item.isExpanded()) {
              item.collapse();
            } else {
              item.expand();
            }
          }
          return;
        }

        // Disclosure triangle: toggle expand/collapse without selecting
        if (e.target.closest(".tree-toggle")) {
          if (data?.has_children) {
            if (item.isExpanded()) item.collapse();
            else item.expand();
          }
          return;
        }

        const wasAlreadySelected = item.isSelected();

        // Selection (mirrors selectionFeature's onClick behavior)
        if (e.shiftKey) {
          item.selectUpTo(e.ctrlKey || e.metaKey);
        } else if (e.ctrlKey || e.metaKey) {
          item.toggleSelect();
        } else {
          tree.setSelectedItems([itemId]);
        }
        if (!e.shiftKey) {
          tree.getDataRef().current.selectUpToAnchorId = itemId;
        }

        // Expand/collapse folders if they have children
        if (data?.has_children) {
          if (!item.isExpanded()) {
            item.expand();
          } else if (wasAlreadySelected) {
            item.collapse();
          }
        }

        item.setFocused();
        if (!wasAlreadySelected) {
          item.primaryAction();
        }
      },
    }),
  },
};

// Produce a user-facing message about an API error
const getApiErrorMessage = (data, fallback) => {
  if (!data) return fallback;
  if (Array.isArray(data)) return data[0] || fallback;
  for (const messages of Object.values(data)) {
    if (Array.isArray(messages) && messages.length)
      return `Error: ${messages[0]}`;
  }
  return fallback;
};

// Produce a user-facing message about a folder restriction
const getFolderRestriction = (item) => {
  const data = item.getItemData();
  if (!data || data._isRoot || data._loading)
    return "This folder cannot be moved or renamed.";
  if (data.is_sponsored_root_folder)
    return "Sponsored folders cannot be moved or renamed.";
  if (data.is_shared_folder)
    return "Shared folders cannot be moved or renamed.";
  const parent = item.getParent();
  if (!parent || parent.getItemMeta().itemId === "root")
    return "Top-level folders cannot be moved or renamed.";
  return null;
};

// Determine whether a drag and drop target is valid
const isValidDropTarget = (target) => {
  // Prevent dropping "between" items to match canReorder: false behavior
  if ("childIndex" in target) return false;

  if (target.item.getItemMeta().itemId === "root") return true;
  const data = target.item.getItemData();
  if (!data || data._loading) return false;
  if (data.is_sponsored_root_folder) return false;
  if (data.read_only) return false;
  return true;
};

// Initialize tree and related elements
const {
  tree,
  treeItems,
  treeState,
  containerProps,
  itemProps,
  vueRenameInputProps,
  renameInputRef
} = useTree({
  rootItemId: "root",
  getItemName: (item) => item.getItemData().name,
  isItemFolder: () => true,
  createLoadingItemData: () => ({ name: "Loading...", _loading: true }),
  indent: indentPixels,
  canReorder: false,
  dataLoader: {
    getItem: (itemId) => {
      if (itemId === "root") {
        return Promise.resolve({ name: "Root", _isRoot: true });
      }
      const cached = folderCache[itemId];
      if (cached) return Promise.resolve(cached);
      return Promise.resolve({ name: "Loading...", _loading: true });
    },
    getChildrenWithData: (itemId) => {
      if (itemId === "root") {
        return Promise.resolve(
          currentUser.top_level_folders.map((f) => ({
            id: String(f.id),
            data: folderCache[String(f.id)] || makeFolderCacheEntry(f),
          })),
        );
      }
      return fetchDataOrError(`/folders/${itemId}/folders/?limit=500`).then(
        ({ data, error }) => {
          if (error || !data?.objects) return [];
          cacheFolders(data.objects);
          return data.objects.map((f) => ({
            id: String(f.id),
            data: folderCache[String(f.id)],
          }));
        },
      );
    },
  },

  // Drag and drop handling
  canDrag: (dragItems) => {
    for (const item of dragItems) {
      const restriction = getFolderRestriction(item);
      if (restriction) {
        globalStore.addToast(restriction, "warning");
        return false;
      }
    }
    return true;
  },
  canDrop: (_dragItems, target) => isValidDropTarget(target),
  onDrop: async (dragItems, target) => {
    const newParentId = target.item.getItemMeta().itemId;
    for (const item of dragItems) {
      const folderId = item.getItemMeta().itemId;
      const oldParent = item.getParent();

      // If item was dropped on its own parent, do nothing
      if (oldParent && oldParent.getItemMeta().itemId === newParentId) {
        continue;
      }

      const oldSiblingCount = oldParent ? oldParent.getChildren().length : 0;
      const {
        data: responseData,
        error,
      } = await fetchDataOrError(
        `/folders/${newParentId}/folders/${folderId}/`,
        { method: "PUT" },
      );
      if (error) {
        globalStore.addToast(
          getApiErrorMessage(responseData, "Error moving folder."),
          "error",
        );
        return;
      }
      const targetData = folderCache[newParentId];
      if (targetData) targetData.has_children = true;
      if (oldParent) {
        const oldParentId = oldParent.getItemMeta().itemId;
        if (oldParentId !== "root" && oldSiblingCount <= 1) {
          const oldParentData = folderCache[oldParentId];
          if (oldParentData) oldParentData.has_children = false;
        }
        oldParent.invalidateChildrenIds();
      }
      target.item.invalidateChildrenIds();
    }
    tree.rebuildTree();
  },

  // Foreign drag and drop handling for links dragged from LinkList
  canDropForeignDragObject: (_dataTransfer, target) =>
    isValidDropTarget(target),
  canDragForeignDragObjectOver: (_dataTransfer, target) =>
    isValidDropTarget(target),
  onDropForeignDragObject: async (dataTransfer, target) => {
    const linkGuid = dataTransfer.getData("application/x-perma-link");
    if (!linkGuid) return;
    const folderId = target.item.getItemMeta().itemId;
    const { data, error } = await fetchDataOrError(
      `/folders/${folderId}/archives/${linkGuid}/`,
      {
        method: "PUT",
      },
    );
    if (error) {
      globalStore.addToast(
        getApiErrorMessage(data, "Error moving link."),
        "error",
      );
      return;
    }
    if (data?.links_remaining !== undefined) {
      globalStore.linksRemaining = data.links_remaining;
    }
    // Remove the link from the current link list display
    globalStore.components.linkList?.fetchLinks();
  },

  // Folder rename handling
  canRename: (item) => !getFolderRestriction(item),
  onRename: async (item, newName) => {
    const folderId = item.getItemMeta().itemId;
    const { data, error } = await fetchDataOrError(`/folders/${folderId}/`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName }),
    });
    if (error) {
      globalStore.addToast(
        getApiErrorMessage(data, "Error renaming folder."),
        "error",
      );
      return;
    }
    // Update the cached data
    if (folderCache[folderId]) {
      folderCache[folderId].name = newName;
    }
    item.updateCachedData({ ...item.getItemData(), name: newName });
    updateSelectedFolderFromItem(item);
  },

  // Folder selection handling
  onPrimaryAction: (item) => {
    updateSelectedFolderFromItem(item);
  },

  // Keyboard shortcuts for tree navigation and keyboard drag and drop
  hotkeys: {
    expandOrDown: {
      hotkey: "ArrowRight",
      canRepeat: true,
      handler: (e, tree) => {
        if (tree.getState().dnd) {
          // If dragging, just expand the current drag target if it's closed
          const target = tree.getDragTarget()?.item || tree.getFocusedItem();
          if (target && target.isFolder() && !target.isExpanded()) {
            target.expand();
          }
          return; // Do not move focus
        }
        // Default behavior when not dragging
        const item = tree.getFocusedItem();
        if (item.isExpanded() || !item.isFolder()) {
          tree.focusNextItem();
          tree.updateDomFocus();
        } else {
          item.expand();
        }
      }
    },
    collapseOrUp: {
      hotkey: "ArrowLeft",
      canRepeat: true,
      handler: (e, tree) => {
        if (tree.getState().dnd) {
          // If dragging, just collapse the current drag target if it's expanded
          const target = tree.getDragTarget()?.item || tree.getFocusedItem();
          if (target && target.isFolder() && target.isExpanded()) {
            target.collapse();
          }
          return; // Do not move focus to parent
        }
        // Default behavior when not dragging
        const item = tree.getFocusedItem();
        if ((!item.isExpanded() || !item.isFolder()) && item.getItemMeta().level !== 0) {
          item.getParent()?.setFocused();
          tree.updateDomFocus();
        } else {
          item.collapse();
        }
      }
    },
    focusFirstItem: {
      hotkey: "Home",
      handler: (e, tree) => {
        if (tree.getState().dnd) return;
        tree.getItems()[0]?.setFocused();
        tree.updateDomFocus();
      }
    },
    focusLastItem: {
      hotkey: "End",
      handler: (e, tree) => {
        if (tree.getState().dnd) return;
        const items = tree.getItems();
        items[items.length - 1]?.setFocused();
        tree.updateDomFocus();
      }
    }
  },

  features: [
    asyncDataLoaderFeature,
    selectionFeature,
    hotkeysCoreFeature,
    dragAndDropFeature,
    keyboardDragAndDropFeature,
    renamingFeature,
    customClickBehavior,
  ],
});

// Wait for a tree item to be loaded
const waitForTreeItem = async (
  itemId,
  { maxAttempts = 20, interval = 50 } = {},
) => {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((resolve) => setTimeout(resolve, interval));
    try {
      const item = tree.getItemInstance(itemId);
      if (item) return item;
    } catch {
      // No-op: item not loaded yet
    }
  }
  return null;
};

// Compute guide lines for each tree item
const treeGuideLines = computed(() => {
  const itemsList = treeItems.value;
  const itemsCount = itemsList.length;
  const guideLines = new Array(itemsCount);
  const activeLevels = new Set();

  for (let i = itemsCount - 1; i >= 0; i--) {
    const level = itemsList[i].getItemMeta().level;
    const ancestors = [];
    for (const l of activeLevels) {
      if (l < level) ancestors.push(l);
    }
    guideLines[i] = {
      isLast: !activeLevels.has(level), // Is this the last sibling at this level?
      ancestors: ancestors.sort((a, b) => a - b), // Levels at which to place guide lines
    };
    activeLevels.add(level);
    for (const l of [...activeLevels]) {
      if (l > level) activeLevels.delete(l);
    }
  }

  return guideLines;
});

// Compute the indentation level for a tree item level
const levelIndent = (level) => {
  return (level + 1) * indentPixels;
};

// Compute the left position for a tree item level
const levelLineLeft = (level) => {
  return levelIndent(level) - (indentPixels - (iconSizePixels / 2));
};

// Get the folder icon class (open, closed, or shared) for a tree item
const getFolderIconClass = (item) => {
  const icons = {
    open: "icon-folder-open-alt",
    closed: "icon-folder-close-alt",
    shared: "icon-sitemap",
  };
  const data = item.getItemData();
  if (data?.is_shared_folder) return icons.shared;
  return item.isExpanded() && data?.has_children ? icons.open : icons.closed;
};

// Build ancestry path and folder IDs for a tree item
const buildItemAncestry = (item) => {
  const path = [];
  const folderIds = [];
  let current = item;
  while (current) {
    const folderId = current.getItemMeta().itemId;
    if (folderId === "root") break;
    folderIds.unshift(parseInt(folderId, 10));
    const data = current.getItemData();
    if (data?.name) path.unshift(data.name);
    current = current.getParent();
  }
  return { path, folderIds };
};

// Calculate the full folder path (hyphen-separated) for an item
const getFolderPath = (item) => {
  const { folderIds } = buildItemAncestry(item);
  return folderIds.length ? folderIds.join("-") : null;
};

// Update the global store's selected folder from a tree item
const updateSelectedFolderFromItem = (item) => {
  const data = item.getItemData();
  if (!data || data._isRoot || data._loading) return;
  if (data.is_sponsored_root_folder) return;

  const folderId = parseInt(item.getItemMeta().itemId, 10);
  const orgId = data.organization || "";
  const sponsorId = data.sponsored_by || "";
  const isReadOnly = !!data.read_only;
  const isPrivate = orgId ? privateOrgIds.value.includes(orgId) : false;
  const isOutOfLinks =
    !isReadOnly && !sponsorId && !orgId && !globalStore.linkCreationAllowed;
  const { path, folderIds } = buildItemAncestry(item);

  savedFoldersState.value[currentUser.id] = { folderIds, orgId };
  urlParams.folder = getFolderPath(item);

  globalStore.selectedFolder = {
    folderId,
    orgId,
    sponsorId,
    isReadOnly,
    isOutOfLinks,
    path,
    isPrivate,
  };
};

onMounted(async () => {
  globalStore.components.folderTree = {
    selectFolder,
    getOpenFolders,
    startKeyboardDragOnForeignObject,
  };

  // Pre-fetch saved path folders to stick in the cache, then expand them
  const savedIds = getUrlFolderIds() || savedFoldersState.value[currentUser.id]?.folderIds;
  if (savedIds && savedIds.length) {
    const validIds = [];
    for (const folderId of savedIds) {
      const { data, error } = await fetchDataOrError(
        `/folders/${folderId}/folders/?limit=500`,
      );
      if (error || !data?.objects) break;
      cacheFolders(data.objects);
      validIds.push(folderId);
    }
    if (validIds.length) {
      tree.applySubStateUpdate("expandedItems", () => validIds.map(String));
    }
  }

  // Select saved folder after tree has loaded the path
  selectInitialFolder();
});

onBeforeUnmount(() => {
  globalStore.components.folderTree = null;
});

// Select initial folder after tree has loaded path from URL
const selectInitialFolder = async () => {
  const savedIds = getUrlFolderIds() || savedFoldersState.value[currentUser.id]?.folderIds;
  let folderToSelect = savedIds && savedIds.length ? savedIds[savedIds.length - 1] : null;
  if (!folderToSelect && currentUser.top_level_folders.length === 1) {
    folderToSelect = currentUser.top_level_folders[0].id;
  }
  if (!folderToSelect) return;

  const itemId = String(folderToSelect);
  const item = await waitForTreeItem(itemId);
  if (item) {
    tree.setSelectedItems([itemId]);
    item.setFocused();
    updateSelectedFolderFromItem(item);
  }
};

// Toolbar actions: new folder
let creatingFolder = false;

const createNewFolder = async () => {
  if (creatingFolder) return;
  creatingFolder = true;
  try {
    const selectedItems = tree.getSelectedItems();
    if (!selectedItems.length) {
      globalStore.addToast("Please select a folder first.", "warning");
      return;
    }
    const parent = selectedItems[0];
    const selectedData = parent.getItemData();
    if (selectedData?.is_sponsored_root_folder) {
      globalStore.addToast(
        "Folders cannot be created in sponsored folders.",
        "warning",
      );
      return;
    }
    if (selectedData?.read_only) {
      globalStore.addToast("This folder is read-only.", "warning");
      return;
    }
    const parentId = parent.getItemMeta().itemId;
    const { data, error } = await fetchDataOrError(
      `/folders/${parentId}/folders/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "New Folder" }),
      },
    );
    if (error) {
      globalStore.addToast(
        getApiErrorMessage(data, "Error creating folder."),
        "error",
      );
      return;
    }
    folderCache[String(data.id)] = makeFolderCacheEntry({
      ...data,
      name: data.name || "New Folder",
      parent: parseInt(parentId, 10),
    });
    const parentData = folderCache[parentId];
    if (parentData) parentData.has_children = true;
    await parent.invalidateItemData();
    await parent.invalidateChildrenIds();
    if (!parent.isExpanded()) parent.expand();

    const newId = String(data.id);
    const newItem = await waitForTreeItem(newId, {
      maxAttempts: 10,
      interval: 200,
    });
    if (newItem) {
      tree.setSelectedItems([newId]);
      newItem.setFocused();
      newItem.startRenaming();
    }
  } finally {
    creatingFolder = false;
  }
};

// Toolbar actions: rename folder
const renameFolder = () => {
  const selectedItems = tree.getSelectedItems();
  if (!selectedItems.length) return;
  const item = selectedItems[0];
  const restriction = getFolderRestriction(item);
  if (restriction) {
    globalStore.addToast(restriction, "warning");
    return;
  }
  item.startRenaming();
};

// Toolbar actions: delete folder
const deleteFolder = async () => {
  const selectedItems = tree.getSelectedItems();
  if (!selectedItems.length) return;
  const item = selectedItems[0];
  const data = item.getItemData();
  if (!data || data._isRoot) return;
  if (data.is_sponsored_root_folder) {
    globalStore.addToast("Sponsored folders cannot be deleted.", "warning");
    return;
  }

  if (!confirm(`Really delete folder '${data.name}'?`)) return;

  const folderId = item.getItemMeta().itemId;
  const parent = item.getParent();
  const { data: responseData, error } = await fetchDataOrError(
    `/folders/${folderId}/`,
    {
      method: "DELETE",
    },
  );
  if (error) {
    globalStore.addToast(
      getApiErrorMessage(responseData, "Error deleting folder."),
      "error",
    );
    return;
  }
  delete folderCache[folderId];
  if (parent) {
    const siblingCount = parent.getChildren().length;
    const parentId = parent.getItemMeta().itemId;
    if (parentId !== "root" && siblingCount <= 1) {
      const parentData = folderCache[parentId];
      if (parentData) parentData.has_children = false;
      if (parent.isExpanded()) parent.collapse();
    }
    parent.invalidateChildrenIds();
    if (parentId !== "root") {
      tree.setSelectedItems([parentId]);
      parent.setFocused();
      updateSelectedFolderFromItem(parent);
    } else {
      tree.setSelectedItems([]);
      savedFoldersState.value[currentUser.id] = { folderIds: [], orgId: null };
      urlParams.folder = null;
    }
  }
};

// Exposed API for component consumers

// Select a folder
const selectFolder = (folderId) => {
  // Called by FolderSelect.vue when user picks a folder from the dropdown
  const idStr = String(folderId);
  try {
    const item = tree.getItemInstance(idStr);
    if (item) {
      tree.setSelectedItems([idStr]);
      item.setFocused();
      // Expand parents up to this item
      let parent = item.getParent();
      while (parent && parent.getItemMeta().itemId !== "root") {
        if (!parent.isExpanded()) parent.expand();
        parent = parent.getParent();
      }
      updateSelectedFolderFromItem(item);
      return;
    }
  } catch {
    // No-op: item not loaded yet
  }

  // If item is not yet loaded, save it and reload the tree
  const orgId = folderCache[idStr]?.organization || "";
  savedFoldersState.value[currentUser.id] = {
    folderIds: [parseInt(folderId, 10)],
    orgId
  };
  urlParams.folder = String(folderId);
  window.location.reload();
};

// Produce an array of objects representing all currently expanded folders for LinkList to use
const getOpenFolders = () => {
  const result = [];
  for (const item of tree.getItems()) {
    const data = item.getItemData();
    if (!data || data._isRoot || data._loading) continue;
    const level = item.getItemMeta().level;
    result.push({
      value: parseInt(item.getItemMeta().itemId, 10),
      text:
        (level > 1 ? "\u2514".padStart(level, "\u00A0") + " " : "") + data.name,
      selected:
        parseInt(item.getItemMeta().itemId, 10) ===
        globalStore.selectedFolder.folderId,
      disabled: data.is_sponsored_root_folder || data.read_only,
      orgId: data.organization,
    });
  }
  return result;
};

// Start keyboard-controlled drag and drop from an external source (like LinkList)
const startKeyboardDragOnForeignObject = (dataTransfer) => {
  tree.startKeyboardDragOnForeignObject(dataTransfer);
  tree.updateDomFocus();
};

// Produce assistive text for keyboard drag and drop
const assistiveDndText = computed(() => {
  const dndState = treeState.value.dnd;
  const assistiveDndState = treeState.value.assistiveDndState;

  if (assistiveDndState === 1 && dndState?.draggedItems?.length) { // Started
    const itemNames = dndState.draggedItems.map(item => item.getItemName()).join(', ');
    return `Started dragging ${itemNames}. Use arrow keys to move the drag target, Enter to drop, or Escape to cancel.`;
  }
  if (assistiveDndState === 2 && dndState?.dragTarget?.item) { // Dragging
    return `Dragging over ${dndState.dragTarget.item.getItemName()}.`;
  }
  if (assistiveDndState === 3) { // Completed
    return "Drop completed.";
  }
  if (assistiveDndState === 4) { // Aborted
    return "Drag aborted.";
  }
  return "";
});

defineExpose({
  selectFolder,
  getOpenFolders,
  startKeyboardDragOnForeignObject,
});
</script>

<template>
  <div class="panel-heading">
    Folders
    <span class="buttons">
      <a href="#" class="pull-right delete-folder icon-trash" aria-label="Delete selected folder"
        title="Delete selected folder" @click.prevent="deleteFolder"></a>
      <a href="#" class="pull-right edit-folder icon-edit" aria-label="Rename selected folder"
        title="Rename selected folder" @click.prevent="renameFolder"></a>
      <a href="#" class="pull-right new-folder icon-plus" aria-label="New folder" title="New folder"
        @click.prevent="createNewFolder"></a>
    </span>
  </div>
  <div v-bind="containerProps('Folders').attrs" v-on="containerProps('Folders').events"
    :ref="(el) => el && tree.registerElement(el)" id="folder-tree">
    <div class="sr-only" aria-live="assertive">{{ assistiveDndText }}</div>
    <template v-for="(item, idx) in treeItems" :key="item.getId()">
      <div class="folder-item-wrapper">
        <span v-for="l in treeGuideLines[idx].ancestors" :key="l" class="tree-guide"
          :style="{ left: levelLineLeft(l) + 'px' }"></span>
        <span class="tree-vertical" :class="{ 'tree-last': treeGuideLines[idx].isLast }"
          :style="{ left: levelLineLeft(item.getItemMeta().level) + 'px' }"></span>
        <span class="tree-horizontal" :style="{ left: levelLineLeft(item.getItemMeta().level) + 'px' }"></span>
        <div v-if="item.isRenaming()" class="folder-item renaming"
          :data-folder-path="getFolderPath(item)"
          :style="{ paddingLeft: levelIndent(item.getItemMeta().level) + 'px' }">
          <span v-if="item.getItemData()?.has_children" class="tree-toggle"></span>
          <span class="folder-icon" :class="getFolderIconClass(item)"></span>
          <input v-bind="vueRenameInputProps(item)" :ref="renameInputRef" class="folder-rename-input" />
        </div>
        <button v-else v-bind="itemProps(item).attrs" v-on="itemProps(item).events"
          :data-folder-path="getFolderPath(item)"
          :ref="(el) => el && item.registerElement(el)"
          :style="{ paddingLeft: levelIndent(item.getItemMeta().level) + 'px' }" :aria-disabled="item.getItemData()?.is_sponsored_root_folder || undefined
            " class="folder-item" :class="{
              selected: item.isSelected(),
              focused: item.isFocused(),
              expanded: item.isExpanded() && item.getItemData()?.has_children,
              'drag-target': item.isDragTarget?.(),
              'is-shared': item.getItemData()?.is_shared_folder,
              'is-disabled': item.getItemData()?.is_sponsored_root_folder,
            }">
          <span v-if="item.getItemData()?.has_children" class="tree-toggle"></span>
          <span class="folder-icon" :class="getFolderIconClass(item)"></span>
          {{ item.getItemName() }}
        </button>
      </div>
    </template>
    <div :style="tree.getDragLineStyle()" class="dragline" />
  </div>
</template>
