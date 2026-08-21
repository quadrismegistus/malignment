<!--
  14,414 passages on a two-axis plane, filterable, with any point openable.

  ## WHY THE CANVAS ENTRY POINT AND NOT SVG

  `layerchart/canvas` is the same component set rendered canvas-native, so this
  is LayerChart throughout rather than a hand-rolled canvas beside it. At 14,414
  points the SVG path would be 14,414 DOM nodes; the canvas one is a single
  element and LayerChart still supplies the scales, the tooltip hit-testing and
  the brush.

  ## THE DETAIL IS FETCHED, NOT SHIPPED

  Behind these points are 3,040,970 word rows and 196,349 sentence rows. The
  artifact carries only what the plane needs plus each point's id; opening one
  passage fetches its two decompositions from the route the ARTIFACT names in
  `detail.url`. The colour domain for those quantities is the artifact's too:
  a component that picks its own is deciding what counts as surprising.
-->
<script lang="ts">
	import { ScatterChart } from 'layerchart/canvas';

	type Art = {
		title: string;
		subtitle?: string;
		x: { key: string; label: string; note?: string; domain: [number, number] };
		y: { key: string; label: string; note?: string; domain: [number, number] };
		cats: { key: string; label: string; colour: string; kind: string; n: number }[];
		models: string[];
		points: { ids: string[]; x: number[]; y: number[]; cat: number[]; model: number[] };
		cells: { key: string; label: string; pooled: number }[];
		table: { cat: string; n: number; pct: Record<string, number>; enrich: Record<string, number> }[];
		detail?: { url?: string; scales?: Record<string, { domain: [number, number]; note: string }> };
		notes?: string[];
	};
	let { art }: { art: Art } = $props();

	const BASE = import.meta.env.DEV ? '/api' : '';

	//: Expanded ONCE. The artifact ships columns because field names repeated
	//: 14,414 times are four fifths of the file; LayerChart wants records.
	const rows = $derived.by(() => {
		const p = art.points;
		return p.ids.map((id, i) => ({
			id,
			x: p.x[i],
			y: p.y[i],
			cat: art.cats[p.cat[i]].key,
			model: art.models[p.model[i]]
		}));
	});

	let hideCat = $state<string[]>([]);
	let model = $state('');
	const visible = $derived(
		rows.filter((r) => !hideCat.includes(r.cat) && (!model || r.model === model))
	);

	//: One series per category, which is how ScatterChart colours points and how
	//: its tooltip knows what it is over. Empty series are dropped rather than
	//: passed: a series with no data still claims a legend slot downstream.
	const series = $derived(
		art.cats
			.map((c) => ({
				key: c.key,
				label: c.label,
				color: c.colour,
				data: visible.filter((r) => r.cat === c.key)
			}))
			.filter((s) => s.data.length)
	);

	const nByCat = $derived.by(() => {
		const m = new Map<string, number>();
		for (const r of visible) m.set(r.cat, (m.get(r.cat) ?? 0) + 1);
		return m;
	});

	//: NOT `$state`, AND NOT `bind:context`. The canvas ScatterChart takes
	//: `$props()` without destructuring a bindable `context`, so only the SVG
	//: variant can be bound -- and the SVG variant is the 14,414-DOM-node one
	//: this component exists to avoid. The tooltip snippet is handed the context
	//: on every pointer move, so the hovered datum is captured there instead.
	//:
	//: A plain `let` on purpose: the click handler needs the VALUE, not a
	//: dependency, and making it reactive would re-render the chart on every
	//: pointer move to update something nothing renders.
	let hovered: any = null;

	/** Record what the pointer is over, and hand it back so the tooltip can draw it. */
	function capture(d: any) {
		hovered = d ?? null;
		return d;
	}

	//: ── ONE PASSAGE ─────────────────────────────────────────────────────────
	let openId = $state<string | null>(null);
	let detail = $state<any>(null);
	let detailErr = $state<string | null>(null);

	$effect(() => {
		const id = openId;
		if (!id || !art.detail?.url) return;
		let dead = false;
		detail = null;
		detailErr = null;
		(async () => {
			try {
				const r = await fetch(`${BASE}${art.detail!.url}?id=${encodeURIComponent(id)}`);
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				const j = await r.json();
				if (!dead) detail = j;
			} catch (e) {
				if (!dead) detailErr = e instanceof Error ? e.message : String(e);
			}
		})();
		return () => {
			dead = true;
		};
	});

	//: CLICK READS LAYERCHART'S OWN HIT TEST. `context.tooltip.data` is the datum
	//: the tooltip is already tracking, so the point that opens is the point the
	//: reader saw highlighted -- a second nearest-point search of my own could
	//: disagree with it at the exact moments the points are dense.
	function openHovered() {
		if (hovered?.id) openId = hovered.id;
	}

	//: ── JOINING THE TWO GRAINS, WHICH IS EXACT AND WAS CHECKED ───────────────
	//:
	//: Words carry no sentence key. They can still be assigned exactly, because
	//: each sentence declares `n_words` and those sum to the passage's NON-PARTIAL
	//: word count for 14,414 of 14,414 passages. The one partial word is always
	//: `word_index` 0 -- the leading fragment left by taking surprisal at a fixed
	//: token prefix -- and belongs to no sentence, so it is rendered ahead of the
	//: first one rather than folded into it.
	//:
	//: The walk asserts as it goes: if a sentence runs out of words the render
	//: SAYS so instead of silently shortening the passage.
	const reading = $derived.by(() => {
		if (!detail?.words || !detail?.sentences) return null;
		const words = [...detail.words].sort((a: any, b: any) => a.word_index - b.word_index);
		const lead = words.filter((w: any) => w.partial);
		const body = words.filter((w: any) => !w.partial);
		let k = 0;
		const sents = detail.sentences.map((s: any) => {
			const take = body.slice(k, k + s.n_words);
			k += s.n_words;
			return { ...s, words: take, short: take.length < s.n_words };
		});
		return { lead, sents, leftover: body.length - k };
	});

	const bitsDom = $derived(art.detail?.scales?.bits?.domain ?? [0, 16]);
	const stepDom = $derived(art.detail?.scales?.step?.domain ?? [0, 0.8]);
	const heat = (b: number) => {
		const t = Math.max(0, Math.min(1, (b - bitsDom[0]) / (bitsDom[1] - bitsDom[0])));
		//: Alpha only, over the page's own background, so the word stays readable
		//: at every value. A hue ramp here would compete with the category
		//: colours the plane above is already using for a different variable.
		return `rgba(232, 89, 12, ${(0.06 + 0.62 * t).toFixed(3)})`;
	};

	const fmt = (v: number, d = 2) => (v == null ? '—' : v.toFixed(d));
	const clearFilters = () => {
		hideCat = [];
		model = '';
	};
	const toggleCat = (k: string) =>
		(hideCat = hideCat.includes(k) ? hideCat.filter((x) => x !== k) : [...hideCat, k]);
