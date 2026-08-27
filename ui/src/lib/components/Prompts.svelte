<!--
  Prompts — the frames, their categories, and how much each one moves.

  ── THE NUMBERS ARE A VIEW'S, NOT THIS PANEL'S ──────────────────────────────

  `js_median`, `departed_median` and `arrived_median` come from
  `{db}.prompt_movement`, a view defined in `malignment/views.py` beside the
  other rollups. Nothing is computed here or in the server: the medians have a
  producer, which is the difference between a number and a number-shaped thing.

  ── SORTING IS OVER THE WHOLE TABLE, WHICH IS WHY IT IS NOT CAPPED ──────────

  The server returns all 3,120 rows (~1 MB) rather than a page. A cap would make
  every sort a sort of an arbitrary window — the windowed-view-beside-an-
  unwindowed-statistic defect with the sort as the statistic — and "top 20 by
  movement" of a capped table is not the top 20.

  ── WHAT THE MEDIANS ARE OVER ──────────────────────────────────────────────

  `n_pairs` travels beside every median and is shown as a column, because a
  prompt measured on 9 lineages and one measured on 50 produce medians that look
  identical and are not comparable. Sorting by `js_median` without reading
  `n_pairs` is the most available mistake this table offers.
-->
<script lang="ts">
	import { api } from '$lib/api';
	import type { PromptRow, PromptProfile, PairWords } from '$lib/api';

	let rows = $state<PromptRow[]>([]);
	let computedAt = $state('');
	let undeclared = $state<number | null>(null);
	let loading = $state(true);
	let error = $state('');

	let filter = $state('');
	let sortKey = $state<keyof PromptRow>('js_median');
	let sortDesc = $state(true);

	let selected = $state<string | null>(null);
	let profile = $state<PromptProfile | null>(null);
	let profileLoading = $state(false);
	let epSort = $state<string>('js_total');
	let epDesc = $state(true);

	//: ── THE FIRST LOAD IS SLOW AND THE BAR IS AN ESTIMATE THAT SAYS SO.
	//:
	//: 14s is MEASURED, not guessed: 13.9s for the rollup and 14.7s end to end
	//: over 400,267 cells. But an estimate is all it is -- the server may be
	//: cold, another query may be running, and the cache may already be warm, in
	//: which case this returns in 0.022s.
	//:
	//: So the bar has two disciplines that a hardcoded timer usually lacks:
	//:
	//: 1. **IT NEVER REACHES 100% ON THE ESTIMATE.** It fills to 95% over the
	//:    expected time and then STOPS, because the only thing that knows the
	//:    work is done is the response arriving. A bar sitting full while the
	//:    request is still in flight is a progress bar lying about the one thing
	//:    it exists to report.
	//: 2. **IT DOES NOT FLASH ON A CACHED LOAD.** Nothing is drawn for the first
	//:    250ms, so the 0.022s cached path shows no bar at all rather than a
	//:    frame of one.
	const EXPECTED_MS = 14000;
	let startedAt = Date.now();
	let elapsed = $state(0);
	let ticker: ReturnType<typeof setInterval> | undefined;

	$effect(() => {
		if (!loading) {
			clearInterval(ticker);
			return;
		}
		ticker = setInterval(() => (elapsed = Date.now() - startedAt), 100);
		return () => clearInterval(ticker);
	});

	//: Capped at 95. See discipline 1.
	let pct = $derived(Math.min(95, (elapsed / EXPECTED_MS) * 95));
	let overdue = $derived(elapsed > EXPECTED_MS);
	let showBar = $derived(loading && elapsed > 250);

	api
		.prompts()
		.then((r) => {
			rows = r.rows;
			computedAt = r.computed_at ?? '';
			undeclared = r.n_measured_undeclared ?? null;
		})
		.catch((e) => (error = e instanceof Error ? e.message : String(e)))
		.finally(() => (loading = false));

	//: The columns, declared once. `num` drives both alignment and the sort
	//: comparator, so a column cannot be right-aligned and string-sorted.
	const COLS: { key: keyof PromptRow; label: string; num?: boolean; help?: string }[] = [
		{ key: 'prompt', label: 'prompt' },
		{ key: 'domain', label: 'domain' },
		{ key: 'subdomain', label: 'subdomain' },
		{ key: 'language', label: 'lang' },
		{ key: 'contrast_type', label: 'contrast' },
		{ key: 'source', label: 'source' },
		{ key: 'n_models', label: 'models', num: true, help: 'checkpoints with a twp cell at this prompt' },
		{ key: 'n_pairs', label: 'pairs', num: true, help: 'declared endpoint pairs measured here — the denominator of every median in this row' },
		{ key: 'js_median', label: 'movement', num: true, help: 'median JS divergence base→endpoint, raw→raw' },
		{ key: 'departed_median', label: 'fallen', num: true, help: 'median mass leaving the words that fell (raw→raw)' },
		{ key: 'arrived_median', label: 'risen', num: true, help: 'median mass arriving at the words that rose (raw→raw)' },
		{ key: 'net_median', label: 'net', num: true, help: 'median (arrived − departed), raw→raw' },
		{ key: 'xf_js_median', label: 'xf movement', num: true, help: 'median JS divergence raw-base → framed-aligned (system_mode=empty)' },
		{ key: 'xf_net_median', label: 'xf net', num: true, help: 'median (arrived − departed), cross-frame' }
	];

	function sortBy(k: keyof PromptRow) {
		if (sortKey === k) sortDesc = !sortDesc;
		else {
			sortKey = k;
			sortDesc = true;
		}
	}

	//: ── THE SAME TEXT CAN BE DECLARED TWICE, AND `prompt_id` IS THE KEY.
	//:
	//: 82 prompt texts appear twice in `{db}.prompts` (168 rows) under different
	//: ids, files and SOURCES -- `angry_want_run` (SETD, violence) and
	//: `store_g045_5` (OTHER, other) are the same stimulus declared in two
	//: files, with different `domain`. `prompt_id` is unique; the text is not.
	//:
	//: This surfaced as a Svelte `each_key_duplicate` crash, which was the
	//: cheapest possible way to find out. **The medians are unaffected** --
	//: checked, both views return exactly one row per prompt, so this is a
	//: duplicate DECLARATION and not a join fan-out.
	//:
	//: Marked rather than merged: the two rows carry different categories for
	//: one stimulus and the measurement is keyed on TEXT, so they show identical
	//: movement under different labels. Which of the two is right is a roster
	//: question, and a panel that silently picked one would be answering it.
	let dupText = $derived.by(() => {
		const seen = new Map<string, number>();
		for (const r of rows) seen.set(r.prompt, (seen.get(r.prompt) ?? 0) + 1);
		return new Set([...seen].filter(([, n]) => n > 1).map(([t]) => t));
	});

	let view = $derived.by(() => {
		const needle = filter.trim().toLowerCase();
		let out = needle
			? rows.filter((r) =>
					[r.prompt, r.domain, r.subdomain, r.family, r.source, r.contrast_type]
						.some((v) => (v ?? '').toLowerCase().includes(needle))
				)
			: rows.slice();
		const col = COLS.find((c) => c.key === sortKey);
		out.sort((a, b) => {
			const x = a[sortKey];
			const y = b[sortKey];
			//: **NULLS SORT LAST IN BOTH DIRECTIONS.** A prompt with no movement
			//: rows is not "the smallest movement", and letting it float to the
			//: top of an ascending sort would read as one.
			if (x == null && y == null) return 0;
			if (x == null) return 1;
			if (y == null) return -1;
			const c = col?.num ? Number(x) - Number(y) : String(x).localeCompare(String(y));
			return sortDesc ? -c : c;
		});
		return out;
	});

	let slopes = $state<any>(null);
	let slopesXf = $state<any>(null);
	let slopesLoading = $state(false);
	let chartTab = $state<'slopes' | 'slopes_xf' | 'dots'>('slopes');

	function open(p: string) {
		selected = p;
		profile = null;
		slopes = null;
		profileLoading = true;
		slopesLoading = true;
		api
			.prompt(p)
			.then((r) => (profile = r))
			.catch((e) => (error = e instanceof Error ? e.message : String(e)))
			.finally(() => (profileLoading = false));
		api
			.promptSlopes(p, 12)
			.then((r) => (slopes = r))
			.catch(() => (slopes = null))
			.finally(() => (slopesLoading = false));
		api
			.promptSlopes(p, 12, 'crossframe')
			.then((r) => (slopesXf = r))
			.catch(() => (slopesXf = null));
	}

	let epView = $derived.by(() => {
		if (!profile) return [];
		const xfByPair = new Map<string, any>();
		for (const x of profile.xf_endpoints ?? []) {
			xfByPair.set(x.base + '>' + x.aligned, x);
		}
		const out = profile.endpoints.map((e: any) => {
			const xf = xfByPair.get(e.base + '>' + e.aligned);
			return { ...e, xf_js_total: xf?.js_total ?? null, xf_departed: xf?.departed ?? null, xf_arrived: xf?.arrived ?? null };
		});
		out.sort((a: any, b: any) => {
			const x = (a as Record<string, unknown>)[epSort];
			const y = (b as Record<string, unknown>)[epSort];
			const c = typeof x === 'number' ? (x as number) - (y as number) : String(x).localeCompare(String(y));
			return epDesc ? -c : c;
		});
		return out;
	});
	function epSortBy(k: string) {
		if (epSort === k) epDesc = !epDesc;
		else {
			epSort = k;
			epDesc = true;
		}
	}
	//: ── LEVEL THREE: every word this pair puts at this prompt.
	//:
	//: **DEFAULT SORT IS `delta` ASCENDING**, so the biggest fallers are at the
	//: top — RH's spec, and the right default: the question this table exists to
	//: answer is what alignment took away. `absdelta` is a derived column for
	//: sorting by magnitude, computed HERE rather than served, because a column
	//: that is a function of another column in the same row is not a
	//: measurement and does not need a producer.
	let pair = $state<{ base: string; aligned: string } | null>(null);
	let pw = $state<PairWords | null>(null);
	let pwLoading = $state(false);
	let pairFrame = $state<string>("raw");
	let wSort = $state<'word' | 'p_base' | 'p_aligned' | 'delta' | 'absdelta' | 'cls'>('delta');
	let wDesc = $state(false);

	function openPair(base: string, aligned: string) {
		pair = { base, aligned };
		pw = null;
		pwLoading = true;
		wSort = 'delta';
		wDesc = false;
		api
			.pairWords(selected as string, base, aligned, pairFrame === "crossframe" ? "crossframe" : undefined)
			.then((r) => (pw = r))
			.catch((e) => (error = e instanceof Error ? e.message : String(e)))
			.finally(() => (pwLoading = false));
	}
	function wSortBy(k: typeof wSort) {
		if (wSort === k) wDesc = !wDesc;
		else {
			wSort = k;
			//: Magnitude and the two levels want DESCENDING first; `delta` wants
			//: ascending, because that is where the fallers are.
			wDesc = k !== 'delta' && k !== 'word' && k !== 'cls';
		}
	}
	let wView = $derived.by(() => {
		if (!pw) return [];
		const out = pw.words.map((w) => ({ ...w, absdelta: Math.abs(w.delta) }));
		out.sort((a, b) => {
			const x = (a as Record<string, unknown>)[wSort];
			const y = (b as Record<string, unknown>)[wSort];
			const c = typeof x === 'number' ? (x as number) - (y as number) : String(x).localeCompare(String(y));
			return wDesc ? -c : c;
		});
		return out;
	});

	//: ── THE INLINE SLOPEGRAPH.
	//:
	//: **SVG HERE RATHER THAN PLOTNINE, AND THE REASON IS THE DATA'S LOCATION.**
	//: The 145 rows are already in the browser, so this needs no round trip; the
	//: plotnine path exists for figures that must leave the app at 300 dpi. This
	//: one is for looking, and the table beneath it holds the exact numbers, so
	//: the drawing can be a SHAPE rather than a document.
	//:
	//: **IT IS NOT THE SAME OBJECT AS THE `prompt_slopes` FIGURE.** That one is a
	//: MEDIAN ACROSS LINEAGES with bootstrap intervals; this is ONE PAIR, one
	//: observation, no interval. Saying so on the panel, because two slopegraphs
	//: of the same prompt that differ in what a line means is exactly the
	//: confusion a reader cannot see.
	//:
	//: **THE SELECTION IS DECLARED.** Drawing 145 lines is an ink blot, so it
	//: draws the largest movers by |delta| and says how many of how many. A
	//: figure showing a subset without naming it is the defect this repo keeps
	//: booking.
	let showPlot = $state(true);
	let plotN = $state(25);
	let hoverW = $state<string | null>(null);

	let plot = $derived.by(() => {
		if (!pw || !pw.words.length) return null;
		const picked = pw.words
			.map((w) => ({ ...w, absdelta: Math.abs(w.delta) }))
			.sort((a, b) => b.absdelta - a.absdelta)
			.slice(0, plotN);
		//: The scale spans BOTH arms of the drawn words, so a line cannot leave
		//: the panel and the two columns share one axis. Zero is kept as the
		//: floor rather than clipped: a word going to exactly 0 is the result.
		const top = Math.max(...picked.flatMap((w) => [w.p_base, w.p_aligned]), 1e-9);
		const H = 260, W = 560, padT = 14, padB = 26, padL = 54, padR = 96;
		const y = (v: number) => padT + (1 - v / top) * (H - padT - padB);
		const x0 = padL, x1 = W - padR;
		//: Label collision is handled the same way the plotnine version does it:
		//: push apart in DATA SPACE from the top, moving text and leaving points.
		const ends = picked
			.map((w) => ({ word: w.word, v: w.p_aligned, d: w.delta }))
			.sort((a, b) => b.v - a.v);
		const gap = 11;
		let prev = -1e9;
		const labels = ends.map((e) => {
			let ly = y(e.v);
			if (ly - prev < gap) ly = prev + gap;
			prev = ly;
			return { ...e, ly };
		});
		return { picked, top, H, W, x0, x1, y, labels };
	});

	//: ── NUMERIC SURFACES ARE TRUNCATED, AND THE ORDERING IS NOT THE ORDERING.
	//:
	//: twp cuts a word at `,` and `.` between digits: every one of the roster's
	//: 159 tokenizers emits the separator as its own token, so `$100,000` is
	//: recorded as `100` (lacan, docket [6430], 159/159 with zero exceptions).
	//:
	//: **THE COLLAPSE IS NOT MONOTONE**, which is why this needs a fence rather
	//: than a footnote. `$100,000` and `$100` both become `100`; `$95,000`
	//: becomes `95`. So a panel row reading `100, 50, 1, 10, 200` -- the real top
	//: surfaces for an upper-class salary prompt -- puts what is almost certainly
	//: `$1,000,000` at `1`, below `200`. Sorting the display inverts the
	//: underlying magnitudes and looks like a class effect while doing it.
	//:
	//: The condition is EXACT, not a heuristic: a surface consisting only of
	//: digits is affected, and nothing else is. No prompt-sniffing, so no false
	//: positives and nothing to re-tune when v4 changes the rule.
	//:
	//: **THE FENCE USED TO PROMISE A FIX AND THAT HALF WAS WRONG** (docket [6449]).
	//: It read "two independent blockers, and the proposed fix reaches only one".
	//: The lookahead rule was then built, measured WORSE than v3 -- it spreads the
	//: amount over 25,000/25,500/25,750, each below theta, moving 90% of resolved
	//: mass into `drop` -- and REJECTED. v3's truncation is a MARGINALISATION, not
	//: an error: `25` at 0.0326 IS P(salary begins 25). Coarser and correct.
	//:
	//: So the caution to keep is the ORDERING, which is unchanged, and the one to
	//: delete is the pending-fix framing. A fence that says a repair is coming
	//: tells a reader to discount the number and wait; this one has to tell them
	//: the number is right and the sort is not.
	//: ── CJK BOUNDARY: which ARMS carry the double-crediting defect.
	//:
	//: On 84 of 133 models `boundary_mask` never marks CJK punctuation, so on a
	//: CJK prompt `expand` walks through `，` and credits a word at more than one
	//: depth; `clean_surface` then strips the punctuation, so the SURFACE looks
	//: correct and the probability behind it is double-counted (docket [6435]).
	//:
	//: **I concluded no fence was needed here and was wrong**, because I checked
	//: the surfaces and the surfaces are the layer that had been cleaned.
	//:
	//: Marked per ARM rather than per prompt, because the split is a property of
	//: the tokenizer family: 49 clean, 84 affected, 0 partial. A blanket warning
	//: on CJK prompts would flag the clean 49 too, and a fence that fires where
	//: nothing is wrong trains the reader past the ones that matter.
	const CJK = /[\u4e00-\u9fff]/;
	let cjkAffected = $state<Set<string>>(new Set());
	let cjkSource = $state<string | null>(null);
	let cjkKnown = $state(false);
	api
		.cjkBoundary()
		.then((r) => {
			cjkAffected = new Set(r.affected ?? []);
			cjkSource = r.source;
			//: The calibration answered. Absent file -> `source` null -> we do not
			//: claim anything either way.
			cjkKnown = !!r.source;
		})
		.catch(() => (cjkKnown = false));

	let promptIsCJK = $derived(!!selected && CJK.test(selected));
	let affectedArms = $derived.by(() => {
		if (!promptIsCJK || !cjkKnown || !profile) return [];
		return profile.endpoints
			.flatMap((e) => [e.base, e.aligned])
			.filter((m) => cjkAffected.has(m));
	});

	const NUMERIC = /^\d+$/;
	let numericWords = $derived.by(() => {
		const src = pw ? pw.words.map((w) => w.word) : [];
		return src.filter((w) => NUMERIC.test(w));
	});

	const n = (v: unknown, d = 4) => (v == null ? '—' : Number(v).toFixed(d));
	const short = (m: string) => m.split('/').pop() ?? m;
