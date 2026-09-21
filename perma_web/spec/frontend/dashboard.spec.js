import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../../static/frontend/components/App.vue'
import Dialog from '../../static/frontend/components/Dialog.vue'
import FolderTree from '../../static/frontend/components/FolderTree.vue'
import { fetchDataOrError, useFetch } from '../../static/frontend/lib/data'
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

const setDashboardGlobals = () => {
  Object.assign(globalThis, {
    links_remaining: 4,
    is_nonpaying: false,
    is_individual: false,
    is_organization_user: true,
    is_registrar_user: false,
    is_sponsored_user: false,
    is_staff: false,
    link_creation_allowed: true,
    subscription_status: 'active',
    max_size: 100,
    urls: {archives: '/api/v1/archives/'},
    current_user: {top_level_folders: [personalFolder, organizationFolder]},
  })
}

describe('Vue dashboard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    setDashboardGlobals()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('mounts with Django-provided state and initializes the Pinia store', () => {
    const pinia = createPinia()
    const wrapper = mount(App, {
      global: {
        plugins: [pinia],
        stubs: {
          CreateLink: true,
          LinkBrowser: true,
          Toast: true,
        },
      },
    })
    const store = useGlobalStore(pinia)

    expect(wrapper.exists()).toBe(true)
    expect(store.linksRemaining).toBe(4)
    expect(store.linksRemainingStatus).toBe('metered')
    expect(store.userTypes).toEqual(['orgAffiliated'])
    expect(store.urls).toEqual({archives: '/api/v1/archives/'})
  })

  it('adds and expires toast state using deterministic timers', async () => {
    const store = useGlobalStore()
    vi.useFakeTimers()

    const toastPromise = store.addToast('Saved', 'success', 3000)
    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0]).toMatchObject({message: 'Saved', level: 'success'})

    await vi.advanceTimersByTimeAsync(3000)
    await toastPromise

    expect(store.toasts).toHaveLength(0)
  })

  it('adds CSRF and JSON data at the fetch boundary', async () => {
    document.cookie = 'csrftoken=token-value'
    const response = {ok: true, json: vi.fn().mockResolvedValue({objects: []})}
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response)

    const result = await fetchDataOrError('/archives/', {
      method: 'POST',
      data: {url: 'https://example.com'},
    })

    expect(result).toMatchObject({data: {objects: []}, error: null, response})
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/archives/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': 'token-value',
      },
      body: JSON.stringify({url: 'https://example.com'}),
    })
  })

  it('exposes API loading and error state', async () => {
    const response = {
      ok: false,
      status: 503,
      statusText: 'Unavailable',
      json: vi.fn().mockRejectedValue(new Error('not JSON')),
    }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(response)
    const request = useFetch('/archives/')

    const requestPromise = request.fetchData()
    expect(request.isLoading.value).toBe(true)
    await requestPromise

    expect(request.isLoading.value).toBe(false)
    expect(request.hasError.value).toBe(true)
    expect(request.error.value).toBe('Unavailable')
    expect(request.data.value).toBeNull()
  })

  it('opens and closes dialogs through its public contract', async () => {
    const handleClose = vi.fn()
    const wrapper = mount(Dialog, {props: {handleClose}})

    wrapper.vm.handleDialogOpen()
    expect(wrapper.get('dialog').element.open).toBe(true)

    await wrapper.get('dialog').trigger('keydown.esc')
    expect(handleClose).toHaveBeenCalledOnce()

    wrapper.vm.handleDialogClose()
    expect(wrapper.get('dialog').element.open).toBe(false)
  })

  it('translates a selected tree node into folder state', async () => {
    const pinia = createPinia()
    const treeApi = {
      getFolderTree: () => ({get_path: () => ['Organization Links', 'Research']}),
    }
    const wrapper = mount(FolderTree, {
      global: {
        plugins: [pinia],
        stubs: {
          JSTree: {
            name: 'JSTree',
            template: '<div />',
            methods: treeApi,
          },
        },
      },
    })
    const store = useGlobalStore(pinia)
    store.currentUser = {top_level_folders: [personalFolder, organizationFolder]}

    wrapper.getComponent({name: 'JSTree'}).vm.$emit('nodeSelect', {
      data: {
        organization_id: 9,
        sponsor_id: null,
        folder_id: 3,
        read_only: false,
      },
    })
    await flushPromises()

    expect(store.selectedFolder).toEqual({
      folderId: 3,
      orgId: 9,
      sponsorId: null,
      isReadOnly: false,
      isOutOfLinks: false,
      isPrivate: true,
      path: ['Organization Links', 'Research'],
    })
  })
})
