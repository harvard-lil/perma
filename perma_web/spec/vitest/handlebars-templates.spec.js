// Pins handlebars 4.7.8 behavior ahead of the 4.7.9 upgrade (see
// .plans/plan_dependency-upgrade-roadmap-5.md, sub-batch 5A). 4.7.9 is a security
// patch: it validates pre-parsed ASTs passed to compile() (Perma only ever compiles
// template *strings*, never a pre-parsed AST, so that path is not reached here) and
// tightens prototype-access control (adds __lookupSetter__ to the default block
// list). Template source is read straight out of admin-stats.html at test time, not
// copied inline, so these tests track the real templates rather than a stale copy.
import { describe, expect, it, vi } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import Handlebars from 'handlebars'
import * as HandlebarsHelpers from '../../static/js/helpers/handlebars.helpers.js'

const TEMPLATE_FILE = path.resolve(import.meta.dirname, '../../perma/templates/admin-stats.html')
const TEMPLATE_SOURCE = fs.readFileSync(TEMPLATE_FILE, 'utf8')

// admin-stats.html names nine template ids in the phase plan's coverage list, but the
// file itself contains only these eight <script type="text/x-handlebars-template">
// blocks (grepped directly) -- admin-stats.js's tabSections/fillSection agrees, also
// naming only eight. Documentation mismatch in the plan, not a missing template.
const TEMPLATE_IDS = [
  'random-template',
  'days-template',
  'emails-template',
  'job_queue-template',
  'celery_queues-template',
  'celery-template',
  'rate_limits-template',
  'capture_errors-template',
]

function extractTemplate(id) {
  const re = new RegExp(`<script[^>]*\\bid="${id}"[^>]*>([\\s\\S]*?)<\\/script>`)
  const match = TEMPLATE_SOURCE.match(re)
  if (!match) throw new Error(`template "${id}" not found in ${TEMPLATE_FILE}`)
  return match[1]
}

const TEMPLATES = Object.fromEntries(TEMPLATE_IDS.map((id) => [id, extractTemplate(id)]))

// Mirrors what Django actually serves: a <script type="text/x-handlebars-template">
// node in the document, read via jQuery's .html() inside handlebars.helpers.js.
function injectTemplate(id, source) {
  const script = document.createElement('script')
  script.id = id
  script.type = 'text/x-handlebars-template'
  script.textContent = source
  document.body.appendChild(script)
  return script
}

function renderToContainer(id, data) {
  injectTemplate(id, TEMPLATES[id])
  const html = HandlebarsHelpers.renderTemplate(`#${id}`, data)
  const container = document.createElement('div')
  container.innerHTML = html
  return {html, container}
}

// Whitespace in the source templates is not itself meaningful; assertions below
// normalize it so they track content, not incidental indentation.
function normalize(text) {
  return text.replace(/\s+/g, ' ').trim()
}

describe('admin-stats.html template extraction', () => {
  it('finds all eight template blocks', () => {
    expect(Object.keys(TEMPLATES).sort()).toEqual([...TEMPLATE_IDS].sort())
    for (const id of TEMPLATE_IDS) {
      expect(TEMPLATES[id].trim().length).toBeGreaterThan(0)
    }
  })
})

