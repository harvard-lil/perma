// @vitest-environment node
//
// Must not run in JSDOM: sass-loader's modern Dart Sass API requires its importer to return a real
// URL instance, and JSDOM's URL global fails that instanceof check with "The canonicalize() method
// must return a URL" on every `@import "~bootstrap/..."`. spec/vitest.setup.js is guarded for this.
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { createRequire } from 'node:module'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const require = createRequire(import.meta.url)
const projectRoot = path.resolve(import.meta.dirname, '..', '..')
const configPath = path.join(projectRoot, 'webpack.config.js')
const webpack = require('webpack')

// All entries declared in webpack.config.js; hardcoded so a deleted/renamed entry fails this test
// rather than silently passing because the test re-derived its expectations from the same config.
const ENTRY_NAMES = [
  'single-link',
  'global',
  'single-link-permissions',
  'link-delete-confirm',
  'developer-docs',
  'admin-stats',
  'dashboard',
]
const CSS_ENTRY_NAMES = ['single-link', 'global', 'dashboard']
const NON_CSS_ENTRY_NAMES = ENTRY_NAMES.filter((name) => !CSS_ENTRY_NAMES.includes(name))

// Webpack 5 reports entrypoint assets as {name, size} objects rather than bare filenames.
const entryAssetNames = (entry) => entry.assets.map((asset) => asset.name)

// webpack-bundle-tracker's plugin constructor reads BUNDLE_TRACKER_DIR once, at require() time,
// so each build needs a fresh module instance to pick up its own stats directory.
function buildOnce(outputPath, statsDir) {
  delete require.cache[require.resolve(configPath)]
  process.env.BUNDLE_TRACKER_DIR = statsDir
  const config = require(configPath)
  config.context = path.dirname(configPath)
  config.output = { ...config.output, path: outputPath }

  return new Promise((resolve, reject) => {
    webpack(config, (err, stats) => {
      if (err) return reject(err)
      if (stats.hasErrors()) return reject(new Error(JSON.stringify(stats.toJson().errors, null, 2)))
      resolve(stats)
    })
  })
}

let tmpRoot
let build1
let build2
let trackerJson

beforeAll(async () => {
  tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'perma-webpack-contract-'))
  const statsToJsonOptions = { entrypoints: true, chunks: true, chunkModules: true, modules: true }

  const outDir1 = path.join(tmpRoot, 'build1')
  const statsDir1 = path.join(tmpRoot, 'stats1')
  fs.mkdirSync(statsDir1, { recursive: true })
  const stats1 = await buildOnce(outDir1, statsDir1)
  build1 = { outDir: outDir1, statsJson: stats1.toJson(statsToJsonOptions) }
  trackerJson = JSON.parse(fs.readFileSync(path.join(statsDir1, 'webpack-stats.json'), 'utf8'))

  // The determinism comparison has to run the second build in a separate process. Webpack's
  // clonedRuleSet counter is module-level and keeps incrementing across compilations in one
  // process, and vue-loader's cloned rules bake those numbers into generated module identifiers --
  // so two in-process builds can never match even when the build is genuinely reproducible.
  const outDir2 = path.join(tmpRoot, 'build2')
  execFileSync('npx', ['webpack', '--config', configPath, '--output-path', outDir2], {
    cwd: projectRoot,
    env: { ...process.env, BUNDLE_TRACKER_DIR: tmpRoot },
    stdio: 'pipe',
  })
  build2 = { outDir: outDir2 }
}, 180000)

afterAll(() => {
  delete process.env.BUNDLE_TRACKER_DIR
  if (tmpRoot) fs.rmSync(tmpRoot, { recursive: true, force: true })
})

describe('webpack entries', () => {
  it.each(ENTRY_NAMES)('entry "%s" builds and emits a JS asset', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    expect(entry).toBeDefined()
    expect(entryAssetNames(entry).some((asset) => asset.endsWith('.js'))).toBe(true)
  })

  it.each(CSS_ENTRY_NAMES)('entry "%s" also emits a CSS asset', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    expect(entryAssetNames(entry).some((asset) => asset.endsWith('.css'))).toBe(true)
  })

  it.each(NON_CSS_ENTRY_NAMES)('entry "%s" does not emit CSS', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    expect(entryAssetNames(entry).some((asset) => asset.endsWith('.css'))).toBe(false)
  })
})

