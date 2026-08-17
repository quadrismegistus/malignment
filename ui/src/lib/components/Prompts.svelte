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
		{ key: 'js_median', label: 'movement', num: true, help: 'median JS divergence base→endpoint across those pairs' },
		{ key: 'departed_median', label: 'fallen', num: true, help: 'median mass leaving the words that fell' },
		{ key: 'arrived_median', label: 'risen', num: true, help: 'median mass arriving at the words that rose' },
		{ key: 'net_median', label: 'net', num: true, help: 'median (arrived − departed)' }
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

	function open(p: string) {
		selected = p;
		profile = null;
		profileLoading = true;
		api
			.prompt(p)
			.then((r) => (profile = r))
			.catch((e) => (error = e instanceof Error ? e.message : String(e)))
			.finally(() => (profileLoading = false));
	}

	let epView = $derived.by(() => {
		if (!profile) return [];
		const out = profile.endpoints.slice();
		out.sort((a, b) => {
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
	let wSort = $state<'word' | 'p_base' | 'p_aligned' | 'delta' | 'absdelta' | 'cls'>('delta');
	let wDesc = $state(false);

	function openPair(base: string, aligned: string) {
		pair = { base, aligned };
		pw = null;
		pwLoading = true;
		wSort = 'delta';
		wDesc = false;
		api
			.pairWords(selected as string, base, aligned)
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
		<p class="muted small">{selected}</p>
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

			<h3>words <span class="muted">{profile.movers_note}</span></h3>
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

			<h3>endpoints <span class="muted">{profile.endpoints.length} declared pairs measured here</span></h3>
			<div class="tablewrap">
				<table>
					<thead>
						<tr>
							{#each [['base', 'base'], ['aligned', 'aligned'], ['relation', 'relation'], ['js_total', 'movement'], ['departed', 'fallen'], ['arrived', 'risen'], ['n_fall', 'n fell'], ['n_rise', 'n rose'], ['resid_base', 'resid base'], ['resid_aligned', 'resid aligned']] as [k, l] (k)}
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
								<td title={e.base}>{short(e.base)}</td>
								<td title={e.aligned}>{short(e.aligned)}</td>
								<td>{e.relation}</td>
								<td class="num">{n(e.js_total)}</td>
								<td class="num">{n(e.departed)}</td>
								<td class="num">{n(e.arrived)}</td>
								<td class="num">{e.n_fall}</td>
								<td class="num">{e.n_rise}</td>
								<td class="num">{n(e.resid_base, 3)}</td>
								<td class="num">{n(e.resid_aligned, 3)}</td>
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
</style>