describe('admin-stats.html templates render real payload shapes', () => {
  describe('random-template', () => {
    it('renders every stat row from the "random" admin_stats.py payload', () => {
      const data = {
        total_link_count: 1000,
        private_link_count: 200,
        private_link_percentage: 20.0,
        private_user_direction: 50,
        private_user_percentage_of_private: 25.5,
        private_user_percentage_of_total: 5.3,
        private_domain: 40,
        private_domain_percentage_of_private: 20.0,
        private_domain_percentage_of_total: 4.0,
        private_meta_perma: 30,
        private_meta_perma_percentage_of_private: 15.0,
        private_meta_perma_percentage_of_total: 3.0,
        private_meta: 20,
        private_meta_percentage_of_private: 10.0,
        private_meta_percentage_of_total: 2.0,
        private_takedown: 10,
        private_takedown_percentage_of_private: 5.0,
        private_takedown_percentage_of_total: 1.0,
        private_flagged: 5,
        private_flagged_percentage_of_private: 2.5,
        private_flagged_percentage_of_total: 0.5,
        private_meta_failure: 45,
        private_meta_failure_percentage_of_private: 22.5,
        private_meta_failure_percentage_of_total: 4.5,
        links_w_meta_failure_tag: 12,
        tagged_meta_failure_percentage_of_total: 1.2,
        links_w_timeout_failure_tag: 8,
        tagged_timeout_failure_percentage_of_total: 0.8,
        links_w_browser_crashed_tag: 3,
        tagged_browser_crashed_percentage_of_total: 0.3,
        total_user_count: 500,
        unconfirmed_user_count: 60,
        unconfirmed_user_percentage: 12.0,
        users_with_ten_links: 25,
        users_with_ten_links_percentage: 5.0,
        confirmed_users_with_no_links: 100,
        confirmed_users_with_no_links_percentage: 20.0,
      }

      const {container} = renderToContainer('random-template', data)
      const rows = container.querySelectorAll('.row')
      expect(rows).toHaveLength(16)

      expect(normalize(rows[0].querySelector('.col-sm-9').textContent)).toBe('1000')
      expect(normalize(rows[1].querySelector('.col-sm-9').textContent)).toBe(
        '50 (25.5% of private, 5.3% of total)'
      )
      expect(normalize(rows[8].querySelector('.col-sm-9').textContent)).toBe('200 (20%)')

      const metaFailureLink = rows[9].querySelector('a')
      expect(metaFailureLink.getAttribute('href')).toBe('/admin/perma/link/?q=meta-tag-retrieval-failure')
      expect(normalize(metaFailureLink.textContent)).toBe('12 (1.2% of total')
      expect(normalize(rows[9].querySelector('.col-sm-9').textContent)).toBe('12 (1.2% of total)')

      expect(normalize(rows[12].querySelector('.col-sm-1').textContent)).toBe('500')
      expect(normalize(rows[13].querySelector('.col-sm-9').textContent)).toBe('60 (12%)')
      expect(normalize(rows[15].querySelector('.col-sm-9').textContent)).toBe('100 (20%)')
    })
  })

  describe('days-template', () => {
    it('renders one row per day plus nested top_users cells, and the static header', () => {
      const data = {
        days: [
          {
            days_ago: 0,
            start_date: '2026-09-01T00:00:00+00:00',
            end_date: '2026-09-02T00:00:00+00:00',
            link_count: 42,
            statuses: {success: 38, pending: 2, failed: 2},
            capture_time_dist: '1.2s / 3.4s / 9.8s',
            wait_time_dist: '0.1s / 0.5s / 2.0s',
            top_users: [
              {email: 'alice@example.com', links_count: 5},
              {email: 'bob@example.com', links_count: 3},
            ],
          },
          {
            days_ago: 1,
            start_date: '2026-08-31T00:00:00+00:00',
            end_date: '2026-09-01T00:00:00+00:00',
            link_count: 10,
            statuses: {success: 10, pending: 0, failed: 0},
            capture_time_dist: '-',
            wait_time_dist: '-',
            top_users: [],
          },
        ],
      }

      const {container} = renderToContainer('days-template', data)
      const rows = container.querySelectorAll('#day tr')
      expect(rows).toHaveLength(3) // static header + 2 days

      expect(normalize(rows[0].textContent)).toContain('Days')
      expect(normalize(rows[0].textContent)).toContain('Top Users')

      const day0Cells = rows[1].querySelectorAll('td')
      expect(day0Cells).toHaveLength(11) // 7 fixed + 2 top_users x 2 cells each
      expect(day0Cells[0].getAttribute('title')).toBe('2026-09-01T00:00:00+00:00-2026-09-02T00:00:00+00:00')
      expect(normalize(day0Cells[0].textContent)).toBe('0')
      expect(normalize(day0Cells[1].textContent)).toBe('42')
      expect(normalize(day0Cells[2].textContent)).toBe('38')
      expect(normalize(day0Cells[3].textContent)).toBe('2')
      expect(normalize(day0Cells[4].textContent)).toBe('2')
      expect(normalize(day0Cells[5].textContent)).toBe('1.2s / 3.4s / 9.8s')
      expect(normalize(day0Cells[6].textContent)).toBe('0.1s / 0.5s / 2.0s')
      expect(normalize(day0Cells[7].textContent)).toBe('alice@example.com')
      expect(normalize(day0Cells[8].textContent)).toBe('5')
      expect(normalize(day0Cells[9].textContent)).toBe('bob@example.com')
      expect(normalize(day0Cells[10].textContent)).toBe('3')

      const day1Cells = rows[2].querySelectorAll('td')
      expect(day1Cells).toHaveLength(7) // no top_users -> no extra cells
      expect(normalize(day1Cells[1].textContent)).toBe('10')
    })
  })

  describe('emails-template', () => {
    it('renders one line per domain from users_by_domain', () => {
      const data = {
        users_by_domain: [
          {domain: 'example.com', count: 120},
          {domain: 'harvard.edu', count: 45},
        ],
      }

      const {container} = renderToContainer('emails-template', data)
      expect(container.querySelectorAll('br')).toHaveLength(2)
      expect(normalize(container.textContent)).toBe('.example.com: 120 .harvard.edu: 45')
    })
  })

  describe('job_queue-template', () => {
    it('renders active jobs and the human requests column from real payload shapes', () => {
      const data = {
        active_jobs: [
          {
            link_id: 'ABCD-1234',
            email: 'carol@example.com',
            attempt: 1,
            step_count: 2.5,
            step_description: 'Uploading to storage',
            capture_start_time: '2026-09-02T12:00:00+00:00',
          },
        ],
        job_queues: {
          human: [{email: 'dave@example.com', count: 3}],
          robot: [{email: 'api-user@example.com', count: 7}],
        },
      }

      const {container} = renderToContainer('job_queue-template', data)
      const columns = container.querySelectorAll('.col-sm-4')
      expect(columns).toHaveLength(3)

      const inProgress = normalize(columns[0].textContent)
      expect(inProgress).toContain('ABCD-1234 attempt 1')
      expect(inProgress).toContain('carol@example.com')
      expect(inProgress).toContain('Started 2026-09-02T12:00:00+00:00')
      expect(inProgress).toContain('Step 2.5: Uploading to storage')

      expect(normalize(columns[1].textContent)).toBe('Human requests: dave@example.com: 3')
    })

    // Pre-existing defect, not introduced by this test and not fixed here (reported
    // separately): admin_stats.py builds job_queues.robot as the same list-of-{email,count}
    // shape as job_queues.human, but this column iterates it as {{@key}}: {{this}},
    // i.e. as a flat scalar map. Over a list of objects that renders the object's
    // default toString(), not the email/count -- pinned exactly as it behaves today.
    it('characterizes the API requests column stringifying each {email,count} object via {{this}}', () => {
      const data = {
        active_jobs: [],
        job_queues: {
          human: [],
          robot: [
            {email: 'api-user-1@example.com', count: 7},
            {email: 'api-user-2@example.com', count: 2},
          ],
        },
      }

      const {container} = renderToContainer('job_queue-template', data)
      const apiColumn = container.querySelectorAll('.col-sm-4')[2]
      expect(normalize(apiColumn.textContent)).toBe(
        'API requests: User 0: [object Object] waiting User 1: [object Object] waiting'
      )
    })
  })

  describe('celery_queues-template', () => {
    it('renders each queue length', () => {
      const data = {
        total_main_queue: 5,
        total_background_queue: 2,
        total_ia_queue: 12,
        total_ia_readonly_queue: 3,
        total_wacz_conversion_queue: 1,
      }

      const {container} = renderToContainer('celery_queues-template', data)
      const rows = container.querySelectorAll('.row')
      expect(rows).toHaveLength(5)
      expect(normalize(rows[0].querySelector('.col-sm-9').textContent)).toBe('5')
      expect(normalize(rows[1].querySelector('.col-sm-9').textContent)).toBe('2')
      expect(normalize(rows[2].querySelector('.col-sm-9').textContent)).toBe('12')
      expect(normalize(rows[3].querySelector('.col-sm-9').textContent)).toBe('3')
      expect(normalize(rows[4].querySelector('.col-sm-9').textContent)).toBe('1')
    })
  })

  describe('celery-template', () => {
    it('renders per-worker active/reserved tasks and finished stats', () => {
      const data = {
        queues: [
          {
            name: 'celery@worker1',
            active: [{name: 'perma.tasks.capture', args: ['ABCD-1234'], kwargs: {}}],
            reserved: [{name: 'perma.tasks.upload', args: [], kwargs: {guid: 'WXYZ-5678'}}],
            stats: {total: {'perma.tasks.capture': 120, 'perma.tasks.upload': 45}},
          },
        ],
      }

      const {container} = renderToContainer('celery-template', data)
      const blocks = container.querySelectorAll('.queue-block')
      expect(blocks).toHaveLength(1)
      expect(normalize(blocks[0].querySelector('h4').textContent)).toBe('celery@worker1')

      const jobBlocks = blocks[0].querySelectorAll('.job-block')
      expect(normalize(jobBlocks[0].textContent)).toBe('perma.tasks.capture: ABCD-1234')
      expect(normalize(jobBlocks[1].textContent)).toContain('Next jobs (not a complete list):')
      expect(normalize(jobBlocks[1].textContent)).toContain('perma.tasks.upload: guid: WXYZ-5678')
      expect(normalize(jobBlocks[2].textContent)).toContain('Finished task count:')
      expect(normalize(jobBlocks[2].textContent)).toContain('perma.tasks.capture: 120')
      expect(normalize(jobBlocks[2].textContent)).toContain('perma.tasks.upload: 45')
    })
  })

  describe('rate_limits-template', () => {
    it('renders inflight counts, general_s3, buckets, task info, and over_limit_details', () => {
      const data = {
        inflight: 4,
        total_ia_queue: 12,
        total_ia_readonly_queue: 3,
        general_s3: {
          accesskey_ration: 100,
          accesskey_tasks_queued: 20,
          total_global_limit: 5000,
          total_tasks_queued: 800,
        },
        buckets: {
          'ABCD-1234': {bucket_ration: 10, bucket_tasks_queued: 2},
        },
        modify_xml: {tasks_limit: 50, tasks_inflight: 5, tasks_blocked_by_offline: 0},
        derive: {tasks_limit: 50, tasks_inflight: 1, tasks_blocked_by_offline: 0},
        over_limit_details: [
          {bucket: 'ABCD-1234', detail: {bucket_ration: 10, bucket_tasks_queued: 11}, over_limit: true},
        ],
      }

      const {container} = renderToContainer('rate_limits-template', data)
      const rows = container.querySelectorAll('.row')
      expect(rows).toHaveLength(7)

      expect(normalize(rows[0].querySelector('.col-sm-8').textContent)).toBe('4')
      expect(normalize(rows[1].querySelector('.col-sm-8').textContent)).toBe('12')
      expect(normalize(rows[2].querySelector('.col-sm-8').textContent)).toBe('3')

      // The source has <dd>{{@key}}:</dd><dt>{{this}}</dt> with no separator between them
      // or between loop iterations, so adjacent key/value pairs run together with no space --
      // real (if visually cramped) rendered output, not a normalization artifact.
      const generalS3Dl = rows[3].querySelectorAll('.col-sm-3')[1].querySelector('dl')
      expect(normalize(generalS3Dl.textContent)).toBe(
        'accesskey_ration:100accesskey_tasks_queued:20total_global_limit:5000total_tasks_queued:800'
      )

      const bucketBlocks = rows[3].querySelectorAll('.bucket-stats')
      expect(normalize(bucketBlocks[0].textContent)).toBe('ABCD-1234')
      expect(normalize(bucketBlocks[1].textContent)).toBe('bucket_ration:10bucket_tasks_queued:2')

      const modifyXmlDl = rows[4].querySelector('dl')
      expect(normalize(modifyXmlDl.textContent)).toBe('tasks_limit:50tasks_inflight:5tasks_blocked_by_offline:0')

      const deriveDl = rows[5].querySelector('dl')
      expect(normalize(deriveDl.textContent)).toBe('tasks_limit:50tasks_inflight:1tasks_blocked_by_offline:0')

      const overLimit = rows[6].querySelector('.over-limit')
      expect(normalize(overLimit.textContent)).toBe(
        'bucketABCD-1234 bucket_ration:10bucket_tasks_queued:11 over_limittrue'
      )
    })
  })

  describe('capture_errors-template', () => {
    it('renders all six time-range breakdowns via explicit this. paths', () => {
      const rangeStats = (n) => ({
        completed: n, completed_percent: n / 10,
        failed: n - 1, failed_percent: (n - 1) / 10,
        celery_timeout: 1, celery_timeout_percent: 0.1,
        proxy_error: 1, proxy_error_percent: 0.1,
        blocklist_error: 0, blocklist_error_percent: 0,
        playwright_error: 0, playwright_error_percent: 0,
        timeout: 1, timeout_percent: 0.1,
        didnt_load: 0, didnt_load_percent: 0,
      })
      const data = {
        last_hour: rangeStats(10),
        last_3_hrs: rangeStats(30),
        last_24_hrs: rangeStats(200),
        last_hour_on_previous_day: rangeStats(8),
        last_3_hrs_on_previous_day: rangeStats(25),
        previous_24_hrs: rangeStats(190),
      }

      const {container} = renderToContainer('capture_errors-template', data)
      const dls = container.querySelectorAll('dl.dl-horizontal')
      expect(dls).toHaveLength(6)

      // <dt>Completed:</dt><dd>...</dd> are adjacent with no separator in the source, so the
      // label and value run together with no space -- real rendered output, not a normalization
      // artifact. (Separate <dt>/<dd> pairs are on their own lines, so a space appears between them.)
      expect(normalize(dls[0].textContent)).toBe(
        'Completed:10 (1%) Failed:9 (0.9%) Killed by Celery:1 (0.1%) Proxy error:1 (0.1%) ' +
        "Blocklist error:0 (0%) Playwright error:0 (0%) Scoop timeout:1 (0.1%) URL didn't load:0 (0%)"
      )
      expect(normalize(dls[5].textContent)).toContain('Completed:190 (19%)')
    })
  })
})