describe('bundle tracker output', () => {
  // Tripwire: webpack-bundle-tracker 3.x (sub-batch 2F) changes this schema. If this test starts
  // failing after that upgrade, that is expected -- update the assertions deliberately, not by rote.
  it('writes status "done" with a chunks entry for every webpack entry', () => {
    expect(trackerJson.status).toBe('done')
    expect(Object.keys(trackerJson.chunks).sort()).toEqual([...ENTRY_NAMES].sort())
  })

  // django-webpack-loader renders every file a chunk lists, so a source map appearing here
  // would be emitted into page markup.
  it('lists each entry\'s JS/CSS and no source maps', () => {
    for (const [entryName, files] of Object.entries(trackerJson.chunks)) {
      expect(files.some((file) => file.endsWith('.js')), `${entryName} lists no JS`).toBe(true)
      expect(files.filter((file) => file.endsWith('.map')), `${entryName} leaked source maps`).toEqual([])
    }
  })

  it('lists only files that were actually emitted by the build', () => {
    const emitted = new Set(fs.readdirSync(build1.outDir))
    for (const [entryName, files] of Object.entries(trackerJson.chunks)) {
      expect(files.length, `${entryName} chunk file list`).toBeGreaterThan(0)
      for (const file of files) {
        expect(emitted.has(file), `${entryName} -> ${file} was not emitted`).toBe(true)
      }
    }
  })
})

describe('source maps', () => {
  it.each(ENTRY_NAMES)('entry "%s" emits a companion source map referenced from its JS', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    const jsFile = entryAssetNames(entry).find((asset) => asset.endsWith('.js'))
    const mapFile = `${jsFile}.map`
    // Webpack 5 moved source maps out of an entry's assets and into its auxiliaryAssets.
    const auxiliaryNames = (entry.auxiliaryAssets || []).map((asset) => asset.name)
    expect(auxiliaryNames).toContain(mapFile)

    const jsContent = fs.readFileSync(path.join(build1.outDir, jsFile), 'utf8')
    expect(jsContent.trimEnd().endsWith(`//# sourceMappingURL=${mapFile}`)).toBe(true)

    const map = JSON.parse(fs.readFileSync(path.join(build1.outDir, mapFile), 'utf8'))
    expect(Array.isArray(map.sources)).toBe(true)
    expect(map.sources.length).toBeGreaterThan(0)
  })
})

describe('CSS extraction and order', () => {
  it('extracts global.css with SCSS content before font-awesome content, matching entry declaration order', () => {
    // Selectors picked by reading the actual sources: style-responsive.scss declares
    // .style-clears-floats directly; font-awesome.min.css declares .icon-glass.
    const scssSelector = '.style-clears-floats'
    const faSelector = '.icon-glass'
    const scssSource = fs.readFileSync(path.join(projectRoot, 'static/css/style-responsive.scss'), 'utf8')
    const faSource = fs.readFileSync(
      path.join(projectRoot, 'static/vendors/font-awesome/font-awesome.min.css'),
      'utf8',
    )
    expect(scssSource).toContain(scssSelector)
    expect(faSource).toContain(faSelector)

    const css = fs.readFileSync(path.join(build1.outDir, 'global.css'), 'utf8')
    const scssIndex = css.indexOf(scssSelector)
    const faIndex = css.indexOf(faSelector)
    expect(scssIndex).toBeGreaterThan(-1)
    expect(faIndex).toBeGreaterThan(-1)
    expect(scssIndex).toBeLessThan(faIndex)
  })
})

describe('image/font inline-vs-resource threshold (url-loader limit: 10000)', () => {
  // No font in this repo is under the 10000-byte limit (smallest is ~19KB), so the "inlined" witness
  // is an image asset instead -- it hits the same url-loader limit option, which is what's under test.
  it('inlines an asset under the limit as a data URI', () => {
    const smallAssetPath = path.join(projectRoot, 'static/img/ui/perma-ui-chev-right-small.png')
    const bytes = fs.readFileSync(smallAssetPath)
    expect(bytes.length).toBeLessThan(10000)

    const css = fs.readFileSync(path.join(build1.outDir, 'global.css'), 'utf8')
    expect(css).toContain(`data:image/png;base64,${bytes.toString('base64')}`)
  })

  it('emits an asset over the limit as a separate hashed file referenced by name', () => {
    const largeAssetPath = path.join(projectRoot, 'static/fonts/font-awesome/fontawesome-webfont.woff')
    const bytes = fs.readFileSync(largeAssetPath)
    expect(bytes.length).toBeGreaterThan(10000)

    const emittedWoffFiles = fs.readdirSync(build1.outDir).filter((file) => file.endsWith('.woff'))
    const match = emittedWoffFiles.find((file) => fs.readFileSync(path.join(build1.outDir, file)).equals(bytes))
    expect(match, 'no emitted .woff file matched the source font bytes').toBeDefined()

    const css = fs.readFileSync(path.join(build1.outDir, 'global.css'), 'utf8')
    expect(css).toContain(`url(${match})`)
  })
})

