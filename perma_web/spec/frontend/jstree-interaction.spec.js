// JSTree.vue is the sole jsTree consumer in Perma, and jsTree is the only reason jQuery cannot
// move to 4.0.0 without an npm `overrides` entry: jstree@3.3.17 declares
// `peerDependencies: { jquery: "^3.5.0" }`, which excludes jQuery 4. These tests drive the real
// jstree/jQuery event wiring under jsdom, against the CURRENT stack (jquery 3.7.1, jstree 3.3.16),
// so they are the evidence that decides whether overriding that peer range at sub-batch 5C is
// safe -- the jQuery 4 and jstree 3.3.17 upgrades must cross this tripwire, not a guess.
// See .plans/plan_dependency-upgrade-roadmap-5.md, sub-batch 5A, item 2.
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import FolderTree from '../../static/frontend/components/FolderTree.vue'
import JSTree from '../../static/frontend/components/JSTree.vue'
import { useGlobalStore } from '../../static/frontend/stores/globalStore'

// ready.jstree fires from a genuine setTimeout(0) inside jstree's own core (jstree.js ~line 812),
// so waiting on it is the only reliable way to know the initial (async) load has settled.
const waitForReady = () => new Promise((resolve) => {
  $(window).one('folderTree.ready', resolve)
})

const leafFolder = {
  id: 10, name: 'Leaf Folder', organization: null, sponsored_by: null,
  is_sponsored_root_folder: false, read_only: false, has_children: false,
}
const branchFolder = {
  id: 20, name: 'Branch Folder', organization: null, sponsored_by: null,
  is_sponsored_root_folder: false, read_only: false, has_children: true,
}
const childFolder = {
  id: 21, name: 'Child Folder', organization: null, sponsored_by: null,
  is_sponsored_root_folder: false, read_only: false, has_children: false,
}

// jstree's `data` option is a function here (JSTree.vue's handleShowFoldersEvent), which calls
// through to $.ajax for anything beyond the preloaded top-level folders. Mock at that boundary,
// the same seam APIModule.request itself sits on.
const respondWithFolders = (objects) =>
  vi.spyOn($, 'ajax').mockImplementation(() => $.Deferred().resolve({objects}).promise())