describe('renderTemplate / compileTemplate behavior', () => {
  it('caches the compiled template: a second renderTemplate call does not recompile', () => {
    injectTemplate('cache-test-template', '{{ value }}')
    const compileSpy = vi.spyOn(Handlebars, 'compile')

    expect(HandlebarsHelpers.renderTemplate('#cache-test-template', {value: 'first'})).toBe('first')
    expect(compileSpy).toHaveBeenCalledTimes(1)

    // Mutate the DOM source after first compile; a real recompile would pick this up.
    document.getElementById('cache-test-template').textContent = '{{ value }}-CHANGED'
    expect(HandlebarsHelpers.renderTemplate('#cache-test-template', {value: 'second'})).toBe('second')
    expect(compileSpy).toHaveBeenCalledTimes(1)
  })

  it('defaults args to {} when renderTemplate is called with only a selector', () => {
    injectTemplate('args-default-template', 'Value: [{{ value }}]')
    expect(HandlebarsHelpers.renderTemplate('#args-default-template')).toBe('Value: []')
  })

  it('compileTemplate populates the same cache renderTemplate reads, and the compiled fn is directly callable', () => {
    injectTemplate('compile-test-template', '{{ greeting }}, {{ name }}!')

    const compiled = HandlebarsHelpers.compileTemplate('#compile-test-template')
    expect(typeof compiled).toBe('function')
    expect(compiled({greeting: 'Hello', name: 'World'})).toBe('Hello, World!')

    // Remove the DOM node entirely; renderTemplate must still work from the shared cache.
    document.getElementById('compile-test-template').remove()
    expect(HandlebarsHelpers.renderTemplate('#compile-test-template', {greeting: 'Hi', name: 'There'})).toBe(
      'Hi, There!'
    )
  })

  it('compileTemplate returns undefined when the selector matches nothing', () => {
    expect(HandlebarsHelpers.compileTemplate('#does-not-exist-anywhere')).toBeUndefined()
  })
})