</script>

<figure class="qm">
	<figcaption>
		<h3>{art.title}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="controls">
		<span class="count"
			><strong>{visible.length.toLocaleString()}</strong> of {rows.length.toLocaleString()} passages</span
		>
		<label>
			model
			<select bind:value={model}>
				<option value="">all {art.models.length}</option>
				{#each art.models as m (m)}<option value={m}>{m}</option>{/each}
			</select>
		</label>
		{#if hideCat.length || model}
			<button onclick={clearFilters}>clear filters</button>
		{/if}
	</div>

	<div class="legend">
		{#each ['ai', 'human'] as kind (kind)}
			<span class="kind">{kind === 'ai' ? 'models' : 'human corpora'}</span>
			{#each art.cats.filter((c) => c.kind === kind) as c (c.key)}
				<button
					class="key"
					class:off={hideCat.includes(c.key)}
					aria-pressed={!hideCat.includes(c.key)}
					onclick={() => toggleCat(c.key)}
				>
					<i style:background={c.colour}></i>{c.label}
					<em>{(nByCat.get(c.key) ?? 0).toLocaleString()}</em>
				</button>
			{/each}
		{/each}
	</div>

	<!--
	  The tooltip snippet is also where the hovered datum is captured, because the
	  canvas chart exposes no bindable context. It names the passage rather than
	  its coordinates: a reader hovering a cloud wants to know what is under the
	  pointer, and both numbers are already on the axes.
	-->
	{#snippet tip({ context }: { context: any })}
		{@const d = capture(context?.tooltip?.data)}
		{#if d}
			<div class="tip">
				<i style:background={art.cats.find((c) => c.key === d.cat)?.colour}></i>
				<strong>{d.model}</strong>
				<span>{d.cat}</span>
				<em>click to read</em>
			</div>
		{/if}
	{/snippet}

	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div class="plot" onclick={openHovered}>
		<ScatterChart
			tooltip={tip}
			x="x"
			y="y"
			xDomain={art.x.domain}
			yDomain={art.y.domain}
			{series}
			padding={{ left: 52, bottom: 44, top: 12, right: 14 }}
			points={{ r: 1.4 }}
			brush
			props={{
				//: NO `label` ON EITHER AXIS. LayerChart's axis label lands in the
				//: same text layer as the ticks here: the y label rotated the y
				//: tick numbers with it and the x label printed over its own tick
				//: row. Both axes are titled in HTML beside the panel instead,
				//: where they also have room for the note that says what the
				//: quantity IS -- which the one-word label never had.
				//: FILL AND STROKE SET EXPLICITLY. In canvas mode LayerChart draws tick
				//: text with BOTH, and the defaults are sized for a light page: on this
				//: one every glyph came out light-outlined with a dark interior, which
				//: at 10px reads as a doubled or rotated character rather than as a
				//: styling default. `stroke: none` is the half that matters.
				xAxis: { grid: false, tickLabelProps: { fill: '#8b94a3', stroke: 'none' } },
				yAxis: { grid: false, tickLabelProps: { fill: '#8b94a3', stroke: 'none' } },
				grid: { x: false, y: false },
				rule: { x: 0, y: 0, class: 'qrule' }
			}}
		/>
		<!--
		  Only the two cells that CARRY A READING are named. The diagonal pair has
		  no label in the artifact because the finding is about the off-diagonal
		  ones, and inventing names for the other two would put two readings on the
		  panel that nothing in the repo supports.
		-->
		<span class="cell tl">{art.cells.find((c) => c.key === '(-surp +drift)')?.label}</span>
		<span class="cell br">{art.cells.find((c) => c.key === '(+surp -drift)')?.label}</span>
		<span class="ylab">{art.y.label} &rarr;</span>
		<span class="xlab">{art.x.label} &rarr;</span>
	</div>
	<p class="axnote">
		<b>x</b>
		{art.x.note} · <b>y</b>
		{art.y.note} · click a point to read its passage
	</p>

	{#if openId}
		<section class="reader">
			{#if detailErr}
				<p class="err">could not read <code>{openId}</code>: {detailErr}</p>
			{:else if !detail}
				<p class="muted">reading…</p>
			{:else}
				{@const p = detail.passage}
				<header>
					<span class="tag" style:background={art.cats.find((c) => c.key === p.category)?.colour}
					></span>
					<strong>{p.model}</strong>
					<span class="muted">{p.category}</span>
					<span class="q">{p.quadrant}</span>
					<span class="muted"
						>surprisal {fmt(p.surprisal)} (z {fmt(p.z_surprisal)}) · drift {fmt(p.drift, 3)} (z
						{fmt(p.z_drift)})</span
					>
					<!--
					  SERVED PER PASSAGE RATHER THAN ASSUMED. `reproduces` is whether
					  this passage's own sentence steps reproduce its own drift, and it
					  is true for 14,414 of 14,414 -- worth nothing until it isn't,
					  which is why it is shown on the passage and not in a README.
					-->
					<span class="rep" class:bad={detail.reproduces === false}>
						{detail.reproduces ? 'steps reproduce drift' : 'STEPS DO NOT REPRODUCE DRIFT'}
					</span>
					<button class="close" onclick={() => (openId = null)}>close</button>
				</header>
				<!--
				  Human-corpus passages have no prompt -- they were not generated --
				  so the row is absent rather than empty. A labelled blank reads as a
				  prompt that was lost.
				-->
				{#if p.prompt}<p class="prompt"><b>prompt</b> {p.prompt}</p>{/if}

				{#if reading}
					{#if reading.leftover !== 0}
						<p class="err">
							word/sentence join is off by {reading.leftover}: the passage below is incomplete
						</p>
					{/if}
					<div class="passage">
						{#each reading.lead as w (w.word_index)}<span
								class="w partial"
								title="leading fragment, belongs to no sentence">{w.word}</span
							>{/each}
						{#each reading.sents as s (s.sent_index)}
							<span class="sent" class:furthest={s.is_furthest}>
								<span
									class="stepbar"
									title="step from the previous sentence: {fmt(s.step, 3)}{s.is_furthest
										? ' · furthest from the opening'
										: ''}"
									style:--f={s.step == null
										? 0
										: Math.max(0, Math.min(1, (s.step - stepDom[0]) / (stepDom[1] - stepDom[0])))}
								></span>
								{#each s.words as w (w.word_index)}<span
										class="w"
										style:background={heat(w.bits)}
										title="{w.word} · {fmt(w.bits)} bits">{w.word}</span
									>{' '}{/each}
								{#if s.short}<span class="err">[sentence short of its declared n_words]</span>{/if}
							</span>
						{/each}
					</div>
					<p class="scalenote">
						<b>word tint</b>
						{art.detail?.scales?.bits?.note} · <b>bar</b>
						{art.detail?.scales?.step?.note}
					</p>
				{/if}
			{/if}
		</section>
	{/if}

	<div class="tablewrap">
		<p class="tcap">
			Occupancy and enrichment. <em
				>Enrichment is against the pooled rate over all {rows.length.toLocaleString()} passages, printed
				beside each quadrant.</em
			>
		</p>
		<div class="scroll">
			<table>
				<thead>
					<tr>
						<th>category</th>
						<th class="num">n</th>
						{#each art.cells as c (c.key)}
							<th class="num" class:named={c.label}>
								{c.key}{#if c.label}<em>{c.label}</em>{/if}
								<span class="pooled">{(100 * c.pooled).toFixed(1)}%</span>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each art.table as r (r.cat)}
						<tr class:dim={hideCat.includes(r.cat)}>
							<td>
								<i style:background={art.cats.find((c) => c.key === r.cat)?.colour}></i>{r.cat}
							</td>
							<td class="num">{r.n.toLocaleString()}</td>
							{#each art.cells as c (c.key)}
								<td class="num">
									{r.pct[c.key].toFixed(1)}%
									<em class:up={r.enrich[c.key] >= 1.25} class:down={r.enrich[c.key] <= 0.8}
										>{r.enrich[c.key].toFixed(2)}x</em
									>
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	{#each art.notes ?? [] as n}<p class="note">{n}</p>{/each}
</figure>

<style>
	.qm {
		margin: 0;
	}
	figcaption h3 {
		margin: 0 0 0.15rem;
		font-size: 1rem;
	}
	.sub {
		margin: 0 0 0.7rem;
		font-size: 0.85rem;
		color: var(--text-3);
		max-width: 120ch;
	}
	.controls,
	.legend {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.3rem 0.85rem;
		font-size: 0.8rem;
		color: var(--text-3);
		margin-bottom: 0.4rem;
	}
	.count strong {
		color: var(--text-1);
	}
	.controls select {
		font: inherit;
		background: none;
		color: var(--text-2);
		border: 1px solid var(--text-3);
		border-radius: 3px;
		max-width: 22ch;
	}
	.controls button,
	.close {
		font: inherit;
		color: inherit;
		background: none;
		border: 1px solid currentColor;
		border-radius: 3px;
		padding: 0 0.4rem;
		cursor: pointer;
	}
	.kind {
		font-style: italic;
		opacity: 0.7;
	}
	button.key {
		font: inherit;
		color: inherit;
		background: none;
		border: 0;
		padding: 0;
		cursor: pointer;
	}
	button.key.off {
		opacity: 0.3;
	}
	.key i,
	td i {
		display: inline-block;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		margin-right: 0.3rem;
		vertical-align: baseline;
	}
	.key em {
		font-style: normal;
		opacity: 0.65;
		margin-left: 0.2rem;
	}
	.plot {
		position: relative;
		height: 440px;
		cursor: pointer;
	}
	/* the quadrant crosshair is LayerChart's own `rule`, at x=0 and y=0 */
	.plot :global(.qrule) {
		stroke: var(--text-3);
		stroke-opacity: 0.55;
		stroke-dasharray: 3 3;
	}
	.tip {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		white-space: nowrap;
	}
	.tip i {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}
	.tip em {
		font-style: italic;
		opacity: 0.6;
	}
	.cell {
		position: absolute;
		font-size: 0.72rem;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--text-3);
		opacity: 0.75;
		pointer-events: none;
	}
	.tl {
		top: 14px;
		left: 54px;
	}
	.br {
		bottom: 52px;
		right: 20px;
	}
	/* axis titles in HTML: see the note on `props.xAxis` for why not LayerChart's */
	.ylab,
	.xlab {
		position: absolute;
		font-size: 0.75rem;
		color: var(--text-2);
		pointer-events: none;
	}
	.ylab {
		left: 2px;
		top: 50%;
		transform: translateY(-50%) rotate(-90deg);
		transform-origin: left center;
		white-space: nowrap;
	}
	.xlab {
		bottom: 2px;
		left: 50%;
		transform: translateX(-50%);
	}
	.axnote,
	.scalenote,
	.note {
		margin: 0.35rem 0 0;
		font-size: 0.75rem;
		color: var(--text-3);
		max-width: 120ch;
	}
	.note {
		margin-top: 0.55rem;
	}
	.reader {
		margin: 0.8rem 0;
		padding: 0.6rem 0.7rem;
		border: 1px solid color-mix(in srgb, var(--text-3) 30%, transparent);
		border-radius: 4px;
	}
	.reader header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		margin-bottom: 0.4rem;
	}
	.tag {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}
	.q {
		font-family: var(--mono);
		font-size: 0.72rem;
		color: var(--text-2);
	}
	.rep {
		font-size: 0.7rem;
		color: var(--text-3);
		font-style: italic;
	}
	.rep.bad {
		color: #fa5252;
		font-style: normal;
		font-weight: 600;
	}
	.close {
		margin-left: auto;
	}
	.prompt {
		margin: 0 0 0.5rem;
		font-size: 0.8rem;
		color: var(--text-3);
	}
	.passage {
		font-size: 0.86rem;
		line-height: 1.85;
		max-height: 26rem;
		overflow-y: auto;
	}
	.sent {
		position: relative;
	}
	/*
	  The step bar sits at the sentence's start, so the reader meets "how far this
	  sentence moved" before reading it. Height is the step on the artifact's
	  declared domain; nothing is clamped, because 0.794 is the observed maximum.
	*/
	.stepbar {
		display: inline-block;
		width: 3px;
		height: calc(0.35rem + 0.85rem * var(--f));
		margin-right: 0.28rem;
		vertical-align: baseline;
		background: var(--text-2);
		opacity: 0.55;
	}
	.sent.furthest .stepbar {
		background: #4dabf7;
		opacity: 0.95;
	}
	.w {
		border-radius: 2px;
		padding: 0 1px;
	}
	.w.partial {
		outline: 1px dotted var(--text-3);
		opacity: 0.6;
	}
	.err {
		color: #fa5252;
		font-size: 0.78rem;
	}
	.tablewrap {
		margin-top: 0.9rem;
	}
	.tcap {
		margin: 0 0 0.3rem;
		font-size: 0.75rem;
		color: var(--text-3);
	}
	.scroll {
		overflow-x: auto;
	}
	table {
		border-collapse: collapse;
		font-size: 0.76rem;
	}
	th,
	td {
		padding: 0.2rem 0.5rem;
		white-space: nowrap;
		border-bottom: 1px solid color-mix(in srgb, var(--text-3) 18%, transparent);
	}
	th {
		text-align: left;
		font-weight: 500;
		color: var(--text-3);
		font-family: var(--mono);
		font-size: 0.7rem;
	}
	th.named {
		color: var(--text-1);
	}
	th em,
	.pooled {
		display: block;
		font-family: inherit;
		font-style: normal;
		font-size: 0.68rem;
		opacity: 0.7;
	}
	th em {
		font-style: italic;
		opacity: 1;
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	td {
		color: var(--text-2);
	}
	tr.dim td {
		opacity: 0.35;
	}
	td em {
		font-style: normal;
		font-size: 0.68rem;
		opacity: 0.6;
		margin-left: 0.3rem;
	}
	td em.up {
		color: #ffa94d;
		opacity: 1;
	}
	td em.down {
		color: #74c0fc;
		opacity: 1;
	}
</style>