beforeEach(() => {
  globalThis.current_user = {top_level_folders: [leafFolder, branchFolder]}
  globalThis.api_path = '/api/v1'
  window.history.pushState(null, null, '?')
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('JSTree.vue jsTree interaction', () => {
  it('mounts, becomes ready, and $.jstree.reference resolves to the same usable instance the component exposes', async () => {
    const wrapper = mount(JSTree)
    await waitForReady()

    const el = wrapper.get('#folder-tree').element
    const ref = $.jstree.reference(el)

    expect(ref).toBeTruthy()
    expect(typeof ref.select_node).toBe('function')
    expect(wrapper.vm.getFolderTree()).toBe(ref)
    expect(wrapper.findAll('a.jstree-anchor').map((a) => a.text())).toEqual(['Leaf Folder', 'Branch Folder'])
  })

  it('fires load_node.jstree while the root loads, then ready.jstree once loading settles', async () => {
    const loadStatuses = []
    const wrapper = mount(JSTree)
    $(wrapper.get('#folder-tree').element).on('load_node.jstree', (e, data) => loadStatuses.push(data.status))

    await waitForReady()

    expect(loadStatuses).toEqual([true])
  })

  it('selects a node on click, emitting nodeSelect with the node and marking it aria-selected', async () => {
    const wrapper = mount(JSTree)
    await waitForReady()

    const anchor = wrapper.findAll('a.jstree-anchor')[0]
    await anchor.trigger('click')

    expect(anchor.attributes('aria-selected')).toBe('true')
    const [[selectedNode]] = wrapper.emitted('nodeSelect')
    expect(selectedNode.text).toBe('Leaf Folder')
    expect(selectedNode.data.folder_id).toBe(10)
  })

  it('selects a node via keyboard Enter on its anchor, the same as a click', async () => {
    const wrapper = mount(JSTree)
    await waitForReady()

    const anchor = wrapper.findAll('a.jstree-anchor')[0]
    // jstree's own keydown binding reads e.which (jstree.js `_kbevent_to_func`); VTU's DOM
    // trigger() can't set that read-only property on a native event, so dispatch a jQuery.Event.
    $(anchor.element).trigger($.Event('keydown', {which: 13}))

    expect(anchor.attributes('aria-selected')).toBe('true')
    expect(wrapper.emitted('nodeSelect')).toHaveLength(1)
  })

  it('deselects a node through the jsTree instance, emitting nodeUnselect with the node', async () => {
    const wrapper = mount(JSTree)
    await waitForReady()
    const tree = wrapper.vm.getFolderTree()
    const nodeId = wrapper.get('li[data-folder_id="10"]').element.id

    tree.select_node(nodeId)
    tree.deselect_node(nodeId)

    const [[deselectedNode]] = wrapper.emitted('nodeUnselect')
    expect(deselectedNode.text).toBe('Leaf Folder')
  })

  it('tracks hover and dehover via mouseenter/mouseleave, toggling the jstree-hovered class jstree itself owns', async () => {
    const wrapper = mount(JSTree)
    await waitForReady()
    const anchor = wrapper.findAll('a.jstree-anchor')[0]

    $(anchor.element).trigger('mouseenter')
    expect(anchor.classes()).toContain('jstree-hovered')

    $(anchor.element).trigger('mouseleave')
    expect(anchor.classes()).not.toContain('jstree-hovered')
  })

  it('opens a closed folder lazily, fetching its children through the API, firing after_open.jstree and nodeExpand', async () => {
    respondWithFolders([childFolder])
    const wrapper = mount(JSTree)
    await waitForReady()
    const tree = wrapper.vm.getFolderTree()
    const nodeId = wrapper.get('li[data-folder_id="20"]').element.id

    tree.open_node(nodeId, null, false) // animation=false: assert the wiring, not jQuery's slideDown timing
    await vi.waitFor(() => {
      if (!wrapper.emitted('nodeExpand')) throw new Error('after_open.jstree has not fired yet')
    })

    expect(wrapper.get(`#${nodeId}`).classes()).toContain('jstree-open')
    expect(wrapper.find('li[data-folder_id="21"]').exists()).toBe(true) // lazily-loaded child now in the DOM
    const [[expandedNode]] = wrapper.emitted('nodeExpand')
    expect(expandedNode.text).toBe('Branch Folder')
  })

  it('closes an open folder, firing after_close.jstree and nodeCollapse', async () => {
    respondWithFolders([childFolder])
    const wrapper = mount(JSTree)
    await waitForReady()
    const tree = wrapper.vm.getFolderTree()
    const nodeId = wrapper.get('li[data-folder_id="20"]').element.id
    tree.open_node(nodeId, null, false)
    await vi.waitFor(() => {
      if (!wrapper.emitted('nodeExpand')) throw new Error('not open yet')
    })

    tree.close_node(nodeId, false)
    await vi.waitFor(() => {
      if (!wrapper.emitted('nodeCollapse')) throw new Error('after_close.jstree has not fired yet')
    })

    expect(wrapper.get(`#${nodeId}`).classes()).toContain('jstree-closed')
    const [[collapsedNode]] = wrapper.emitted('nodeCollapse')
    expect(collapsedNode.text).toBe('Branch Folder')
  })

  // Pre-existing defect, not fixed here: selectSavedFolder() (JSTree.vue) calls
  // folderTree.refresh(false, callback) and, on the very next line, dereferences
  // getNodeByFolderID(...) as though refresh() had already completed. jsTree's own data loading
  // is asynchronous (real production folders come from $.ajax), so refresh() has not repopulated
  // the model by the time that next line runs, and `node` is still null:
  // `node.state.selected = true` throws a TypeError. This is exactly the "Sponsored Folder ...
  // not previously been loaded" case the component's own comment names -- the comment's belief
  // that the empty refresh callback "lets the node get selected after the refresh" does not hold;
  // nothing in the code waits for that callback. jsTree's "types" plugin then replays the same
  // load via a real (unmockable-after-import) setImmediate, which re-enters selectSavedFolder()
  // and throws again, asynchronously and uncaught, unless the saved-folder state is cleared first.
  it('selecting a saved folder that was never loaded refreshes the tree and throws synchronously (suspected pre-existing defect)', async () => {
    respondWithFolders([])
    const wrapper = mount(JSTree)
    await waitForReady()

    expect(() => wrapper.vm.handleSelectionChange({orgId: null, folderId: [999]}))
      .toThrow(TypeError)

    // Defuse jstree's async replay (see comment above): selectSavedFolder() re-reads the saved
    // folder from localStorage/URL on every load_node.jstree, including jstree's own deferred
    // retrigger. With nothing saved to chase, that replay returns quietly instead of crashing
    // again outside any try/catch this test could otherwise wrap around it.
    localStorage.clear()
    window.history.pushState(null, null, '?')
    await new Promise((resolve) => setImmediate(resolve))
    await new Promise((resolve) => setImmediate(resolve))
    await new Promise((resolve) => setTimeout(resolve, 10))
  })
})

describe('FolderTree.vue: get_path as consumed through the store', () => {
  const configureStore = () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useGlobalStore(pinia)
    store.currentUser = {top_level_folders: [leafFolder, branchFolder]}
    store.linkCreationAllowed = true
    return {pinia, store}
  }

  it('selecting a top-level folder sets selectedFolder.path from jstree get_path()', async () => {
    const {pinia, store} = configureStore()
    const wrapper = mount(FolderTree, {global: {plugins: [pinia]}})
    await waitForReady()

    const anchor = wrapper.findAll('a.jstree-anchor')[1] // Branch Folder
    await anchor.trigger('click')

    expect(store.selectedFolder.path).toEqual(['Branch Folder'])
    expect(store.selectedFolder.folderId).toBe(20)
  })

  it('selecting a nested folder returns the full name path, root to leaf', async () => {
    respondWithFolders([childFolder])
    const {pinia, store} = configureStore()
    const wrapper = mount(FolderTree, {global: {plugins: [pinia]}})
    await waitForReady()
    const tree = wrapper.findComponent(JSTree).vm.getFolderTree()
    const parentId = wrapper.get('li[data-folder_id="20"]').element.id
    tree.open_node(parentId, null, false)
    await vi.waitFor(() => {
      if (!wrapper.find('li[data-folder_id="21"]').exists()) throw new Error('child not loaded yet')
    })

    const childAnchor = wrapper.get('li[data-folder_id="21"] > a.jstree-anchor')
    await childAnchor.trigger('click')

    expect(store.selectedFolder.path).toEqual(['Branch Folder', 'Child Folder'])
  })
})
