import { flushPromises, mount } from '@vue/test-utils'
import { useInfiniteScroll } from '@vueuse/core'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import CreateLinkBatch from '../../static/frontend/components/CreateLinkBatch.vue'
import FolderSelect from '../../static/frontend/components/FolderSelect.vue'
import LinkList from '../../static/frontend/components/LinkList.vue'
import UploadForm from '../../static/frontend/components/UploadForm.vue'
import { useGlobalStore } from '../../static/frontend/stores/globalStore'

// JSDOM reports zero scroll geometry, so the real composable treats the list as
// already scrolled to the bottom and fires from mount. Record the registration
// instead and drive the callback explicitly.
vi.mock('@vueuse/core', async (importOriginal) => {
  const original = await importOriginal()

  return {...original, useInfiniteScroll: vi.fn()}
})

const infiniteScrollRegistration = () => {
  const [target, onLoadMore, options] = vi.mocked(useInfiniteScroll).mock.calls.at(-1)

  return {target, onLoadMore, options}
}

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

const link = (guid) => ({
  guid,
  title: `Link ${guid}`,
  description: '',
  notes: '',
  url: `https://example.com/${guid}`,
  archive_timestamp: '2020-01-01T00:00:00Z',
  creation_timestamp: '2020-01-01T00:00:00Z',
  expiration_date: null,
  captures: [],
  is_private: false,
  default_to_screenshot_view: false,
  created_by: {full_name: 'Test User'},
})

const configureStore = (folderId = 1) => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useGlobalStore(pinia)

  store.currentUser = {top_level_folders: [personalFolder, organizationFolder]}
  store.selectedFolder = {
    folderId,
    orgId: null,
    sponsorId: null,
    path: folderId ? ['Personal Links'] : [],
    isPrivate: false,
    isReadOnly: false,
    isOutOfLinks: false,
  }

  return {pinia, store}
}

