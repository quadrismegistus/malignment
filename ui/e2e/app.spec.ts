import { test, expect, type Page, type ConsoleMessage } from '@playwright/test';

//: ── EVERY ASSERTION HERE TRACES TO A BUG THAT SHIPPED ───────────────────────
//:
//: Not a coverage exercise. Each check is the cheapest thing that would have
//: caught a specific failure on 2026-08-17, named beside it, because a test
//: whose motivating failure nobody can state is the first one deleted.

const PANELS = ['experiments', 'roster', 'prompts', 'slot', 'plots'] as const;

/** Errors the page reported about itself. */
function watch(page: Page) {
	const errors: string[] = [];
	const failed: string[] = [];
	//: **`pageerror` CATCHES THE CRASH `console.error` MISSES.** The Prompts
	//: table died on `each_key_duplicate`, which Svelte throws — so it arrives as
	//: an uncaught exception, not as a logged message.
	page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
	page.on('console', (m: ConsoleMessage) => {
		if (m.type() === 'error') errors.push(`console: ${m.text()}`);
	});
	//: **THE ONE THAT WOULD HAVE CAUGHT THE BROKEN IMAGE.** A 404 on an <img>
	//: logs no JS error and throws nothing: the render had succeeded, the
	//: filename was right, every number beside it was correct, and the only
	//: evidence was a request that failed.
	//:
	//: **IT DOES NOT CATCH DOCUMENT-LEVEL ASSETS.** An earlier version of this
	//: comment claimed the favicon too; renaming `static/favicon.svg` and running
	//: the suite showed it passing, because a favicon is fetched by the browser
	//: outside the page's request lifecycle. In-page requests only.
	page.on('requestfailed', (r) => failed.push(`${r.method()} ${r.url()}`));
	page.on('response', (r) => {
		if (r.status() >= 400) failed.push(`HTTP ${r.status()} ${r.url()}`);
	});
	return { errors, failed };
}

test.beforeAll(async ({ request }) => {
	//: **REACHABILITY FIRST, WITH A SENTENCE.** The dev server proxies `/api` to
	//: the Python server, so with the API down every panel renders its error
	//: state perfectly and a screenshot baseline would record that as the truth.
	//: A suite that silently blesses the broken state is worse than no suite.
	const r = await request.get('/api/health').catch(() => null);
	if (!r || !r.ok()) {
		throw new Error(
			'the API server is not answering on /api/health. Start it with ' +
				'`python -m malignment.serve --port 8431` (the dev server proxies /api to it). ' +
				'Refusing to screenshot the error state as a baseline.'
		);
	}
	const h = await r.json();
	//: A STALE SERVER MAKES EVERY BASELINE A LIE about code that is on disk.
	//: The badge exists for humans; this is the same fact asserted.
	expect(h.source?.stale, `server is stale: ${(h.source?.changed ?? []).join(', ')}`).not.toBe(
		true
	);
});

for (const panel of PANELS) {
	test(`${panel}: no page errors, no failed requests, stable render`, async ({ page }) => {
		const seen = watch(page);
		await page.goto('/');
		//: The nav labels are the app's own, so this fails loudly if a section is
		//: renamed rather than silently testing nothing.
		await page.getByRole('button', { name: new RegExp(panel, 'i') }).first().click();

		if (panel === 'prompts') {
			//: The uncached rollup is a measured 14s. Waiting for the table rather
			//: than a fixed sleep, because a sleep that is too short reports a
			//: loading spinner as the panel.
			await expect(page.locator('table')).toBeVisible({ timeout: 60_000 });
		} else if (panel === 'plots') {
			await expect(page.getByRole('button', { name: /draw/i })).toBeVisible();
		} else {
			await page.waitForLoadState('networkidle');
		}
		//: Settle animations and the measured plot fit before the pixels are read.
		await page.waitForTimeout(600);

		expect(seen.errors, `page reported errors:\n${seen.errors.join('\n')}`).toEqual([]);
		expect(seen.failed, `requests failed:\n${seen.failed.join('\n')}`).toEqual([]);
		await expect(page).toHaveScreenshot(`${panel}.png`, { fullPage: false });
	});
}

test('prompts: drilling to a pair renders the word table and the slopegraph', async ({ page }) => {
	//: THE DEEPEST PATH, because it is where the most recent work is and where
	//: the broken <img> class of bug lives — three levels of navigation, each
	//: fetching, and the last one drawing.
	const seen = watch(page);
	await page.goto('/');
	await page.getByRole('button', { name: /prompts/i }).first().click();
	await expect(page.locator('table')).toBeVisible({ timeout: 60_000 });

	await page.locator('tbody tr').first().click();
	await expect(page.getByRole('heading', { level: 3, name: /endpoints/i })).toBeVisible({
		timeout: 30_000
	});

	//: The endpoints table is the LAST table on the profile, and clicking one of
	//: its rows is the third level. Chosen by position rather than by content so
	//: the test does not depend on which pair happens to move most.
	await page.locator('table').last().locator('tbody tr').first().click();
	await expect(page.locator('svg.slope')).toBeVisible({ timeout: 30_000 });
	//: A slopegraph with no lines is a blank panel that passes a visibility check.
	expect(await page.locator('svg.slope line.sl').count()).toBeGreaterThan(1);

	expect(seen.errors, `page reported errors:\n${seen.errors.join('\n')}`).toEqual([]);
	expect(seen.failed, `requests failed:\n${seen.failed.join('\n')}`).toEqual([]);
	await expect(page).toHaveScreenshot('pair-words.png', { fullPage: false });
});