describe('browser runtime globals', () => {
  // Webpack 5 stopped shimming Node globals. Any surviving bare `process.env` read throws
  // "process is not defined" in the browser, which silently breaks the whole entry.
  it.each(ENTRY_NAMES)('entry "%s" ships no unreplaced process.env reads', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    for (const asset of entryAssetNames(entry).filter((file) => file.endsWith('.js'))) {
      const content = fs.readFileSync(path.join(build1.outDir, asset), 'utf8')
      expect(content.includes('process.env'), `${asset} reads process.env at runtime`).toBe(false)
    }
  })
})

describe('jQuery global exposure (webpack.ProvidePlugin)', () => {
  it('global.js uses $ without importing jquery itself', () => {
    const src = fs.readFileSync(path.join(projectRoot, 'static/js/global.js'), 'utf8')
    expect(src).toMatch(/\$\(/)
    expect(src).not.toMatch(/require\(\s*['"]jquery['"]\s*\)/)
  })

  it('the "global" chunk pulls in the jquery module via ProvidePlugin injection', () => {
    const globalChunk = build1.statsJson.chunks.find((chunk) => chunk.names.includes('global'))
    expect(globalChunk).toBeDefined()
    const hasJqueryModule = globalChunk.modules.some((module) => /node_modules\/jquery/.test(module.name || ''))
    expect(hasJqueryModule).toBe(true)
  })
})

describe('Vue SFC compilation (dashboard entry)', () => {
  it('resolves at least one .vue module, including the scoped LinkList.vue component', () => {
    const vueModules = build1.statsJson.modules.filter((module) => (module.name || '').split('?')[0].endsWith('.vue'))
    expect(vueModules.length).toBeGreaterThan(0)
    expect(vueModules.some((module) => module.name.includes('LinkList.vue'))).toBe(true)
  })

  it('agrees on LinkList.vue\'s scoped-style id between dashboard.js and dashboard.css', () => {
    const js = fs.readFileSync(path.join(build1.outDir, 'dashboard.js'), 'utf8')
    const css = fs.readFileSync(path.join(build1.outDir, 'dashboard.css'), 'utf8')
    // Vue also stamps a bare "data-v-app" marker on the root element; requiring 4+ hex digits
    // after "data-v-" excludes that and matches only real content-derived scope ids.
    const scopeIdPattern = /data-v-[0-9a-f]{4,}/g
    const jsIds = new Set(js.match(scopeIdPattern) || [])
    const cssIds = new Set(css.match(scopeIdPattern) || [])

    expect(jsIds.size).toBeGreaterThan(0)
    expect(cssIds.size).toBeGreaterThan(0)
    expect([...jsIds].sort()).toEqual([...cssIds].sort())
  })
})

describe('deterministic rebuild', () => {
  it('emits the same set of asset names on both builds', () => {
    const files1 = fs.readdirSync(build1.outDir).sort()
    const files2 = fs.readdirSync(build2.outDir).sort()
    expect(files2).toEqual(files1)
  })

  it.each(ENTRY_NAMES)('entry "%s" JS/CSS output is byte-identical across both builds', (name) => {
    const entry = build1.statsJson.entrypoints[name]
    const assetsToCompare = entryAssetNames(entry).filter((asset) => asset.endsWith('.js') || asset.endsWith('.css'))
    expect(assetsToCompare.length).toBeGreaterThan(0)
    for (const asset of assetsToCompare) {
      const contentA = fs.readFileSync(path.join(build1.outDir, asset))
      const contentB = fs.readFileSync(path.join(build2.outDir, asset))
      expect(contentB.equals(contentA), `${asset} differed between builds`).toBe(true)
    }
  })
})
