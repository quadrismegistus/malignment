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
		cells: { key: string; label: string; pooled: number; surp: number; drift: number }[];
		table: { cat: string; n: number; pct: Record<string, number>; enrich: Record<string, number> }[];
		detail?: {
			url?: string;
			scales?: Record<
			string,
			{ domain: [number, number]; mid?: number; mean?: number; sd?: number; note: string }
		>;
		};
		notes?: string[];
		n_total?: number;
		arrows?: { label: string; n_kids: number; from: { x: number; y: number }; to: { x: number; y: number } }[];
		anchors?: { label: string; colour: string; x: number; y: number }[];
	};
	let { art }: { art: Art } = $props();

	const BASE = import.meta.env.DEV ? '/api' : '';

	//: ONE PADDING CONSTANT, read by the chart and by the hover marker below.
	//: The marker projects a data point to pixels itself, so if these were two
	//: literals the ring would sit off its own point the moment either moved --
	//: and it would still look like a ring on a point, just the wrong one.
	const PAD = { left: 52, bottom: 44, top: 12, right: 14 };

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

	//: ONE SERIES, COLOURED PER POINT. A series per category is the obvious shape
	//: and it silently re-blocks the draw order: the producer interleaves the
	//: categories precisely so no colour paints over another, and grouping them
	//: back into nine arrays throws that away and paints them in blocks again. So
	//: the categories become a colour SCALE over one array, and the array stays in
	//: the order the producer emitted.
	const cDomain = $derived(art.cats.map((c) => c.key));
	const cRange = $derived(art.cats.map((c) => c.colour));

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
	//: THE PANEL'S OWN WIDTH, bound rather than taken from the last pointer event.
	//: The ring used `ptr.w`, which only exists once the pointer has moved -- fine
	//: for a hover mark and useless for an overlay that must be right on first
	//: paint. Both project through `px`/`py` now, so they cannot disagree.
	let plotW = $state(0);
	const px = (v: number) =>
		PAD.left + ((v - art.x.domain[0]) / (art.x.domain[1] - art.x.domain[0])) * (plotW - PAD.left - PAD.right);
	const py = (v: number) =>
		PAD.top + (1 - (v - art.y.domain[0]) / (art.y.domain[1] - art.y.domain[0])) * (plotW - PAD.top - PAD.bottom);

	//: A ONE-DIMENSIONAL LABEL DECLUTTER: sort by y, then push each label down
	//: until it clears the one above by `LGAP`. Six anchors, so a greedy pass is
	//: exact enough and, unlike a force layout, gives the same answer every time.
	const LGAP = 13;
	const allAnchors = $derived.by(() => {
		const p = art.points;
		if (!p?.x?.length) return art.anchors ?? [];
		const out: { label: string; colour: string; x: number; y: number }[] = [];
		for (const c of art.cats ?? []) {
			const idx = art.cats.indexOf(c);
			const xs: number[] = [], ys: number[] = [];
			for (let j = 0; j < p.x.length; j++) {
				if (p.cat[j] === idx) { xs.push(p.x[j]); ys.push(p.y[j]); }
			}
			if (xs.length < 3) continue;
			out.push({ label: c.label, colour: c.colour,
				x: xs.reduce((a, b) => a + b, 0) / xs.length,
				y: ys.reduce((a, b) => a + b, 0) / ys.length });
		}
		return out;
	});
	const decluttered = $derived.by(() => {
		if (!plotW) return [];
		const all = allAnchors;
		const out = all
			.map((a) => ({ ...a, dx: px(a.x), dy: py(a.y), ly: py(a.y) }))
			.sort((m, n) => m.dy - n.dy);
		for (let i = 1; i < out.length; i++)
			if (out[i].ly - out[i - 1].ly < LGAP) out[i].ly = out[i - 1].ly + LGAP;
		return out;
	});

	//: OFF BY DEFAULT. The arrows are a different CLAIM from the cloud -- paired,
	//: causal, 22 lineages -- and stacking them on by default would let a reader
	//: take the descriptive panel for the tested one.
	let showMoves = $state(false);

	let ptr = $state<{ x: number; y: number; w: number } | null>(null);
	let hovered: any = $state(null);

	/** Record what the pointer is over, and hand it back so the tooltip can draw it.
	 *
	 * DEFERRED BY A MICROTASK, and it has to be. `hovered` is read during render
	 * (it draws the tip) so it must be `$state`; it is WRITTEN from inside a
	 * `{@const}` in the tooltip snippet, which is also render. Svelte 5 refuses
	 * that outright -- `state_unsafe_mutation` -- and the whole figure failed to
	 * mount rather than degrading, which is the good kind of failure.
	 *
	 * A microtask lands after the current render and before paint, so the tip is
	 * never a frame behind the point it names. The alternative, capturing in the
	 * pointermove handler instead, cannot guarantee that: it would race
	 * LayerChart's own hit test and could label a point the pointer had left. */
	function capture(d: any) {
		const next = d ?? null;
		//: COMPARED BY id, NOT BY IDENTITY. An identity guard looks equivalent and
		//: is not: if the chart hands back a fresh object for the same datum, every
		//: assignment re-renders, every render re-captures, and the microtask queue
		//: never drains -- the page mounts and then freezes on first hover, which
		//: is a worse failure than the mount error it replaced because it looks
		//: like a slow chart.
		if (next?.id !== hovered?.id) queueMicrotask(() => (hovered = next));
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

	//: A RAW COSINE STEP IS UNINTERPRETABLE (RH). 0.472 says nothing on its own;
	//: +0.3σ says it is a slightly-longer-than-usual move. Parameters come from
	//: the producer, which asserts them against the store, because a z printed
	//: against a stale mean is wrong in a way nothing on the panel can reveal.
	//:
	//: **WRITTEN AS σ, NOT AS "z", ON PURPOSE.** The header already shows the
	//: PASSAGE's `z_drift`, and the two are not the same scale: a passage's drift
	//: is the mean of its steps, and averaging shrinks the spread, so the sentence
	//: sd is 0.0921 against the passage sd of 0.0434. Two numbers spelled the same
	//: way on one screen, differing by a factor of two, is a mismatch a reader has
	//: no way to suspect. The raw value stays on hover.
	const stepZ = $derived.by(() => {
		const sc = art.detail?.scales?.step;
		if (!sc?.sd) return null;
		return (v: number) => (v - (sc.mean ?? 0)) / sc.sd!;
	});
	//: DIVERGING ABOUT A MIDPOINT THE PRODUCER DECLARES, blue below and red above.
	//: The two sides are normalised SEPARATELY, because the domain is not
	//: symmetric about the median -- 0 to 3.44 against 3.44 to 16 -- and one ramp
	//: would hand the cheap half of the distribution a fifth of the colour range.
	//:
	//: Saturation carries the magnitude and hue carries the side, so a word AT the
	//: midpoint is nearly untinted and reads as ordinary prose, which is what it
	//: is. An absent `mid` falls back to the one-sided ramp rather than guessing a
	//: centre: where a scale diverges is a claim about what counts as ordinary.
	const bitsMid = $derived(art.detail?.scales?.bits?.mid ?? null);
	const heat = (b: number) => {
		const [lo, hi] = bitsDom;
		const v = Math.max(lo, Math.min(hi, b));
		if (bitsMid == null)
			return `rgba(232, 89, 12, ${(0.06 + 0.62 * ((v - lo) / (hi - lo))).toFixed(3)})`;
		if (v <= bitsMid)
			return `rgba(77, 171, 247, ${(0.04 + 0.5 * ((bitsMid - v) / (bitsMid - lo))).toFixed(3)})`;
		return `rgba(250, 82, 82, ${(0.04 + 0.62 * ((v - bitsMid) / (hi - bitsMid))).toFixed(3)})`;
	};

	const fmt = (v: number, d = 2) => (v == null ? '—' : v.toFixed(d));

	//: THE GAP IS THE STEP, ON THE ARTIFACT'S DOMAIN AND THIS COMPONENT'S PIXELS.
	//: Which quantity it is and what its range means are the producer's (`step`
	//: runs 0.000 to 0.794 over 181,935 sentences, nothing clamped); how many
	//: pixels that becomes is a drawing decision and stays here.
	//:
	//: The floor is 12px rather than 0 so that consecutive sentences at step 0 --
	//: a model repeating itself, which is exactly the tail RH had me window off
	//: the plane -- still read as two sentences rather than as one run-on. So the
	//: gap is proportional ABOVE a floor, and the number is printed beside it
	//: because that is the part a reader can check.
	//: `(-0.04).toFixed(1)` is "-0.0", which prints a signed zero -- a value that
	//: reads as "slightly below" when what it means is "at the mean". Rounded
	//: first, so the sign is decided on the number actually shown.
	const sig = (z: number) => {
		const r = Math.round(z * 10) / 10;
		return `${r > 0 ? '+' : r < 0 ? '\u2212' : ''}${Math.abs(r).toFixed(1)}\u03c3`;
	};

	const GAP_MIN = 12;
	const GAP_MAX = 78;
	const gapPx = (step: number | null) => {
		if (step == null) return GAP_MIN;
		const t = Math.max(0, Math.min(1, (step - stepDom[0]) / (stepDom[1] - stepDom[0])));
		return Math.round(GAP_MIN + t * (GAP_MAX - GAP_MIN));
	};
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
		<!--
		  THREE NUMBERS, BECAUSE THERE ARE THREE POPULATIONS: what the filters
		  leave, what the producer drew, and what the table counts. Printing only
		  the first two would let a reader take the count of ink for the count of
		  passages, which is exactly the mismatch nothing in the figure would flag.
		-->
		<span class="count">
			<strong>{visible.length.toLocaleString()}</strong>
			{#if visible.length !== rows.length}of {rows.length.toLocaleString()} drawn{/if}
			{#if (art.n_total ?? 0) > rows.length}
				<span class="muted"
					>· {rows.length.toLocaleString()} drawn of {(art.n_total ?? 0).toLocaleString()} passages</span
				>
			{:else}
				passages
			{/if}
		</span>
		<label>
			model
			<select bind:value={model}>
				<option value="">all {art.models.length}</option>
				{#each art.models as m (m)}<option value={m}>{m}</option>{/each}
			</select>
		</label>
		{#if (art.arrows ?? []).length}
			<label class="tog">
				<input type="checkbox" bind:checked={showMoves} />
				base → aligned
				<span class="hint"
					>{(art.arrows ?? []).length} lineages, each base median to the mean of its aligned
					children; the cloud dims because it is a different claim</span
				>
			</label>
		{/if}
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
	<!--
	  THE SNIPPET ONLY CAPTURES; THE TIP IS DRAWN BELOW. LayerChart puts
	  `.lc-tooltip-root` at `position: fixed` on `body` and hands it CHART-relative
	  coordinates, so anything rendered through it landed exactly the figure's own
	  left offset away from the pointer -- 276px on this page, naming a point
	  nowhere near the cursor, which is worse than no tooltip because it reads as
	  a label for whatever it happens to cover. Verified by walking the parent
	  chain rather than guessed: div.tip < lc-tooltip-content < lc-tooltip-container
	  < lc-tooltip-root [fixed] < BODY.
	-->
	{#snippet tip({ context }: { context: any })}
		{@const d = capture(context?.tooltip?.data)}
		{#if d}{/if}
	{/snippet}

	<div class="stage">
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div
		class="plot"
		class:moving={showMoves}
		bind:clientWidth={plotW}
		onclick={openHovered}
		onpointermove={(e) => {
			const b = e.currentTarget.getBoundingClientRect();
			//: WIDTH CARRIED WITH THE POINT. The flip-near-the-edge test was
			//: `ptr.x > 0.66 * 660`, and 660 was the width the panel happened to
			//: have while I was looking at it -- the plot is square and responsive,
			//: so that constant is wrong at every other viewport, in the direction
			//: that pushes the tooltip off the panel.
			ptr = { x: e.clientX - b.left, y: e.clientY - b.top, w: b.width };
		}}
		onpointerleave={() => (ptr = null)}
	>
		<ScatterChart
			tooltip={tip}
			x="x"
			y="y"
			xDomain={art.x.domain}
			yDomain={art.y.domain}
			//: NEAREST POINT IN TWO DIMENSIONS. The default mode bisects on x alone,
			//: so hovering lit up every point sharing the pointer's x -- a vertical
			//: line of highlights under a tooltip naming ONE of them, with no way to
			//: tell which would open on click. On a scatter that is not a cosmetic
			//: default: the click opens whatever the tooltip resolved to, which could
			//: be a passage the pointer was nowhere near in y.
			tooltipContext={{ mode: 'quadtree' }}
			highlight={false}
			data={visible}
			c="cat"
			{cDomain}
			{cRange}
			padding={PAD}
			//: `stroke: 'none'` FOR THE SAME REASON THE TICK TEXT NEEDED IT. Canvas
			//: Points draw a stroke as well as a fill, and against this background the
			//: default put a light ring on every dot -- at r=1.4 the ring was most of
			//: the mark, so 14,414 points read as 14,414 little doughnuts. Smaller and
			//: translucent now, so the dense middle shows as density, not as a mass.
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
				//: NESTED, NOT THE TOP-LEVEL `points` PROP. That one is the series
				//: path's: switching to `data` plus a colour scale silently dropped it
				//: and every dot came back full size and opaque, with nothing in the
				//: code or console to say the prop was no longer being read.
				points: { r: 1.2, stroke: 'none', opacity: 0.45 },
				//: OFF. It lit four points in a near-vertical line under a tooltip
				//: naming one of them, and constraining it to `points` with `axis:
				//: 'none'` did not reduce that. The CLICK was never wrong -- five hovers
				//: at one x and five different y resolve five distinct passages, so
				//: quadtree mode is doing its job -- but an affordance pointing at four
				//: things when one is selectable is its own defect. Replaced by a single
				//: ring drawn below, on the point the click will actually open.
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
		<!--
		  PLACED FROM EACH CELL'S OWN SIGNS. The axes were swapped once already --
		  surprisal used to be x -- and a corner written as "top left" survives
		  that swap silently, putting one reading where the other belongs while
		  every number on the panel stays right. The producer declares `surp` and
		  `drift` per cell; which axis carries which decides the corner here.
		-->
		{#each art.cells.filter((c) => c.label) as c (c.key)}
			{@const sx = art.x.key.includes('drift') ? c.drift : c.surp}
			{@const sy = art.y.key.includes('drift') ? c.drift : c.surp}
			<span
				class="cell"
				style:left={sx < 0 ? '54px' : 'auto'}
				style:right={sx > 0 ? '20px' : 'auto'}
				style:top={sy > 0 ? '14px' : 'auto'}
				style:bottom={sy < 0 ? '52px' : 'auto'}>{c.label}</span
			>
		{/each}
		{#if showMoves && plotW > 0}
			<!--
			  ONE VECTOR PER LINEAGE, base median to the mean of its aligned
			  children's medians. Drawn over the cloud rather than beside it,
			  because the question the arrows answer is WHERE the move lands
			  relative to the human corpora -- which only the shared plane shows.
			-->
			<svg class="moves" width={plotW} height={plotW}>
				<defs>
					<marker id="qm-head" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="5"
						markerHeight="5" orient="auto-start-reverse">
						<path d="M0,0 L8,4 L0,8 z" fill="#ffd43b" opacity="0.4" />
					</marker>
				</defs>
				{#each art.arrows ?? [] as a (a.label)}
					<line
						x1={px(a.from.x)}
						y1={py(a.from.y)}
						x2={px(a.to.x)}
						y2={py(a.to.y)}
						marker-end="url(#qm-head)"
					><title>{a.label} → {a.n_kids} aligned child{a.n_kids > 1 ? 'ren' : ''}</title></line>
				{/each}

				<!--
				  THE DOT STAYS PUT AND ONLY THE LABEL MOVES, with a leader drawn to
				  it. `arxiv_abstracts` and `philosophy` have genuinely close medians
				  and their labels overlapped into an unreadable smear -- but nudging
				  the MARK to fix that would move a measured position to make room
				  for text, which is the one thing a declutter must never do.
				-->
				{#each decluttered as a (a.label)}
					<g class="anchor">
						{#if a.ly !== a.dy}<line class="leader" x1={a.dx + 5} y1={a.dy} x2={a.dx + 9} y2={a.ly} />{/if}
						<circle cx={a.dx} cy={a.dy} r="4" fill={a.colour} />
						<text x={a.dx + 11} y={a.ly + 3}>{a.label}</text>
					</g>
				{/each}
			</svg>
		{/if}

		{#if hovered && ptr}
			<span class="ring" style:left="{px(hovered.x)}px" style:top="{py(hovered.y)}px"></span>
		{/if}
		{#if hovered && ptr}
			<!--
			  CLAMPED, NOT FLIPPED. Flipping past a fraction of the width works only
			  while the panel is wider than two tooltips: at a 1050px viewport the
			  square plot is 402px and a 240px tip overflowed by 64px on EITHER
			  side, so there is no side to flip to. Clamping into the panel is
			  correct at every width, and `--tw` is the same number the CSS caps
			  the tip at, so the two cannot drift apart.
			-->
			<div
				class="tip"
				style:left="clamp(4px, {ptr.x + 14}px, {ptr.w}px - var(--tw) - 4px)"
				style:top="clamp(4px, {ptr.y + 14}px, 100% - 2.2rem)"
			>
				<i style:background={art.cats.find((c) => c.key === hovered.cat)?.colour}></i>
				<strong>{hovered.model}</strong>
				<span>{hovered.cat}</span>
				<em>click to read</em>
			</div>
		{/if}
		<span class="ylab">{art.y.label} &rarr;</span>
		<span class="xlab">{art.x.label} &rarr;</span>
	</div>
	<aside class="side">
	{#if !openId}
		<p class="muted hint">Click a point to read its passage: every word tinted by the bits
			spent on it, every sentence opening with a bar for its step from the one before.</p>
	{:else}
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
					<!--
					  ONE SENTENCE PER LINE, SEPARATED BY ITS OWN STEP. The gap between
					  two sentences IS the distance between them in bge space, on the
					  domain the artifact declares, so the passage reads as the drift
					  statistic rather than merely carrying it in a caption. A tight
					  passage is visibly tight.

					  The measure is a DISTANCE FROM THE PREVIOUS sentence, so it belongs
					  between them and the first has none -- `step` is null for sentence
					  0 in all 14,414 passages, which is why the gap is rendered by the
					  sentence AFTER it and never by the sentence itself.
					-->
					<div class="passage">
						{#each reading.lead as w (w.word_index)}<span
								class="w partial"
								title="leading fragment, belongs to no sentence">{w.word}</span
							>{/each}
						{#each reading.sents as s, i (s.sent_index)}
							{#if i > 0}
								<div
									class="gap"
									style:height="{gapPx(s.step)}px"
									title="step from the previous sentence: {fmt(s.step, 3)} raw{s.step != null &&
									stepZ
										? ` · ${stepZ(s.step) >= 0 ? '+' : ''}${stepZ(s.step).toFixed(2)} sd from the mean sentence step`
										: ''}"
								>
									<span class="rule"></span>
									<span class="num">
										{#if s.step == null}—{:else if stepZ}{sig(stepZ(s.step))}{:else}{s.step.toFixed(
												3
											)}{/if}
									</span>
								</div>
							{/if}
							<p class="sent" class:furthest={s.is_furthest}>
								{#each s.words as w (w.word_index)}<span
										class="w"
										style:background={heat(w.bits)}
										title="{w.word} · {fmt(w.bits)} bits">{w.word}</span
									>{' '}{/each}
								{#if s.is_furthest}<span class="far" title="furthest from the opening sentence"
										>furthest</span
									>{/if}
								{#if s.short}<span class="err">[sentence short of its declared n_words]</span>{/if}
							</p>
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
	</aside>
	</div>

	<p class="axnote">
		<b>x</b>
		{art.x.note} · <b>y</b>
		{art.y.note}
	</p>

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
		color: var(--text);
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
	/*
	  SQUARE PLOT, READER BESIDE IT. Both axes are z-scores, so a square panel is
	  the only aspect ratio on which a unit of surprisal and a unit of drift are
	  the same distance. On the wide panel this replaces, the cloud read as much
	  flatter than it is -- which is a claim about the very correlation the figure
	  exists to argue over.
	*/
	/*
	  THE SQUARE IS SIZED BY THE WINDOW AND THE SIDEBAR TAKES THE REST. `auto 1fr`
	  rather than a fixed sidebar width: the plot column is sized by its own
	  content, which `aspect-ratio: 1` ties to the height, so on a tall window the
	  panel grows and the reader keeps whatever is left instead of being pinned at
	  320px while the plot stays small.

	  `min(78vh, 58vw)` is the height, and the `58vw` half is what stops a short
	  wide window from producing a square wider than the space beside it.
	*/
	.stage {
		display: grid;
		grid-template-columns: auto minmax(280px, 1fr);
		gap: 1rem;
		align-items: stretch;
	}
	.plot {
		position: relative;
		height: min(78vh, 58vw);
		aspect-ratio: 1;
		cursor: pointer;
	}
	.side {
		max-height: min(78vh, 58vw);
		overflow-y: auto;
		font-size: 0.8rem;
		min-width: 0;
	}
	.hint {
		margin: 0;
		font-size: 0.78rem;
		color: var(--text-3);
		font-style: italic;
	}
	@media (max-width: 900px) {
		.stage {
			grid-template-columns: 1fr;
		}
		.side {
			max-height: none;
		}
	}
	/* the quadrant crosshair is LayerChart's own `rule`, at x=0 and y=0 */
	.plot :global(.qrule) {
		stroke: var(--text-3);
		stroke-opacity: 0.55;
		stroke-dasharray: 3 3;
	}
	.moves {
		position: absolute;
		inset: 0;
		pointer-events: none;
		z-index: 1;
	}
	.moves line {
		stroke: #ffd43b;
		stroke-width: 1.6;
		stroke-opacity: 0.4;
		pointer-events: stroke;
	}
	.moves .anchor text {
		font-size: 9.5px;
		fill: var(--text-2);
		paint-order: stroke;
		stroke: var(--ground);
		stroke-width: 3px;
	}
	.moves .leader {
		stroke: var(--text-3);
		stroke-width: 1;
		stroke-opacity: 0.5;
	}
	.moves .anchor circle {
		stroke: var(--ground);
		stroke-width: 1.5;
	}
	/* the cloud steps back while the vectors are up: two claims, one plane */
	.plot.moving :global(canvas) {
		opacity: 0.3;
	}
	.tog {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		cursor: pointer;
	}
	.tog input {
		margin: 0;
	}
	/* the hover marker: one ring, on the point the click opens */
	.ring {
		position: absolute;
		width: 11px;
		height: 11px;
		margin: -5.5px 0 0 -5.5px;
		border: 1.5px solid var(--text);
		border-radius: 50%;
		pointer-events: none;
		z-index: 1;
	}
	.tip {
		--tw: 240px;
		max-width: var(--tw);
		position: absolute;
		z-index: 2;
		pointer-events: none;
		background: color-mix(in srgb, var(--ground) 92%, transparent);
		border: 1px solid color-mix(in srgb, var(--text-3) 35%, transparent);
		border-radius: 3px;
		padding: 0.15rem 0.4rem;
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
	.tip strong,
	.tip span {
		overflow: hidden;
		text-overflow: ellipsis;
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
	/* axis titles in HTML: see the note on `props.xAxis` for why not LayerChart's */
	.ylab,
	.xlab {
		position: absolute;
		font-size: 0.75rem;
		color: var(--text-2);
		pointer-events: none;
	}
	/*
	  `writing-mode` rather than a rotate: rotating about the left edge put the
	  glyphs in a strip the figure then clipped, and the fix for that is guessing
	  an offset that depends on the string's length. Vertical text occupies the
	  box it is given.
	*/
	.ylab {
		left: 0;
		top: 50%;
		transform: translateY(-50%) rotate(180deg);
		writing-mode: vertical-rl;
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
		margin: 0;
		padding: 0.5rem 0.6rem;
		border: 1px solid color-mix(in srgb, var(--text-3) 30%, transparent);
		border-radius: 4px;
	}
	.reader header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.35rem 0.5rem;
		font-size: 0.75rem;
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
		font-size: 0.82rem;
		line-height: 1.9;
	}
	.sent {
		margin: 0;
	}
	.gap {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding-left: 3px;
	}
	/*
	  `align-self: stretch`, not `height: 100%`. The gap is a flex row with
	  `align-items: center` so the number sits mid-gap, and centring makes every
	  item size to its CONTENT -- a 1px empty span then has no height at all and
	  the rule was invisible. Measured, not eyeballed: it rendered 0px tall.

	  It then measured 1x51 and STILL did not read on the panel -- a 1px line at
	  55% opacity against this background is under the threshold at 1x. Measuring
	  that the element exists is not the same as measuring that it is visible, and
	  only the second one is what the reader gets.
	*/
	.rule {
		width: 2px;
		align-self: stretch;
		background: var(--text-3);
		opacity: 0.8;
		flex: none;
		border-radius: 1px;
	}
	.num {
		font-size: 0.62rem;
		font-variant-numeric: tabular-nums;
		color: var(--text-3);
		opacity: 0.8;
	}
	.far {
		font-size: 0.62rem;
		font-style: italic;
		color: #4dabf7;
		margin-left: 0.35rem;
		white-space: nowrap;
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
		color: var(--text);
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
