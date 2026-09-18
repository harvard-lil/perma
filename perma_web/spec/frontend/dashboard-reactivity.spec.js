import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CreateLink from '../../static/frontend/components/CreateLink.vue'
import FolderSelect from '../../static/frontend/components/FolderSelect.vue'
import LinkList from '../../static/frontend/components/LinkList.vue'
import { useGlobalStore } from '../../static/frontend/stores/globalStore'

const personalFolder = {
  id: 1,
  name: 'Personal Links',
  organization: null,
  sponsored_by: null,
  default_to_private: false,
  read_only: false,
}

const organizationFolder = {
  id: 2,
  name: 'Organization Links',
  organization: 9,
  sponsored_by: null,
  default_to_private: true,
  read_only: false,
}

const response = (data, options = {}) => ({
  ok: options.ok ?? true,
  status: options.status ?? 200,
  statusText: options.statusText ?? 'OK',
  json: vi.fn().mockResolvedValue(data),
})

const configureStore = () => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useGlobalStore(pinia)
  store.currentUser = {top_level_folders: [personalFolder, organizationFolder]}

  return {pinia, store}
}

describe('dashboard reactivity, watchers, and template refs', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('keeps FolderSelect reactive to a storeToRefs-destructured selectedFolder mutated after mount', async () => {
    const {pinia, store} = configureStore()
    const wrapper = mount(FolderSelect, {global: {plugins: [pinia]}})

    expect(wrapper.get('button').text()).toContain('Please select a folder')

    store.selectedFolder = {
      folderId: 2,
      orgId: 9,
      sponsorId: null,
      path: ['Organization Links'],
      isPrivate: true,
      isReadOnly: false,
      isOutOfLinks: false,
    }
    await flushPromises()

    expect(wrapper.get('button').text()).toContain('Organization Links')
  })

  it('refetches through the [selectedFolder, query] watcher when the store folder changes', async () => {
    const {pinia, store} = configureStore()
    store.selectedFolder = {
      folderId: 1, orgId: null, sponsorId: null, path: ['Personal Links'],
      isPrivate: false, isReadOnly: false, isOutOfLinks: false,
    }
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({objects: []}))
    const wrapper = mount(LinkList, {global: {plugins: [pinia]}})

    // onMounted(fetchLinks) is commented out in LinkList.vue, so mounting alone must not fetch
    expect(fetchMock).not.toHaveBeenCalled()

    store.selectedFolder = {
      folderId: 2, orgId: 9, sponsorId: null, path: ['Organization Links'],
      isPrivate: true, isReadOnly: false, isOutOfLinks: false,
    }
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/folders/2/archives/?q=&limit=20&offset=0',
      {headers: {'X-CSRFToken': undefined}},
    )
    // relies on the same storeToRefs destructuring: the header text tracks the new folder too
    expect(wrapper.text()).toContain('Organization Links Links')
  })

  it('nulls the store linkList registration when LinkList unmounts', () => {
    const {pinia, store} = configureStore()
    store.selectedFolder = {
      folderId: 1, orgId: null, sponsorId: null, path: ['Personal Links'],
      isPrivate: false, isReadOnly: false, isOutOfLinks: false,
    }
    const wrapper = mount(LinkList, {global: {plugins: [pinia]}})

    expect(store.components.linkList).toEqual({fetchLinks: expect.any(Function)})

    wrapper.unmount()

    expect(store.components.linkList).toBeNull()
  })

  it('stops CreateLink capture-status polling once unmounted', async () => {
    vi.useFakeTimers()
    const {pinia, store} = configureStore()
    store.selectedFolder = {
      folderId: 1, orgId: null, sponsorId: null, path: ['Personal Links'],
      isPrivate: false, isReadOnly: false, isOutOfLinks: false,
    }
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({guid: 'ABCD-1234'}))
      .mockResolvedValue(response({step_count: 1, status: 'in_progress'}))
    const wrapper = mount(CreateLink, {global: {plugins: [pinia]}})

    await wrapper.get('#rawUrl').setValue('https://example.com')
    await wrapper.get('#addlink').trigger('click')
    await vi.advanceTimersByTimeAsync(0) // let the POST resolve and the immediate progress poll fire
    expect(fetchMock).toHaveBeenCalledTimes(2)

    await vi.advanceTimersByTimeAsync(2000) // one setInterval tick while still mounted
    expect(fetchMock).toHaveBeenCalledTimes(3)

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(6000) // several more ticks worth, post-unmount

    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('opens the batch dialog end to end through the batchDialogRef template ref', async () => {
    const {pinia, store} = configureStore()
    store.selectedFolder = {
      folderId: 1, orgId: null, sponsorId: null, path: ['Personal Links'],
      isPrivate: false, isReadOnly: false, isOutOfLinks: false,
    }
    const wrapper = mount(CreateLink, {global: {plugins: [pinia]}})

    expect(wrapper.get('dialog').element.open).toBe(false)

    await wrapper.get('#create-batch-links button').trigger('click')

    expect(wrapper.get('dialog').element.open).toBe(true)
  })

  it("returns focus to FolderSelect's button via selectButtonRef when Escape closes the listbox", async () => {
    const {pinia, store} = configureStore()
    store.components.jstree = {handleSelectionChange: vi.fn()}
    // `attachTo` calls app.onUnmount(), a Vue 3.5+ API not present on this project's pinned Vue
    // 3.4.21 -- appending the mounted element manually gets real DOM attachment without it.
    const wrapper = mount(FolderSelect, {global: {plugins: [pinia]}})
    document.body.appendChild(wrapper.element)

    // keyboard open path focuses the first item via selectListRef, unlike a plain click
    await wrapper.get('button').trigger('keydown.down')
    expect(document.activeElement).toBe(wrapper.get('[data-index="0"]').element)

    await wrapper.get('[role="listbox"]').trigger('keydown.esc')

    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
    expect(document.activeElement).toBe(wrapper.get('button').element)

    wrapper.unmount()
  })
})

