<script setup>
import {
  asyncDataLoaderFeature,
  dragAndDropFeature,
  hotkeysCoreFeature,
  renamingFeature,
  selectionFeature,
} from "@headless-tree/core";
import { computed, onBeforeUnmount, onMounted } from "vue";
import { useTree } from "../composables/useTree";
import { fetchDataOrError } from "../lib/data";
import { useGlobalStore } from "../stores/globalStore";

const globalStore = useGlobalStore();
const current_user = window.current_user;
const LOCAL_STORAGE_KEY = "perma_selection";

const privateOrgIds = computed(() =>
  globalStore.currentUser.top_level_folders
    .filter((folder) => folder.default_to_private)
    .map((folder) => folder.organization),
);

// --- Local storage / URL persistence ---

function jsonLocalStorageGet(key) {
  try {
    return JSON.parse(localStorage.getItem(key));
  } catch {
    return localStorage.getItem(key);
  }
}

function jsonLocalStorageSet(key, value) {
  localStorage.setItem(
    key,
    typeof value === "string" ? value : JSON.stringify(value),
  );
}

// This data structure supports multiple users' last-used folders stored
// simultaneously, keyed by user id. Currently only one user is active at a
// time (localStorage is cleared on logout).
function savedFoldersGetAll() {
  return jsonLocalStorageGet(LOCAL_STORAGE_KEY) || {};
}

function savedFoldersGetCurrent() {
  return savedFoldersGetAll()[current_user.id] || {};
}

function savedFoldersSetCurrent(orgId, folderIds) {
  const all = savedFoldersGetAll();
  all[current_user.id] = { folderIds, orgId };
  if (folderIds && folderIds.length) {
    history.pushState(null, null, "?folder=" + folderIds.join("-"));
  }
  jsonLocalStorageSet(LOCAL_STORAGE_KEY, all);
}

function folderIdsFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("folder");
  if (!raw) return null;
  try {
    const ids = raw.split("-").map((s) => parseInt(s, 10));
    ids.forEach((id) => {
      if (isNaN(id)) throw new Error("Invalid folder id");
    });
    return ids;
  } catch (err) {
    console.error(err);
    return [];
  }
}

function getSavedFolderIds() {
  return folderIdsFromUrl() || savedFoldersGetCurrent().folderIds;
}

function getSavedFolderId() {
  const ids = getSavedFolderIds();
  return ids && ids.length ? ids[ids.length - 1] : null;
}

// --- Folder data cache (for the async data loader) ---

// folderCache maps string folder id -> folder data object
const folderCache = {};

function makeFolderCacheEntry(f) {
  return {
    id: f.id,
    name: f.name,
    organization: f.organization,
    sponsored_by: f.sponsored_by,
    is_sponsored_root_folder: f.is_sponsored_root_folder,
    read_only: f.read_only,
    has_children: f.has_children,
    parent: f.parent,
    is_shared_folder: !!(f.organization && !f.parent),
  };
}

function cacheFolders(apiFolders) {
  for (const folder of apiFolders) {
    folderCache[String(folder.id)] = makeFolderCacheEntry(folder);
  }
}

// Pre-cache top-level folders from user object
cacheFolders(current_user.top_level_folders);

// Clicking a closed folder expands it; clicking an already-selected
// open folder collapses it
const customClickBehavior = {
  itemInstance: {
    getProps: ({ tree, item, prev }) => ({
      ...prev?.(),
      onClick: (e) => {
        const itemId = item.getItemMeta().itemId;
        const data = item.getItemData();

        // Sponsored root folders: toggle expand/collapse
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

        // Click on disclosure triangle: toggle expand without selecting
        if (e.target.closest(".tree-toggle")) {
          if (data?.has_children) {
            if (item.isExpanded()) item.collapse();
            else item.expand();
          }
          return;
        }

        const wasAlreadySelected = item.isSelected();

        // Selection (mirrors selectionFeature's onClick)
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

        // Expand/collapse only for folders with children
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
        // Do NOT chain to prev?.()?.onClick?.(e) -- the core tree
        // feature's onClick has its own expand/collapse logic that
        // would immediately reverse what we just did.
      },
    }),
  },
};

// --- Vue / React prop compatibility helpers ---
//
// Headless Tree generates React-style props (onDragStart, onChange, ref
// callbacks, etc.). Three adjustments are needed for Vue:
//
// 1. `ref` callbacks: React passes `ref` to the framework; Vue's v-bind
//    treats `ref` as a plain attribute. We strip it and bind via :ref.
//
// 2. `on*` drag events: Vue 3's v-bind does NOT reliably bind on* props
//    as event listeners for drag events (onClick works, but onDragStart,
//    onDragOver, etc. do not). We strip them from v-bind and use v-on
//    with lowercase event names instead.
//
// 3. `onChange` on <input>: React fires onChange on every keystroke;
//    Vue maps onChange to the native "change" event (blur/Enter only).
//    We remap to onInput.