describe('dashboard interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders an initial page and appends later pages through the link-list refresh contract', async () => {
    const {pinia} = configureStore()
    const firstPage = Array.from({length: 20}, (_, index) => link(`first-${index}`))
    const secondPage = Array.from({length: 20}, (_, index) => link(`second-${index}`))
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({objects: firstPage}))
      .mockResolvedValueOnce(response({objects: secondPage}))
    const wrapper = mount(LinkList, {global: {plugins: [pinia]}})

    await wrapper.vm.fetchLinks()
    await wrapper.vm.fetchLinks(true)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/v1/folders/1/archives/?q=&limit=20&offset=0',
      {headers: {'X-CSRFToken': undefined}},
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/folders/1/archives/?q=&limit=20&offset=20',
      {headers: {'X-CSRFToken': undefined}},
    )
    expect(wrapper.findAll('.item-container._isExpandable')).toHaveLength(40)
    expect(wrapper.text()).toContain('Link first-0')
    expect(wrapper.text()).toContain('Link second-19')
  })

  it('appends the next page from the infinite-scroll callback and stops on the last page', async () => {
    const {pinia} = configureStore()
    const fullPage = Array.from({length: 20}, (_, index) => link(`first-${index}`))
    const lastPage = Array.from({length: 5}, (_, index) => link(`second-${index}`))
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({objects: fullPage}))
      .mockResolvedValueOnce(response({objects: lastPage}))
    const wrapper = mount(LinkList, {global: {plugins: [pinia]}})

    const {target, onLoadMore, options} = infiniteScrollRegistration()
    expect(target.value).toBe(wrapper.get('.container.item-rows').element)
    expect(options).toEqual({distance: 10})

    await wrapper.vm.fetchLinks()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    await onLoadMore()
    await flushPromises()

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/folders/1/archives/?q=&limit=20&offset=20',
      {headers: {'X-CSRFToken': undefined}},
    )
    expect(wrapper.findAll('.item-container._isExpandable')).toHaveLength(25)

    // a short page clears hasMore, so further scrolling must not request again
    await onLoadMore()
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('ignores the infinite-scroll callback while a page request is in flight', async () => {
    const {pinia} = configureStore()
    const fullPage = Array.from({length: 20}, (_, index) => link(`first-${index}`))
    let releaseFirstPage
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockReturnValueOnce(new Promise((resolve) => { releaseFirstPage = resolve }))
    const wrapper = mount(LinkList, {global: {plugins: [pinia]}})

    const {onLoadMore} = infiniteScrollRegistration()
    const firstPage = wrapper.vm.fetchLinks()

    await onLoadMore()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    releaseFirstPage(response({objects: fullPage}))
    await firstPage
    await flushPromises()

    await onLoadMore()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('keeps the folder selector keyboard and click path routed through jsTree', async () => {
    const {pinia, store} = configureStore()
    const handleSelectionChange = vi.fn()
    store.components.jstree = {handleSelectionChange}
    const wrapper = mount(FolderSelect, {global: {plugins: [pinia]}})

    await wrapper.get('button').trigger('keydown.down')
    expect(wrapper.get('[role="listbox"]').exists()).toBe(true)

    await wrapper.get('[data-index="1"]').trigger('click')

    expect(handleSelectionChange).toHaveBeenCalledWith({orgId: 9, folderId: 2})
    expect(wrapper.find('[role="listbox"]').exists()).toBe(false)
  })

  it('blocks an empty batch submission with visible URL and folder errors', async () => {
    const {pinia} = configureStore('')
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    await wrapper.get('.form-buttons .btn').trigger('click')

    expect(fetchMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Missing URLs: please submit a list of valid URLs.')
    expect(wrapper.text()).toContain('No folder selected: please select a folder.')
  })

  it('submits trimmed batch URLs, refreshes the list, and displays completed batch details', async () => {
    const {pinia, store} = configureStore()
    store.components.linkList = {fetchLinks: vi.fn()}
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({id: 41}))
      .mockResolvedValueOnce(response({
        target_folder: {name: 'Personal Links'},
        capture_jobs: [{
          guid: 'ABCD-1234',
          status: 'completed',
          message: '{}',
          step_count: 6,
          submitted_url: 'https://example.com/one',
          title: 'First link',
          user_deleted: false,
        }],
      }))
    const wrapper = mount(CreateLinkBatch, {global: {plugins: [pinia]}})

    wrapper.vm.handleOpen()
    expect(wrapper.get('dialog').element.open).toBe(true)
    await wrapper.get('#userSubmittedLinks').setValue(' https://example.com/one\n\nhttps://example.com/two ')
    await wrapper.get('.form-buttons .btn').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/v1/archives/batches/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          urls: ['https://example.com/one', 'https://example.com/two'],
          target_folder: 1,
          human: true,
        }),
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/archives/batches/41',
      {headers: {'X-CSRFToken': undefined}},
    )
    expect(store.components.linkList.fetchLinks).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Batch complete.')
    expect(wrapper.text()).toContain('These Perma Links were added to Personal Links')
  })

  it('renders server field errors from the upload dialog without navigating away', async () => {
    const {pinia, store} = configureStore()
    store.components.createLink = {resetForm: vi.fn()}
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response(
      {title: ['A title is required']},
      {ok: false, status: 400, statusText: 'Bad Request'},
    ))
    const FileInputStub = {
      emits: ['update:modelValue'],
      setup(_, {emit}) {
        return {
          selectFile: () => emit('update:modelValue', new File(['content'], 'capture.pdf', {type: 'application/pdf'})),
        }
      },
      template: '<button class="file-select" type="button" @click="selectFile">Choose file</button>',
    }
    const wrapper = mount(UploadForm, {
      global: {
        plugins: [pinia],
        stubs: {FileInput: FileInputStub},
      },
    })

    await wrapper.get('#url').setValue('https://example.com/upload')
    await wrapper.get('.file-select').trigger('click')
    await wrapper.get('.btn-primary').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/archives/',
      expect.objectContaining({method: 'POST', body: expect.any(FormData)}),
    )
    expect(wrapper.text()).toContain('A title is required')
    expect(wrapper.text()).not.toContain('Upload failed.')
  })
})