describe('escaping: {{ }} vs {{{ }}}', () => {
  it('{{ }} HTML-escapes interpolated values, using emails-template\'s real {{ domain }} usage', () => {
    injectTemplate('emails-template', TEMPLATES['emails-template'])
    const html = HandlebarsHelpers.renderTemplate('#emails-template', {
      users_by_domain: [{domain: '<b>evil</b>&co', count: 1}],
    })
    expect(html).toContain('&lt;b&gt;evil&lt;/b&gt;&amp;co')
    expect(html).not.toContain('<b>evil</b>&co')
  })

  // None of the eight real admin-stats.html templates use {{{ }}} (grepped) -- this
  // synthetic template exists only to show the contrast the 4.7.9 patch is adjacent to.
  it('{{{ }}} does not escape, unlike every real template usage above', () => {
    injectTemplate('triple-mustache-template', 'Escaped: {{ value }} | Unescaped: {{{ value }}}')
    const html = HandlebarsHelpers.renderTemplate('#triple-mustache-template', {value: '<b>hi</b>'})
    expect(html).toBe('Escaped: &lt;b&gt;hi&lt;/b&gt; | Unescaped: <b>hi</b>')
  })
})

describe('prototype access', () => {
  // Not exercised by any real admin-stats.html template (their data is plain JSON from
  // Perma's own endpoints), but this is exactly the mechanism 4.7.9 tightens (it adds
  // __lookupSetter__ to the default block list below). Pins 4.7.8's current behavior:
  // a property resolved only via the prototype chain -- not an own property -- renders
  // as empty and logs once via Handlebars.logger, rather than throwing or rendering the
  // inherited value.
  it('renders empty and logs once when a template reads a property that exists only on the prototype', () => {
    function Proto() {}
    Proto.prototype.protoOnlyStatValueForThisTest = 'inherited-value'
    const obj = new Proto()
    obj.ownStatValue = 'own-value'

    const logSpy = vi.spyOn(Handlebars.logger, 'log')
    injectTemplate('proto-access-template', 'own=[{{ ownStatValue }}] inherited=[{{ protoOnlyStatValueForThisTest }}]')
    const html = HandlebarsHelpers.renderTemplate('#proto-access-template', obj)

    expect(html).toBe('own=[own-value] inherited=[]')
    expect(logSpy).toHaveBeenCalledWith(
      'error',
      expect.stringContaining(
        'Access has been denied to resolve the property "protoOnlyStatValueForThisTest" because it is not an "own property" of its parent.'
      )
    )
  })
})