</script>

<div class="prompts">
	{#if !selected}
		<h2>Prompts <span class="muted">the frames, and how much each one moves</span></h2>
		{#if loading}
			{#if showBar}
				<div class="prog">
					<div class="track"><div class="fill" style="width: {pct}%"></div></div>
					<p class="muted">
						{#if overdue}
							still computing — longer than the usual {Math.round(EXPECTED_MS / 1000)}s
							({(elapsed / 1000).toFixed(0)}s so far). The rollup is 400,267 cells; it is
							cached once it lands.
						{:else}
							computing the rollup over 400,267 cells — about {Math.round(
								(EXPECTED_MS - elapsed) / 1000
							)}s left, then it is cached for 15 minutes
						{/if}
					</p>
				</div>
			{/if}
		{:else if error}
			<p class="bad">{error}</p>
		{:else}
			<div class="bar">
				<input class="filt" bind:value={filter} placeholder="filter prompt, domain, source…" />
				<span class="muted">{view.length} of {rows.length}</span>
				{#if computedAt}<span class="muted">rollup computed {computedAt}</span>{/if}
				{#if undeclared}
					<!--
					  THE GAP, STATED. The prompts TABLE declares these rows; the store
					  holds cells for more. A declared-only table read as the corpus is
					  the population defect one level up, so the count is on the panel
					  rather than in a comment.
					-->
					<span class="muted warn" title="prompts with twp cells that the roster's prompts table does not declare">
						+{undeclared} measured but undeclared
					</span>
				{/if}
			</div>

			<div class="tablewrap">
				<table>
					<thead>
						<tr>
							{#each COLS as c (c.key)}
								<th class:num={c.num} class:on={sortKey === c.key} title={c.help ?? ''}>
									<button onclick={() => sortBy(c.key)}>
										{c.label}{#if sortKey === c.key}<span class="dir">{sortDesc ? '▾' : '▴'}</span>{/if}
									</button>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each view.slice(0, 500) as r (r.prompt_id)}
							<tr onclick={() => open(r.prompt)}>
								<td class="p" title={r.prompt}>
									{r.prompt}{#if dupText.has(r.prompt)}<span
											class="dup"
											title="this text is declared more than once in the prompts table, under different ids and categories; the measurement is keyed on the text, so the movement columns are identical across them"
											>·2</span
										>{/if}
								</td>
								<td>{r.domain ?? ''}</td>
								<td>{r.subdomain ?? ''}</td>
								<td>{r.language ?? ''}</td>
								<td>{r.contrast_type ?? ''}</td>
								<td>{r.source ?? ''}</td>
								<td class="num">{r.n_models ?? '—'}</td>
								<td class="num">{r.n_pairs ?? '—'}</td>
								<td class="num">{n(r.js_median)}</td>
								<td class="num">{n(r.departed_median)}</td>
								<td class="num">{n(r.arrived_median)}</td>
								<td class="num">{n(r.net_median)}</td>
											<td class="num">{r.xf_js_median ? n(r.xf_js_median) : ''}</td>
											<td class="num">{r.xf_net_median ? n(r.xf_net_median) : ''}</td>
							</tr>
						{/each}
					</tbody>
				</table>
				{#if view.length > 500}
					<!--
					  A COUNT OF WHAT WAS DRAWN. The SORT is over all {rows.length};
					  only the rendering stops at 500, so the top of the table is the
					  real top and this says which number is which.
					-->
					<p class="muted cap">
						drawing the first 500 of {view.length} matched — the sort is over all of them, so
						this is the real top
					</p>
				{/if}
			</div>
		{/if}
	{:else if pair}
		<div class="bar">
			<button class="ghost" onclick={() => { pair = null; pw = null; }}>← {selected}</button>
			<button class="ghost" onclick={() => { pair = null; pw = null; selected = null; profile = null; }}>← all prompts</button>
		</div>
		<h2 class="pt">{short(pair.base)} → {short(pair.aligned)}</h2>
		<div class="frame-toggle">
			<button class:active={pairFrame === 'raw'} onclick={() => { pairFrame = 'raw'; openPair(pair.base, pair.aligned); }}>raw → raw</button>
			<button class:active={pairFrame === 'crossframe'} onclick={() => { pairFrame = 'crossframe'; openPair(pair.base, pair.aligned); }}>raw → framed</button>
		</div>
		<p class="muted small">{selected}{pairFrame === 'crossframe' ? ' (cross-frame, system_mode=empty)' : ''}</p>
		{#if pwLoading}
			<p class="muted">reading…</p>
		{:else if pw}
			<!--
			  THE APERTURE, ON THE PANEL. The two probability columns do NOT sum
			  to 1 and the gap is not the same on both arms. Shown as visible mass
			  plus residual so the books visibly close, rather than leaving a
			  reader to notice the columns fall short.
			-->
			<div class="meta">
				<span class="kv"><b>words</b> {pw.n_words}</span>
				<span class="kv"><b>visible mass</b> {n(pw.sum_p_base)} → {n(pw.sum_p_aligned)}</span>
				<span class="kv"><b>residual</b> {n(pw.residual_base)} → {n(pw.residual_aligned)}</span>
				<span class="kv"
					><b>closes to</b>
					{n((pw.sum_p_base ?? 0) + (pw.residual_base ?? 0))} / {n(
						(pw.sum_p_aligned ?? 0) + (pw.residual_aligned ?? 0)
					)}</span
				>
			</div>
			{#if promptIsCJK && cjkKnown && (cjkAffected.has(pw.base) || cjkAffected.has(pw.aligned))}
				<p class="fence">
					<strong>CJK prompt, and
						{cjkAffected.has(pw.base) && cjkAffected.has(pw.aligned)
							? 'both arms'
							: cjkAffected.has(pw.base)
								? 'the base arm'
								: 'the aligned arm'} does not mark CJK punctuation as a boundary.</strong>
					So <code>expand</code> walks through <code>，</code> and credits a word at more than one
					depth; <code>clean_surface</code> strips the punctuation, so the surfaces below look
					correct and some probabilities behind them are double-counted. 84 of 133 models are
					affected and 49 are not, so this is <strong>a reordering that differs by tokenizer
						family</strong> — <strong>but an UNMARKED arm is not a clean one</strong>. The 49
					models absent from that list are clean on the CJK marks lacan probed; malign's roster
					sweep finds <strong>88 of 88 tokenizers missing punctuation ids by the same mechanism,
						including all 36 SentencePiece</strong> (median 72 missed ids, 33 of them non-CJK —
					SentencePiece prefixes word-initial tokens with U+2581, so <code>_—</code> misses the em
					dash because the raw key is not the decoded key). The marking below is a floor, not a
					partition. Magnitude is not established at roster scale. On one model and three
					prompts, correcting the mask moves <strong>+15% to +28% of resolved mass on Chinese
						prompts</strong> and every word in the cell — this is recovery of mass that was
					bleeding into <code>drop</code>/<code>open</code>, not redistribution between words.
					<strong>English is not exempt</strong>: the corrected mask also marks
					<code>—</code> <code>–</code> <code>…</code> <code>·</code>, so English cells move too,
					by +0.12%. An earlier version of this fence said English was unaffected, which was true
					of the double-crediting symptom and false of the fix. See docket [6435], [6437],
					[6445]; classification from <code>{cjkSource}</code>.
				</p>
			{/if}
			{#if numericWords.length}
				<!--
				  THE FENCE TRAVELS WITH THE NUMBERS, not in a caption someone
				  strips. It appears only when a bare-digit surface is on screen,
				  which is an exact condition rather than a guess about the prompt.
				-->
				<p class="fence">
					<strong>{numericWords.length} of these surfaces are bare digits</strong> and twp cuts a
					word at <code>,</code> and <code>.</code> between digits — all 159 roster tokenizers emit
					the separator alone. So <code>100</code> may be <code>$100,000</code> or
					<code>$100</code>, and <code>1</code> may be <code>$1,000,000</code>.
					<strong>The collapse is not monotone</strong>: sorting these surfaces does not sort the
					underlying numbers, so a contrast built on them can reverse in sign.
					<strong>The coarseness is correct; the ordering is not</strong>. <code>100</code> is a
					PREFIX CLASS, not a number: read as <em>P(the amount begins 100)</em> it is a valid
					marginal, which is why the lookahead rule that would have split it was implemented,
					measured <strong>worse</strong> than this — it pushes 90% of resolved mass into
					<code>drop</code> — and rejected. So do not wait for a fix here; do not sort on these
					surfaces. <code>MAX_DEPTH</code> is now 9 and reaches <code>$100,000</code> at
					0.0317, but <strong>no v4 data is ingested</strong>, so every cell on this panel is
					v3. See docket [6430], [6440], [6449].
				</p>
			{/if}
			{#if plot}
				<div class="plotbar">
					<button class="ghost" onclick={() => (showPlot = !showPlot)}
						>{showPlot ? 'hide' : 'show'} slopegraph</button
					>
					{#if showPlot}
						<label class="nsel"
							>largest
							<select bind:value={plotN}>
								{#each [10, 25, 50, 100] as k (k)}<option value={k}>{k}</option>{/each}
							</select>
							movers of {pw.n_words}</label
						>
						<span class="muted"
							>one pair, one observation — not the median-across-lineages figure in Plots</span
						>
					{/if}
				</div>
			{/if}
			{#if plot && showPlot}
				<svg class="slope" viewBox="0 0 {plot.W} {plot.H}" role="img"
					aria-label="slopegraph of the largest movers">
					<line x1={plot.x0} y1={plot.y(0)} x2={plot.x1} y2={plot.y(0)} class="axis" />
					<text x={plot.x0} y={plot.H - 8} class="ax">{short(pw.base)}</text>
					<text x={plot.x1} y={plot.H - 8} class="ax" text-anchor="end">{short(pw.aligned)}</text>
					<text x={plot.x0 - 6} y={plot.y(plot.top) + 4} class="ax" text-anchor="end"
						>{plot.top.toFixed(3)}</text
					>
					<text x={plot.x0 - 6} y={plot.y(0) + 4} class="ax" text-anchor="end">0</text>
					{#each plot.picked as w (w.word)}
						<line
							x1={plot.x0} y1={plot.y(w.p_base)} x2={plot.x1} y2={plot.y(w.p_aligned)}
							class="sl" class:fell={w.delta < 0} class:rose={w.delta > 0}
							class:dim={hoverW !== null && hoverW !== w.word}
							class:hot={hoverW === w.word}
							onmouseenter={() => (hoverW = w.word)}
							onmouseleave={() => (hoverW = null)}
							role="presentation"
						/>
					{/each}
					{#each plot.labels as l (l.word)}
						<text
							x={plot.x1 + 6} y={l.ly + 3}
							class="wl" class:fell={l.d < 0} class:rose={l.d > 0}
							class:dim={hoverW !== null && hoverW !== l.word}
							onmouseenter={() => (hoverW = l.word)}
							onmouseleave={() => (hoverW = null)}
							role="presentation">{l.word}</text
						>
					{/each}
				</svg>
			{/if}

			<div class="tablewrap">
				<table>
					<thead>
						<tr>
							{#each [['word', 'word'], ['p_base', 'base'], ['p_aligned', 'aligned'], ['delta', 'delta'], ['absdelta', '|delta|'], ['cls', 'class']] as [k, l] (k)}
								<th class:on={wSort === k} class:num={k !== 'word' && k !== 'cls'}>
									<button onclick={() => wSortBy(k as typeof wSort)}>
										{l}{#if wSort === k}<span class="dir">{wDesc ? '▾' : '▴'}</span>{/if}
									</button>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each wView as w (w.word)}
							<tr class:fell={w.delta < 0} class:rose={w.delta > 0}>
								<td class="mono">{w.word}</td>
								<td class="num">{n(w.p_base, 5)}</td>
								<td class="num">{n(w.p_aligned, 5)}</td>
								<td class="num d">{w.delta > 0 ? '+' : ''}{n(w.delta, 5)}</td>
								<td class="num">{n(w.absdelta, 5)}</td>
								<td>{w.cls}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{:else}
		<div class="bar">
			<button class="ghost" onclick={() => { selected = null; profile = null; }}>← all prompts</button>
		</div>
		{#if profileLoading}
			<p class="muted">reading…</p>
		{:else if profile}
			<h2 class="pt">{profile.prompt}</h2>
			<div class="meta">
				{#each Object.entries(profile.meta) as [k, v] (k)}
					{#if v != null && v !== '' && k !== 'prompt'}
						<span class="kv"><b>{k}</b> {typeof v === 'number' ? n(v) : v}</span>
					{/if}
				{/each}
			</div>

			{#if profile.partners.length}
				<h3>related frames <span class="muted">same pair_id</span></h3>
				<div class="tablewrap">
					<table>
						<thead><tr><th>prompt</th><th>role</th><th class="num">pairs</th><th class="num">movement</th><th class="num">fallen</th><th class="num">risen</th></tr></thead>
						<tbody>
							{#each profile.partners as p (p.prompt)}
								<tr onclick={() => open(p.prompt)}>
									<td class="p">{p.prompt}</td><td>{p.pair_role ?? ''}</td>
									<td class="num">{p.n_pairs ?? '—'}</td><td class="num">{n(p.js_median)}</td>
									<td class="num">{n(p.departed_median)}</td><td class="num">{n(p.arrived_median)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}

			<h3>words — raw→raw <span class="muted">{profile.movers_note}</span></h3>
			<div class="movers">
				<div>
					<span class="lbl rise">risen</span>
					{#each profile.top_risers as w (w.word)}
						<span class="w">{w.word} <b>{w.d > 0 ? '+' : ''}{n(w.d, 3)}</b></span>
					{/each}
				</div>
				<div>
					<span class="lbl fall">fallen</span>
					{#each profile.top_fallers as w (w.word)}
						<span class="w">{w.word} <b>{n(w.d, 3)}</b></span>
					{/each}
				</div>
			</div>
			{#if profile.xf_top_risers?.length || profile.xf_top_fallers?.length}
				<h3>words — cross-frame <span class="muted">raw base → framed aligned (system_mode=empty)</span></h3>
				<div class="movers">
					<div>
						<span class="lbl rise">risen</span>
						{#each profile.xf_top_risers ?? [] as w (w.word)}
							<span class="w">{w.word} <b>{w.d > 0 ? '+' : ''}{n(w.d, 3)}</b></span>
						{/each}
					</div>
					<div>
						<span class="lbl fall">fallen</span>
						{#each profile.xf_top_fallers ?? [] as w (w.word)}
							<span class="w">{w.word} <b>{n(w.d, 3)}</b></span>
						{/each}
					</div>
				</div>
			{/if}

			{@const hasSlopes = slopes && slopes.levels?.length}
			{@const hasSlopesXf = slopesXf && slopesXf.levels?.length}
			{@const hasDots = epView.length > 1}
			{#if hasSlopes || hasSlopesXf || hasDots}
				<div class="chart-tabs">
					{#if hasSlopes}
						<button class:active={chartTab === 'slopes'} onclick={() => chartTab = 'slopes'}>slopegraph</button>
					{/if}
					{#if hasSlopesXf}
						<button class:active={chartTab === 'slopes_xf'} onclick={() => chartTab = 'slopes_xf'}>slopegraph (framed)</button>
					{/if}
					{#if hasDots}
						<button class:active={chartTab === 'dots'} onclick={() => chartTab = 'dots'}>movement by lineage</button>
					{/if}
				</div>
			{/if}

			{@const activeSlopes = chartTab === 'slopes_xf' ? slopesXf : slopes}
			{#if (chartTab === 'slopes' || chartTab === 'slopes_xf') && activeSlopes && activeSlopes.levels?.length}
				{@const W = 560}
				{@const H = 280}
				{@const padT = 18}
				{@const padB = 30}
				{@const padL = 58}
				{@const padR = 100}
				{@const top = Math.max(...activeSlopes.levels.map((l) => l.hi), 0.001)}
				{@const floor = 0.0005}
				{@const logTop = Math.log10(top)}
				{@const logFloor = Math.log10(floor)}
				{@const y = (v) => {
					const lv = Math.log10(Math.max(v, floor));
					return padT + (logTop - lv) / (logTop - logFloor) * (H - padT - padB);
				}}
				{@const x0 = padL}
				{@const x1 = W - padR}
				{@const faller = activeSlopes.diffs[0]?.word}
				{@const riser = activeSlopes.diffs[activeSlopes.diffs.length - 1]?.word}
				{@const endLabels = (() => {
					const ends = activeSlopes.levels
						.filter((l) => l.position === 1)
						.map((l) => ({ word: l.word, v: l.central,
							role: l.word === faller ? 'faller' : l.word === riser ? 'riser' : 'other' }))
						.sort((a, b) => b.v - a.v);
					const gap = 12;
					let prev = -1e9;
					return ends.map((e) => {
						let ly = y(e.v);
						if (ly - prev < gap) ly = prev + gap;
						prev = ly;
						return { ...e, ly };
					});
				})()}
				{@const diffMap = new Map(activeSlopes.diffs.map((d) => [d.word, d.d]))}
				{@const logTicks = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3].filter((t) => t >= floor && t <= top * 1.1)}
				<h3>slopegraph <span class="muted">{activeSlopes.selection}, {activeSlopes.n_units} lineages, median with 95% CI</span></h3>
				<svg class="slopegraph" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">
					<text x={x0} y={H - 8} font-size="10" fill="#888">base</text>
					<text x={x1} y={H - 8} font-size="10" fill="#888" text-anchor="end">aligned</text>
					{#each logTicks as tick}
						<line x1={x0} x2={x1} y1={y(tick)} y2={y(tick)} stroke="#444" stroke-width="0.3" />
						<text x={x0 - 6} y={y(tick) + 3} font-size="7" fill="#888" text-anchor="end">{tick < 0.01 ? tick.toFixed(3) : tick.toFixed(2)}</text>
					{/each}
					{#each activeSlopes.words as w}
						{@const base = activeSlopes.levels.find((l) => l.word === w && l.position === 0)}
						{@const aligned = activeSlopes.levels.find((l) => l.word === w && l.position === 1)}
						{@const wd = diffMap.get(w) ?? 0}
						{@const isTopFaller = w === faller}
						{@const isTopRiser = w === riser}
						{@const col = wd < 0 ? '#e15759' : '#4e79a7'}
						{@const opac = (isTopFaller || isTopRiser) ? 0.95 : 0.35}
						{@const sw = (isTopFaller || isTopRiser) ? 2.5 : 1.2}
						{#if base && aligned}
							<line x1={x0} y1={y(base.central)} x2={x1} y2={y(aligned.central)}
								stroke={col} stroke-width={sw} opacity={opac} />
							<line x1={x0} x2={x0} y1={y(base.lo)} y2={y(base.hi)}
								stroke={col} stroke-width="1" opacity={opac * 0.7} />
							<line x1={x1} x2={x1} y1={y(aligned.lo)} y2={y(aligned.hi)}
								stroke={col} stroke-width="1" opacity={opac * 0.7} />
							<circle cx={x0} cy={y(base.central)} r={role === 'other' ? 2 : 3}
								fill={col} opacity={opac} />
							<circle cx={x1} cy={y(aligned.central)} r={role === 'other' ? 2 : 3}
								fill={col} opacity={opac} />
						{/if}
					{/each}
					{#each endLabels as l}
						{@const ld = diffMap.get(l.word) ?? 0}
						{@const isTop = l.word === faller || l.word === riser}
						<text x={x1 + 6} y={l.ly + 3} font-size="9"
							fill={ld < 0 ? '#e15759' : '#4e79a7'}
							opacity={isTop ? 1 : 0.5}
							font-weight={isTop ? 'bold' : 'normal'}
						>{l.word}</text>
					{/each}
				</svg>
				{#if activeSlopes.diffs.length >= 2}
					<p class="muted small">
						largest faller <b style="color:#e15759">{faller}</b> {activeSlopes.diffs[0].d > 0 ? '+' : ''}{n(activeSlopes.diffs[0].d, 4)} [{n(activeSlopes.diffs[0].lo, 4)}, {n(activeSlopes.diffs[0].hi, 4)}]
						· largest riser <b style="color:#4e79a7">{riser}</b> +{n(activeSlopes.diffs[activeSlopes.diffs.length-1].d, 4)} [{n(activeSlopes.diffs[activeSlopes.diffs.length-1].lo, 4)}, {n(activeSlopes.diffs[activeSlopes.diffs.length-1].hi, 4)}]
						· intervals on the paired within-lineage difference
					</p>
				{/if}
			{/if}

			{#if chartTab === 'dots' && epView.length > 1}
				{@const maxJs = Math.max(...epView.map((e) => Math.max(e.js_total ?? 0, e.xf_js_total ?? 0)), 0.01)}
				{@const dotW = 500}
				{@const dotH = Math.max(80, epView.length * 8 + 30)}
				{@const dotX = (v) => 40 + (v / maxJs) * (dotW - 80)}
				{@const sorted = epView.slice().sort((a, b) => (b.js_total ?? 0) - (a.js_total ?? 0))}
				<h3>movement by lineage <span class="muted">blue = raw→raw, red = cross-frame</span></h3>
				<svg viewBox="0 0 {dotW} {dotH}" class="dotstrip" preserveAspectRatio="xMidYMid meet">
					<line x1={dotX(0)} x2={dotX(0)} y1="14" y2={dotH - 12} stroke="#555" stroke-width="0.5" />
					<text x={dotX(0)} y="10" text-anchor="middle" font-size="8" fill="#888">0</text>
					<text x={dotX(maxJs)} y="10" text-anchor="middle" font-size="8" fill="#888">{maxJs.toFixed(2)}</text>
					{#each sorted as e, i}
						{@const y = 20 + i * ((dotH - 34) / Math.max(sorted.length - 1, 1))}
						{#if e.xf_js_total}
							<line x1={dotX(e.js_total)} x2={dotX(e.xf_js_total)} y1={y} y2={y}
								stroke="#e1575944" stroke-width="1" />
							<circle cx={dotX(e.xf_js_total)} cy={y} r="2.5" fill="#e15759" opacity="0.6" />
						{/if}
						<circle cx={dotX(e.js_total)} cy={y} r="2.5" fill="#4e79a7" opacity="0.7" />
					{/each}
				</svg>
			{/if}

			<h3>
				endpoints <span class="muted">{profile.endpoints.length} declared pairs measured here</span>
				{#if promptIsCJK && cjkKnown && affectedArms.length}
					<span class="muted warn"
						>· {affectedArms.length} arm{affectedArms.length > 1 ? 's' : ''} marked
						<code>cjk</code> miss CJK punctuation — and an unmarked arm is not clean, it is
						untested on other marks (88 of 88 tokenizers miss some; docket [6447])</span
					>
				{/if}
			</h3>
			<div class="tablewrap">
				<table>
					<thead>
						<tr>
							{#each [['base', 'base'], ['aligned', 'aligned'], ['relation', 'relation'], ['js_total', 'movement'], ['departed', 'fallen'], ['arrived', 'risen'], ['n_fall', 'n fell'], ['n_rise', 'n rose'], ['resid_base', 'resid base'], ['resid_aligned', 'resid aligned'], ['xf_js_total', 'xf movement']] as [k, l] (k)}
								<th class:on={epSort === k} class:num={k !== 'base' && k !== 'aligned' && k !== 'relation'}>
									<button onclick={() => epSortBy(k)}>
										{l}{#if epSort === k}<span class="dir">{epDesc ? '▾' : '▴'}</span>{/if}
									</button>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each epView as e (e.base + e.aligned)}
							<tr class="click" onclick={() => openPair(e.base, e.aligned)}>
								<td title={e.base}
									>{short(e.base)}{#if promptIsCJK && cjkKnown && cjkAffected.has(e.base)}<span
											class="cjkmark"
											title="this arm does not mark CJK punctuation as a boundary, so some word probabilities on this CJK prompt are double-counted (docket [6435]). An UNMARKED arm is not clean: 88 of 88 tokenizers miss punctuation ids by the same mechanism, including all SentencePiece (docket [6447]) — this marking is a floor, not a partition."
											>cjk</span
										>{/if}</td
								>
								<td title={e.aligned}
									>{short(e.aligned)}{#if promptIsCJK && cjkKnown && cjkAffected.has(e.aligned)}<span
											class="cjkmark"
											title="this arm does not mark CJK punctuation as a boundary, so some word probabilities on this CJK prompt are double-counted — docket [6435]"
											>cjk</span
										>{/if}</td
								>
								<td>{e.relation}</td>
								<td class="num">{n(e.js_total)}</td>
								<td class="num">{n(e.departed)}</td>
								<td class="num">{n(e.arrived)}</td>
								<td class="num">{e.n_fall}</td>
								<td class="num">{e.n_rise}</td>
								<td class="num">{n(e.resid_base, 3)}</td>
								<td class="num">{n(e.resid_aligned, 3)}</td>
								<td class="num">{e.xf_js_total ? n(e.xf_js_total) : ''}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

		{/if}
	{/if}
</div>

<style>
	.prompts { max-width: none; }
	h2 { font-size: 15px; margin: 0 0 6px; font-weight: 600; }
	h2.pt { font-family: var(--mono); font-size: 14px; }
	h3 { font-size: 12px; margin: 18px 0 6px; font-weight: 600; }
	h2 .muted, h3 .muted { font-weight: 400; font-size: 11px; }
	.muted { color: var(--text-2); }
	.muted.warn { color: var(--amber, #b8860b); }
	.bad { color: var(--bad, #c92a2a); font-size: 12px; }
	.bar { display: flex; gap: 14px; align-items: center; margin: 8px 0; flex-wrap: wrap; font-size: 11px; }
	.filt {
		flex: 0 1 320px; padding: 5px 8px; background: var(--panel);
		border: 1px solid var(--rule); border-radius: 4px; color: var(--text); font-size: 12px;
	}
	.tablewrap { overflow-x: auto; border: 1px solid var(--rule); border-radius: 4px; }
	table { border-collapse: collapse; width: 100%; font-size: 11px; }
	th { text-align: left; border-bottom: 1px solid var(--rule); background: var(--panel); position: sticky; top: 0; }
	th button {
		background: none; border: 0; color: var(--text-2); font: inherit; cursor: pointer;
		padding: 6px 8px; width: 100%; text-align: inherit;
	}
	th.on button { color: var(--blue-light); }
	th.num, td.num { text-align: right; font-family: var(--mono); }
	.dir { margin-left: 3px; }
	td { padding: 4px 8px; border-bottom: 1px solid var(--rule); }
	tbody tr { cursor: pointer; }
	tbody tr:hover { background: var(--panel); }
	td.p { max-width: 460px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--mono); }
	.cap { font-size: 11px; padding: 6px 8px; margin: 0; }
	.meta { display: flex; gap: 14px; flex-wrap: wrap; font-size: 11px; margin: 4px 0 6px; }
	.kv b { color: var(--text-2); font-weight: 500; margin-right: 4px; }
	.movers { display: flex; gap: 28px; flex-wrap: wrap; font-size: 11px; }
	.movers .lbl { text-transform: uppercase; font-size: 10px; letter-spacing: 0.04em; margin-right: 8px; }
	.movers .rise { color: var(--blue-light); }
	.movers .fall { color: var(--red, #c92a2a); }
	.movers .w { font-family: var(--mono); margin-right: 12px; }
	.fence {
		margin: 10px 0; padding: 8px 10px; font-size: 11px; line-height: 1.5;
		border: 1px solid var(--amber, #b8860b); border-radius: 4px;
		color: var(--text-2); max-width: 92ch;
	}
	.fence strong { color: var(--amber, #b8860b); }
	.cjkmark {
		margin-left: 5px; font-size: 9px; padding: 0 3px; border-radius: 2px;
		border: 1px solid var(--amber, #b8860b); color: var(--amber, #b8860b);
		font-family: var(--mono); cursor: help;
	}
	.fence code { font-family: var(--mono); }
	.plotbar { display: flex; gap: 14px; align-items: center; margin: 12px 0 4px; font-size: 11px; flex-wrap: wrap; }
	.nsel select {
		background: var(--panel); border: 1px solid var(--rule); border-radius: 3px;
		color: var(--text); font-size: 11px; padding: 2px 4px; margin: 0 2px;
	}
	.slope { width: 100%; max-width: 900px; height: auto; display: block; margin-bottom: 10px; }
	.slope .axis { stroke: var(--rule); stroke-width: 0.6; }
	.slope .ax { fill: var(--text-2); font-size: 8px; font-family: var(--mono); }
	.slope .sl { stroke-width: 1.1; opacity: 0.75; cursor: pointer; }
	.slope .sl.fell { stroke: var(--red, #c92a2a); }
	.slope .sl.rose { stroke: var(--blue-light); }
	.slope .sl.dim { opacity: 0.12; }
	.slope .sl.hot { stroke-width: 2.4; opacity: 1; }
	.slope .wl { font-size: 8px; font-family: var(--mono); cursor: pointer; }
	.slope .wl.fell { fill: var(--red, #c92a2a); }
	.slope .wl.rose { fill: var(--blue-light); }
	.slope .wl.dim { opacity: 0.25; }
	.prog { margin: 14px 0; max-width: 520px; }
	.track {
		height: 4px; background: var(--panel); border: 1px solid var(--rule);
		border-radius: 3px; overflow: hidden;
	}
	.fill {
		height: 100%; background: var(--blue-light);
		/* Matches the tick, so the bar moves smoothly rather than in steps. */
		transition: width 0.1s linear;
	}
	.prog p { font-size: 11px; margin: 6px 0 0; }
	.small { font-family: var(--mono); font-size: 11px; margin: 0 0 8px; }
	tr.click { cursor: pointer; }
	td.mono { font-family: var(--mono); }
	td.d { font-weight: 600; }
	tr.fell td.d { color: var(--red, #c92a2a); }
	tr.rose td.d { color: var(--blue-light); }
	.dup {
		margin-left: 6px; font-size: 9px; padding: 1px 4px; border-radius: 3px;
		border: 1px solid var(--amber, #b8860b); color: var(--amber, #b8860b);
		font-family: var(--mono); cursor: help;
	}

	.frame-toggle { display: flex; gap: 2px; margin: 4px 0; }
	.frame-toggle button {
		background: var(--panel-2, #333); border: 1px solid var(--rule, #555);
		border-radius: 4px; padding: 2px 10px; cursor: pointer;
		font-size: 0.75rem; color: var(--text-3);
	}
	.chart-tabs { display: flex; gap: 2px; margin: 8px 0 4px; }
	.chart-tabs button {
		background: var(--panel-2, #333); border: 1px solid var(--rule, #555);
		border-radius: 4px 4px 0 0; padding: 3px 12px; cursor: pointer;
		font-size: 0.75rem; color: var(--text-3);
	}
	.chart-tabs button.active {
		background: var(--panel, #1a1a2e); border-bottom-color: transparent;
		color: var(--text); font-weight: 600;
	}
	.slopegraph { display: block; width: 100%; max-width: 560px; margin: 4px 0 8px; }
	.dotstrip { display: block; width: 100%; max-width: 500px; margin: 4px 0 8px; }
	.frame-toggle button.active {
		background: var(--blue, #4e79a7); color: #fff; border-color: var(--blue);
	}
</style>