describe('globalStore async actions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('setFromAPI assigns the fetched objects on success', async () => {
    const store = useGlobalStore()
    const objects = [{id: 1, name: 'Sponsor A'}]

    await store.setFromAPI('sponsoredFolders', Promise.resolve({data: {objects}, error: null}))

    expect(store.sponsoredFolders).toEqual(objects)
    expect(store.fetchErrorMessage).toBe('')
  })

  it('setFromAPI sets fetchErrorMessage on failure, and overwrites the target with whatever .objects the error body has', async () => {
    const store = useGlobalStore()
    store.sponsoredFolders = [{id: 99, name: 'stale'}]

    // fetchDataOrError still resolves {data, error} on a handled API error (e.g. a JSON error body)
    await store.setFromAPI('sponsoredFolders', Promise.resolve({data: {detail: 'Not found'}, error: 'Not Found'}))

    expect(store.fetchErrorMessage).toBe('Not Found')
    expect(store.sponsoredFolders).toBeUndefined()
  })

  it('setUserTypesFromGlobals fetches sponsored folders for a sponsored user', async () => {
    const sponsoredRootFolder = {id: 3, is_sponsored_root_folder: true}
    globalThis.current_user = {top_level_folders: [personalFolder, sponsoredRootFolder]}
    const objects = [{id: 5, name: 'Sponsor A'}]
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({objects}))
    const store = useGlobalStore()

    store.setUserTypesFromGlobals(false, false, false, true, false)
    await flushPromises()

    expect(store.userTypes).toEqual(['sponsored'])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/folders/3/folders/',
      {headers: {'X-CSRFToken': undefined}},
    )
    expect(store.sponsoredFolders).toEqual(objects)
  })
})

describe("CreateLink's useStorage-persisted tools reminder", () => {
  it('shows the reminder by default and persists dismissal to localStorage', async () => {
    const {pinia} = configureStore()
    const wrapper = mount(CreateLink, {global: {plugins: [pinia]}})

    expect(wrapper.find('#browser-tools-message').exists()).toBe(true)

    await wrapper.get('.close-browser-tools').trigger('click')

    expect(wrapper.find('#browser-tools-message').exists()).toBe(false)
    expect(localStorage.getItem('perma_tools_reminder')).toBe('true')
  })

  it('hides the reminder on a fresh mount when a prior dismissal is already persisted', () => {
    localStorage.setItem('perma_tools_reminder', 'true')
    const {pinia} = configureStore()
    const wrapper = mount(CreateLink, {global: {plugins: [pinia]}})

    expect(wrapper.find('#browser-tools-message').exists()).toBe(false)
  })
})
