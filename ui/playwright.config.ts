import { defineConfig, devices } from '@playwright/test';

//: ── WHY THIS EXISTS, AND WHAT IT IS AIMED AT ────────────────────────────────
//:
//: Three defects shipped in one day and every one of them was invisible to
//: `svelte-check`, to the build, and to reading the diff:
//:
//:   a focus ring painted over the plot on every click     visual
//:   `punch` printed on top of `cry` in a slopegraph        visual
//:   a broken <img> beside a successful render and correct  a failed REQUEST,
//:     numbers, because the URL lacked the /api prefix      not a JS error
//:
//: A fourth crashed the Prompts table with `each_key_duplicate`, which WAS a
//: console error and which nothing was listening for.
//:
//: So the suite is not a DOM-assertion suite. It watches for page errors, for
//: failed requests, and it keeps screenshots — in that order of cheapness.
//: `ui/TODO.md` argued the honest first test here is a screenshot diff rather
//: than a DOM assertion, and this is that argument implemented.
//:
//: ── EACH CHECK WAS WATCHED FAILING, AND ONE CLAIM WAS WRONG ─────────────────
//:
//: A checker is not a checker until it has been seen to refuse, so all three
//: were made to fire deliberately:
//:
//:   failed requests   pointed one api.ts route at `/rosterX` -> FIRED
//:   screenshot diff   table font 11px -> 14px, ratio 0.06 against the 0.005
//:                     threshold, 12x over -> FIRED
//:   favicon 404       renamed `static/favicon.svg` -> **DID NOT FIRE**
//:
//: **The third was a claim I made and it is false.** A favicon is fetched by the
//: browser outside the page's request lifecycle, so `page.on('requestfailed')`
//: never sees it, and the test passed with the file gone. The check catches
//: IN-PAGE requests, which is what the broken `<img>` was; it does not catch
//: document-level assets. Left recorded rather than deleted, because the version
//: of this comment that only listed the two successes would have read as
//: coverage of three.
//:
//: **IT NEEDS BOTH SERVERS AND SAYS SO RATHER THAN FAILING OBSCURELY.** The dev
//: server proxies `/api` to the Python one, so a panel with the API down renders
//: its error state perfectly well and a screenshot baseline would happily record
//: it. `e2e/app.spec.ts` checks reachability first and skips with a sentence.
export default defineConfig({
	testDir: './e2e',
	//: Serial. The API server holds a `_PLOT_LOCK` and a `_SLOT_LOCK`, and the
	//: Prompts rollup is a 14s ClickHouse read — parallel workers would queue on
	//: the same locks and time out looking like flakes.
	workers: 1,
	fullyParallel: false,
	//: The uncached Prompts rollup is a measured 14s and the render is ~13s on a
	//: cold cache, so the default 30s is not enough for the panels this suite
	//: exists to look at.
	timeout: 90_000,
	expect: {
		//: **A THRESHOLD, NOT AN EXACT MATCH.** Antialiasing differs across
		//: machines and OS versions, and a suite that fails on a rounded pixel
		//: gets disabled within a week. 0.5% of pixels is loose enough to survive
		//: a font-rendering difference and tight enough to catch a focus ring
		//: painted over a plot or two labels landing on each other.
		toHaveScreenshot: { maxDiffPixelRatio: 0.005 }
	},
	use: {
		baseURL: process.env.UI_URL ?? 'http://127.0.0.1:5173',
		//: Fixed, because a screenshot baseline is meaningless at a viewport the
		//: next run might not have. The slot panel sizes its plot from the
		//: viewport, so this number is load-bearing for that panel specifically.
		viewport: { width: 1440, height: 900 },
		trace: 'retain-on-failure'
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	reporter: [['list']]
});
