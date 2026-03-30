<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useGlobalStore } from '../stores/globalStore';
import { fetchDataOrError } from '../lib/data';
import { useTree } from '../composables/useTree';
import {
  asyncDataLoaderFeature,
  hotkeysCoreFeature,
  selectionFeature,
  dragAndDropFeature,
  renamingFeature,
} from '@headless-tree/core';

const globalStore = useGlobalStore();
const LOCAL_STORAGE_KEY = 'perma_selection';

const privateOrgIds = computed(() =>
  globalStore.currentUser.top_level_folders
    .filter(folder => folder.default_to_private)
    .map(folder => folder.organization)
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
  localStorage.setItem(key, typeof value === 'string' ? value : JSON.stringify(value));
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
    history.pushState(null, null, '?folder=' + folderIds.join('-'));
  }
  jsonLocalStorageSet(LOCAL_STORAGE_KEY, all);
}

function folderIdsFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('folder');
  if (!raw) return null;
  try {
    const ids = raw.split('-').map(s => parseInt(s, 10));
    ids.forEach(id => { if (isNaN(id)) throw new Error('Invalid folder id'); });
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

function cacheFolders(apiFolders) {
  for (const folder of apiFolders) {
    folderCache[String(folder.id)] = {
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
  }
}

// Pre-cache top-level folders from user object
cacheFolders(current_user.top_level_folders);

// --- Custom click behavior ---
// Clicking a closed folder expands it; clicking an already-selected
// open folder collapses it. Sponsored root folders toggle expand only.
const customClickBehavior = {
  itemInstance: {
    getProps: ({ tree, item, prev }) => ({
      ...prev?.(),
      onClick: (e) => {
        const itemId = item.getItemMeta().itemId;
        const data = item.getItemData();

        // Sponsored root folders: only toggle expand, never select
        if (data.is_sponsored_root_folder) {
          if (item.isExpanded()) {
            item.collapse();
          } else {
            item.expand();
          }
          return;
        }

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

        // Expand/collapse: expand if closed, collapse only if
        // clicking the already-selected folder
        if (item.isFolder()) {
          if (!item.isExpanded()) {
            item.expand();
          } else if (item.isSelected()) {
            item.collapse();
          }
        }

        item.setFocused();
        item.primaryAction();
        // Do NOT chain to prev?.()?.onClick?.(e) -- the core tree
        // feature's onClick has its own expand/collapse logic that
        // would immediately reverse what we just did.
      },
      onDblClick: () => {
        if (item.canRename()) {
          item.startRenaming();
        }
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
  const { ref, onDragOver, onDrop, ...attrs } = tree.getContainerProps();
  return { attrs, events: { dragover: onDragOver, drop: onDrop } };
}

function itemProps(item) {
  const {
    ref,
    onDragStart, onDragEnd, onDragEnter, onDragOver, onDragLeave, onDrop,
    onDblClick,
    ...attrs
  } = item.getProps();
  const events = {};
  if (onDragStart) events.dragstart = onDragStart;
  if (onDragEnd) events.dragend = onDragEnd;
  if (onDragEnter) events.dragenter = onDragEnter;
  if (onDragOver) events.dragover = onDragOver;
  if (onDragLeave) events.dragleave = onDragLeave;
  if (onDrop) events.drop = onDrop;
  if (onDblClick) events.dblclick = onDblClick;
  return { attrs, events };
}

function vueRenameInputProps(item) {
  const { onChange, ref: _ref, ...rest } = item.getRenameInputProps();
  return { ...rest, onInput: onChange };
}

function renameInputRef(el) {
  if (el) {
    el.focus();
    requestAnimationFrame(() => el.select());
  }
}

// --- Tree setup ---

const { tree, items } = useTree({
  rootItemId: 'root',
  getItemName: (item) => item.getItemData().name,
  isItemFolder: () => true,
  createLoadingItemData: () => ({ name: 'Loading...', _loading: true }),
  indent: 20,
  canReorder: false,
  dataLoader: {
    getItem: (itemId) => {
      if (itemId === 'root') {
        return Promise.resolve({ name: 'Root', _isRoot: true });
      }
      const cached = folderCache[itemId];
      if (cached) return Promise.resolve(cached);
      return Promise.resolve({ name: 'Loading...', _loading: true });
    },
    getChildrenWithData: (itemId) => {
      if (itemId === 'root') {
        return Promise.resolve(
          current_user.top_level_folders.map(f => ({
            id: String(f.id),
            data: folderCache[String(f.id)] || {
              id: f.id,
              name: f.name,
              organization: f.organization,
              sponsored_by: f.sponsored_by,
              is_sponsored_root_folder: f.is_sponsored_root_folder,
              read_only: f.read_only,
              has_children: f.has_children,
              parent: f.parent,
              is_shared_folder: !!(f.organization && !f.parent),
            },
          }))
        );
      }
      return fetchDataOrError(`/folders/${itemId}/folders/?limit=500`).then(
        ({ data, error }) => {
          if (error || !data?.objects) return [];
          cacheFolders(data.objects);
          return data.objects.map(f => ({
            id: String(f.id),
            data: folderCache[String(f.id)],
          }));
        }
      );
    },
  },

  // --- Drag and drop (folder-to-folder) ---
  canDrag: (dragItems) => {
    for (const item of dragItems) {
      const data = item.getItemData();
      if (!data || data._isRoot || data._loading) return false;
      if (data.is_sponsored_root_folder) {
        globalStore.addToast('Sponsored folders cannot be moved.', 'warning');
        return false;
      }
      if (data.is_shared_folder) {
        globalStore.addToast('Shared folders cannot be moved.', 'warning');
        return false;
      }
      const parent = item.getParent();
      if (!parent || parent.getItemMeta().itemId === 'root') {
        globalStore.addToast('Top-level folders cannot be moved.', 'warning');
        return false;
      }
    }
    return true;
  },
  canDrop: (dragItems, target) => {
    const targetData = target.item.getItemData();
    if (!targetData || targetData._isRoot || targetData._loading) return false;
    if (targetData.is_sponsored_root_folder) return false;
    if (targetData.read_only) return false;
    return true;
  },
  onDrop: async (dragItems, target) => {
    const newParentId = target.item.getItemMeta().itemId;
    for (const item of dragItems) {
      const folderId = item.getItemMeta().itemId;
      const oldParent = item.getParent();
      const { error } = await fetchDataOrError(
        `/folders/${newParentId}/folders/${folderId}/`,
        { method: 'PUT' }
      );
      if (error) {
        globalStore.addToast('Error moving folder. Please try again.', 'error');
        return;
      }
      // Invalidate both old and new parent's children
      if (oldParent) oldParent.invalidateChildrenIds();
      target.item.invalidateChildrenIds();
    }
    tree.rebuildTree();
  },

  // --- Foreign DnD (links dragged from LinkList) ---
  canDropForeignDragObject: (dataTransfer, target) => {
    const targetData = target.item.getItemData();
    if (!targetData || targetData._isRoot || targetData._loading) return false;
    if (targetData.is_sponsored_root_folder) return false;
    if (targetData.read_only) return false;
    return true;
  },
  canDragForeignDragObjectOver: (dataTransfer, target) => {
    const targetData = target.item.getItemData();
    if (!targetData || targetData._isRoot || targetData._loading) return false;
    if (targetData.is_sponsored_root_folder) return false;
    if (targetData.read_only) return false;
    return true;
  },
  onDropForeignDragObject: async (dataTransfer, target) => {
    const linkGuid = dataTransfer.getData('application/x-perma-link');
    if (!linkGuid) return;
    const folderId = target.item.getItemMeta().itemId;
    const { data, error } = await fetchDataOrError(
      `/folders/${folderId}/archives/${linkGuid}/`,
      { method: 'PUT' }
    );
    if (error) {
      globalStore.addToast('Error moving link. Please try again.', 'error');
      return;
    }
    if (data?.links_remaining !== undefined) {
      globalStore.linksRemaining = data.links_remaining;
    }
    // Remove the link from the current link list display
    globalStore.components.linkList?.fetchLinks();
  },

  // --- Renaming ---
  canRename: (item) => {
    const data = item.getItemData();
    if (!data || data._isRoot || data._loading) return false;
    if (data.is_sponsored_root_folder) return false;
    if (data.is_shared_folder) return false;
    const parent = item.getParent();
    if (!parent || parent.getItemMeta().itemId === 'root') return false;
    return true;
  },
  onRename: async (item, newName) => {
    const folderId = item.getItemMeta().itemId;
    const { error } = await fetchDataOrError(`/folders/${folderId}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName }),
    });
    if (error) {
      globalStore.addToast('Error renaming folder. Please try again.', 'error');
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

// --- Selection handling ---

function buildPathForItem(item) {
  const path = [];
  let current = item;
  while (current) {
    const id = current.getItemMeta().itemId;
    if (id === 'root') break;
    const data = current.getItemData();
    if (data?.name) path.unshift(data.name);
    current = current.getParent();
  }
  return path;
}

function buildFolderIdsPath(item) {
  const ids = [];
  let current = item;
  while (current) {
    const id = current.getItemMeta().itemId;
    if (id === 'root') break;
    ids.unshift(parseInt(id, 10));
    current = current.getParent();
  }
  return ids;
}

function updateSelectedFolderFromItem(item) {
  const data = item.getItemData();
  if (!data || data._isRoot || data._loading) return;
  if (data.is_sponsored_root_folder) return;

  const folderId = parseInt(item.getItemMeta().itemId, 10);
  const orgId = data.organization || '';
  const sponsorId = data.sponsored_by || '';
  const isReadOnly = !!data.read_only;
  const isPrivate = orgId ? privateOrgIds.value.includes(orgId) : false;
  const isOutOfLinks = !isReadOnly && !sponsorId && !orgId && !globalStore.linkCreationAllowed;
  const path = buildPathForItem(item);
  const folderIds = buildFolderIdsPath(item);

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
    for (const folderId of savedIds) {
      try {
        const { data, error } = await fetchDataOrError(
          `/folders/${folderId}/folders/?limit=500`
        );
        if (!error && data?.objects) {
          cacheFolders(data.objects);
        }
      } catch {
        break;
      }
    }
    // Expand the saved path
    tree.applySubStateUpdate('expandedItems', () => savedIds.map(String));
  }

  // Select saved folder after tree is ready
  setTimeout(() => {
    selectInitialFolder();
  }, 0);
});

onBeforeUnmount(() => {
  globalStore.components.folderTree = null;
});

function selectInitialFolder() {
  let folderToSelect = getSavedFolderId();
  if (!folderToSelect && current_user.top_level_folders.length === 1) {
    folderToSelect = current_user.top_level_folders[0].id;
  }
  if (folderToSelect) {
    const itemId = String(folderToSelect);
    try {
      const item = tree.getItemInstance(itemId);
      if (item) {
        tree.setSelectedItems([itemId]);
        item.setFocused();
        updateSelectedFolderFromItem(item);
      }
    } catch {
      // Item may not be loaded yet; this is OK on first load
    }
  }
}

// --- Toolbar actions ---

async function newFolder() {
  const selectedItems = tree.getSelectedItems();
  if (!selectedItems.length) {
    globalStore.addToast('Please select a folder first.', 'warning');
    return;
  }
  const parent = selectedItems[0];
  const parentId = parent.getItemMeta().itemId;
  const { data, error } = await fetchDataOrError(
    `/folders/${parentId}/folders/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'New Folder' }),
    }
  );
  if (error) {
    globalStore.addToast('Error creating folder. Please try again.', 'error');
    return;
  }
  // Cache the new folder
  folderCache[String(data.id)] = {
    id: data.id,
    name: data.name || 'New Folder',
    organization: data.organization,
    sponsored_by: data.sponsored_by,
    is_sponsored_root_folder: false,
    read_only: false,
    has_children: false,
    parent: parseInt(parentId, 10),
    is_shared_folder: false,
  };
  parent.invalidateChildrenIds();
  if (!parent.isExpanded()) parent.expand();
  // After re-fetch, start renaming
  setTimeout(() => {
    try {
      const newItem = tree.getItemInstance(String(data.id));
      if (newItem) {
        tree.setSelectedItems([String(data.id)]);
        newItem.setFocused();
        newItem.startRenaming();
      }
    } catch {
      // Item may not be available yet
    }
  }, 300);
}

function editFolder() {
  const selectedItems = tree.getSelectedItems();
  if (!selectedItems.length) return;
  const item = selectedItems[0];
  const data = item.getItemData();
  if (!data || data._isRoot || data._loading) return;
  if (data.is_sponsored_root_folder) {
    globalStore.addToast('Sponsored folders cannot be renamed.', 'warning');
    return;
  }
  if (data.is_shared_folder) {
    globalStore.addToast('Shared folders cannot be renamed.', 'warning');
    return;
  }
  const parent = item.getParent();
  if (!parent || parent.getItemMeta().itemId === 'root') {
    globalStore.addToast('Top-level folders cannot be renamed.', 'warning');
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

  if (!confirm(`Really delete folder '${data.name}'?`)) return;

  const folderId = item.getItemMeta().itemId;
  const parent = item.getParent();
  const { error } = await fetchDataOrError(`/folders/${folderId}/`, {
    method: 'DELETE',
  });
  if (error) {
    globalStore.addToast('Error deleting folder. Please try again.', 'error');
    return;
  }
  delete folderCache[folderId];
  if (parent) {
    parent.invalidateChildrenIds();
    const parentId = parent.getItemMeta().itemId;
    if (parentId !== 'root') {
      tree.setSelectedItems([parentId]);
      parent.setFocused();
      updateSelectedFolderFromItem(parent);
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
      while (parent && parent.getItemMeta().itemId !== 'root') {
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
  const orgId = folderCache[idStr]?.organization || '';
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
      text: (level > 1 ? '\u2514'.padStart(level, '\u00A0') + ' ' : '') + data.name,
      selected: parseInt(item.getItemMeta().itemId, 10) === globalStore.selectedFolder.folderId,
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
      <a href="#" class="pull-right delete-folder icon-trash" aria-label="Delete Selected Folder"
         title="Delete Selected Folder" @click.prevent="deleteFolder"></a>
      <a href="#" class="pull-right edit-folder icon-edit" aria-label="Rename Selected Folder"
         title="Rename Selected Folder" @click.prevent="editFolder"></a>
      <a href="#" class="pull-right new-folder icon-plus" aria-label="New Folder" title="New Folder"
         @click.prevent="newFolder"></a>
    </span>
  </div>
  <div v-bind="containerProps().attrs" v-on="containerProps().events"
       :ref="(el) => el && tree.registerElement(el)" id="folder-tree">
    <template v-for="item in items" :key="item.getId()">
      <template v-if="item.isRenaming()">
        <div class="folder-item renaming"
             :style="{ paddingLeft: item.getItemMeta().level * 20 + 'px' }">
          <input v-bind="vueRenameInputProps(item)" :ref="renameInputRef" class="folder-rename-input" />
        </div>
      </template>
      <template v-else>
        <button
          v-bind="itemProps(item).attrs"
          v-on="itemProps(item).events"
          :ref="(el) => el && item.registerElement(el)"
          :style="{ paddingLeft: item.getItemMeta().level * 20 + 'px' }"
          class="folder-item"
          :class="{
            selected: item.isSelected(),
            focused: item.isFocused(),
            expanded: item.isExpanded(),
            'drag-target': item.isDragTarget?.(),
            'is-shared': item.getItemData()?.is_shared_folder,
            'is-disabled': item.getItemData()?.is_sponsored_root_folder,
          }"
        >
          <span v-if="item.getItemData()?.is_shared_folder" class="folder-icon icon-sitemap"></span>
          <span v-else-if="item.isExpanded()" class="folder-icon icon-folder-open-alt"></span>
          <span v-else class="folder-icon icon-folder-close-alt"></span>
          {{ item.getItemName() }}
          <span v-if="item.isLoading()" class="loading-indicator">...</span>
        </button>
      </template>
    </template>
    <div :style="tree.getDragLineStyle()" class="dragline" />
  </div>
</template>