function containerProps() {
  const { ref, onDragOver, onDrop, ...attrs } = tree.getContainerProps(
    "Folders",
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
    onDblClick: _onDblClick,
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

function getApiErrorMessage(data, fallback) {
  if (!data) return fallback;
  if (Array.isArray(data)) return data[0] || fallback;
  for (const messages of Object.values(data)) {
    if (Array.isArray(messages) && messages.length)
      return `Error: ${messages[0]}`;
  }
  return fallback;
}

// Returns a user-facing message string if the folder is restricted, or null if allowed.
function getFolderRestriction(item) {
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
}

// Allows root so Headless Tree's getDragTarget doesn't short-circuit
// the "drop INTO child folder" logic when canReorder is false.
function isValidDropTarget(target) {
  if (target.item.getItemMeta().itemId === "root") return true;
  const data = target.item.getItemData();
  if (!data || data._loading) return false;
  if (data.is_sponsored_root_folder) return false;
  if (data.read_only) return false;
  return true;
}

// --- Tree setup ---

const { tree, items } = useTree({
  rootItemId: "root",
  getItemName: (item) => item.getItemData().name,
  isItemFolder: () => true,
  createLoadingItemData: () => ({ name: "Loading...", _loading: true }),
  indent: 20,
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
          current_user.top_level_folders.map((f) => ({
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

  // --- Drag and drop (folder-to-folder) ---
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

  // --- Foreign DnD (links dragged from LinkList) ---
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

  // --- Renaming ---
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

  // --- Selection ---
  onPrimaryAction: (item) => {
    updateSelectedFolderFromItem(item);
  },

  features: [
    asyncDataLoaderFeature,
    selectionFeature,
    hotkeysCoreFeature,
    dragAndDropFeature,
    renamingFeature,
    customClickBehavior,
  ],
});

async function waitForTreeItem(
  itemId,
  { maxAttempts = 20, interval = 50 } = {},
) {
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, interval));
    try {
      const item = tree.getItemInstance(itemId);
      if (item) return item;
    } catch {
      /* not loaded yet */
    }
  }
  return null;
}

// --- Tree connector lines ---
// Computes vertical guide lines and ├/└ connectors for each item.
// For each item: { isLast: bool, ancestors: number[] }
//   isLast - whether the item is the last sibling at its level
//   ancestors - levels where a vertical guide line should continue
const treeConnectors = computed(() => {
  const list = items.value;
  const n = list.length;
  const result = new Array(n);
  const activeLevels = new Set();

  for (let i = n - 1; i >= 0; i--) {
    const level = list[i].getItemMeta().level;
    const ancestors = [];
    for (const l of activeLevels) {
      if (l < level) ancestors.push(l);
    }
    result[i] = {
      isLast: !activeLevels.has(level),
      ancestors: ancestors.sort((a, b) => a - b),
    };
    activeLevels.add(level);
    for (const l of [...activeLevels]) {
      if (l > level) activeLevels.delete(l);
    }
  }

  return result;
});

function levelIndent(level) {
  return (level + 1) * 20;
}

function levelLineLeft(level) {
  return levelIndent(level) - 12;
}

function getFolderIconClass(item) {
  const data = item.getItemData();
  if (data?.is_shared_folder) return "icon-sitemap";
  if (item.isExpanded() && data?.has_children) return "icon-folder-open-alt";
  return "icon-folder-close-alt";
}

// --- Selection handling ---

function buildItemAncestry(item) {
  const path = [];
  const folderIds = [];
  let current = item;
  while (current) {
    const id = current.getItemMeta().itemId;
    if (id === "root") break;
    folderIds.unshift(parseInt(id, 10));
    const data = current.getItemData();
    if (data?.name) path.unshift(data.name);
    current = current.getParent();
  }
  return { path, folderIds };
}

function updateSelectedFolderFromItem(item) {
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

  savedFoldersSetCurrent(orgId, folderIds);

  globalStore.selectedFolder = {
    folderId,
    orgId,
    sponsorId,
    isReadOnly,
    isOutOfLinks,
    path,
    isPrivate,
  };
}

// --- Initial selection ---

onMounted(async () => {
  globalStore.components.folderTree = {
    selectFolder,
    getOpenFolders,
  };

  // Pre-fetch saved path folders so they're in the cache, then expand them
  const savedIds = getSavedFolderIds();
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

async function selectInitialFolder() {
  let folderToSelect = getSavedFolderId();
  if (!folderToSelect && current_user.top_level_folders.length === 1) {
    folderToSelect = current_user.top_level_folders[0].id;
  }
  if (!folderToSelect) return;

  const itemId = String(folderToSelect);
  const item = await waitForTreeItem(itemId);
  if (item) {
    tree.setSelectedItems([itemId]);
    item.setFocused();
    updateSelectedFolderFromItem(item);
  }
}

// --- Toolbar actions ---

let creatingFolder = false;

async function newFolder() {
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
}

function editFolder() {
  const selectedItems = tree.getSelectedItems();
  if (!selectedItems.length) return;
  const item = selectedItems[0];
  const restriction = getFolderRestriction(item);
  if (restriction) {
    globalStore.addToast(restriction, "warning");
    return;
  }
  item.startRenaming();
}

async function deleteFolder() {
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
      savedFoldersSetCurrent(null, []);
    }
  }
}

// --- Exposed API for consumers ---

function selectFolder(folderId) {
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
    // fall through
  }

  // If item is not yet loaded, save it and reload the tree
  const orgId = folderCache[idStr]?.organization || "";
  savedFoldersSetCurrent(orgId, [parseInt(folderId, 10)]);
  window.location.reload();
}

function getOpenFolders() {
  // Returns a flat list of {folderId, name, depth, disabled} for all
  // currently visible (expanded) folders, used by LinkList's "Move to folder" dropdown
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
}

defineExpose({
  selectFolder,
  getOpenFolders,
});
</script>

<template>
  <div class="panel-heading">
    Folders
    <span class="buttons">
      <a
        href="#"
        class="pull-right delete-folder icon-trash"
        aria-label="Delete Selected Folder"
        title="Delete Selected Folder"
        @click.prevent="deleteFolder"
      ></a>
      <a
        href="#"
        class="pull-right edit-folder icon-edit"
        aria-label="Rename Selected Folder"
        title="Rename Selected Folder"
        @click.prevent="editFolder"
      ></a>
      <a
        href="#"
        class="pull-right new-folder icon-plus"
        aria-label="New Folder"
        title="New Folder"
        @click.prevent="newFolder"
      ></a>
    </span>
  </div>
  <div
    v-bind="containerProps().attrs"
    v-on="containerProps().events"
    :ref="(el) => el && tree.registerElement(el)"
    id="folder-tree"
  >
    <template v-for="(item, idx) in items" :key="item.getId()">
      <div class="folder-item-wrapper">
        <span
          v-for="l in treeConnectors[idx].ancestors"
          :key="l"
          class="tree-guide"
          :style="{ left: levelLineLeft(l) + 'px' }"
        ></span>
        <span
          class="tree-vert"
          :class="{ 'tree-last': treeConnectors[idx].isLast }"
          :style="{ left: levelLineLeft(item.getItemMeta().level) + 'px' }"
        ></span>
        <span
          class="tree-horiz"
          :style="{ left: levelLineLeft(item.getItemMeta().level) + 'px' }"
        ></span>
        <div
          v-if="item.isRenaming()"
          class="folder-item renaming"
          :style="{ paddingLeft: levelIndent(item.getItemMeta().level) + 'px' }"
        >
          <span
            v-if="item.getItemData()?.has_children"
            class="tree-toggle"
          ></span>
          <span class="folder-icon" :class="getFolderIconClass(item)"></span>
          <input
            v-bind="vueRenameInputProps(item)"
            :ref="renameInputRef"
            class="folder-rename-input"
          />
        </div>
        <button
          v-else
          v-bind="itemProps(item).attrs"
          v-on="itemProps(item).events"
          :ref="(el) => el && item.registerElement(el)"
          :style="{ paddingLeft: levelIndent(item.getItemMeta().level) + 'px' }"
          :aria-disabled="
            item.getItemData()?.is_sponsored_root_folder || undefined
          "
          class="folder-item"
          :class="{
            selected: item.isSelected(),
            focused: item.isFocused(),
            expanded: item.isExpanded() && item.getItemData()?.has_children,
            'drag-target': item.isDragTarget?.(),
            'is-shared': item.getItemData()?.is_shared_folder,
            'is-disabled': item.getItemData()?.is_sponsored_root_folder,
          }"
        >
          <span
            v-if="item.getItemData()?.has_children"
            class="tree-toggle"
          ></span>
          <span class="folder-icon" :class="getFolderIconClass(item)"></span>
          {{ item.getItemName() }}
        </button>
      </div>
    </template>
    <div :style="tree.getDragLineStyle()" class="dragline" />
  </div>
</template>
