<!--
  Parallel coordinates with per-axis brushing, drawn from a producer's data file.

  Same contract as SlopeGrid: this component owns NO arithmetic and knows nothing
  about any particular figure. Axis order, domains, colours, the notes under each
  axis and every number it prints arrive in the `parcoords` artifact.

  ## WHY THIS ONE IS RAW SVG AND SlopeGrid IS NOT

  LayerChart has no parallel-coordinates primitive, and the thing it would give
  us -- a responsive scale context -- is nine scales here rather than one, so
  `Chart`'s single x/y pair does not fit. What we actually came to LayerChart for
  is RE-LAYOUT on resize, and that comes from `bind:clientWidth` plus d3 scales,
  not from the library. Wrapping this in `Chart` would buy generics to fight and
  no reflow we do not already have.

  ## WHY BRUSHING RATHER THAN A PRETTIER STATIC PICTURE

  The data is ordinal and heavily tied -- the producer's axis notes say so, e.g.
  "78% at 1". At 1,730 lines that means most of the ink is a rope along the floor
  of six axes, and no opacity setting distinguishes 1,348 overlapping lines from
  200. That is fatal for READING the picture and harmless for QUERYING it, so the
  count is reported as a number in the readout and never left to the ink.

  ## THE PATH GEOMETRY IS COMPUTED ONCE

  Brushing changes which lines are lit, never where they are. `d` strings are
  derived from the artifact alone so a drag re-styles 1,730 nodes instead of
  re-projecting them.
-->
<script lang="ts">
	import { scaleLinear } from 'd3-scale';

	type Axis = {
		key: string;
		label: string;
		domain: [number, number];
		note?: string;
		//: The data's granularity on this axis, for snapping the brush. Absent
		//: means continuous.
		step?: number;
	};
	type Group = { key: string; label: string; colour: string };
	type Line = {
		key: string;
		label: string;
		group: string;
		values: (number | null)[];
		marks?: string[];
		missing?: Record<string, string>;
		meta?: Record<string, any>;
	};
	type Art = {
		title: string;
		subtitle?: string;
		value_label?: string;
		mark_label?: string;
		mark_legend?: Record<string, string>;
		meta_order?: string[];
		//: Which meta keys become table columns. The producer names them because
		//: it is the only side that knows which are short enough to be one.
		table_meta?: string[];
		axes: Axis[];
		groups: Group[];
		lines: Line[];
	};

	let { art }: { art: Art } = $props();

	const H = 300;
	let w = $state(0);

	//: THE OUTER AXIS LABELS ANCHOR INWARD RATHER THAN CENTRE. Centre-anchored,
	//: the first and last stick out by half their width and the svg clips them:
	//: `euphemism` shipped reading "euphemi" and its note "82% a". The loss
	//: exists ONLY in the rendered image -- no error, no warning, and a truncated
	//: label reads as a complete one, which is the same failure plotnine has.
	//:
	//: The first fix estimated the overhang at 2.85px per character and padded
	//: for it. It was still cut. A PAD SIZED BY AN ESTIMATE IS A MEASUREMENT
	//: NEVER TAKEN, and it fails silently in the direction that loses text, so
	//: this anchors instead: `start` on the first axis and `end` on the last
	//: cannot overflow whatever the font does.
	const PAD = { top: 14, bottom: 42, left: 34, right: 12 };
	const anchor = (i: number) =>
		i === 0 ? 'start' : i === art.axes.length - 1 ? 'end' : 'middle';
	const innerW = $derived(Math.max(120, w - PAD.left - PAD.right));
	const innerH = H - PAD.top - PAD.bottom;

	const colour = $derived(new Map(art.groups.map((g) => [g.key, g.colour])));

	//: One scale per axis. Domains differ -- `body_distance` starts at 0, which is
	//: its "not on the body" code and not a lower rating -- so a single shared
	//: scale would put that 0 half a rating below where the axis says it is.
	const yOf = $derived(art.axes.map((a) => scaleLinear().domain(a.domain).range([innerH, 0])));
	const xOf = $derived(
		art.axes.length === 1
			? () => innerW / 2
			: (i: number) => (i * innerW) / (art.axes.length - 1)
	);

	//: ── JITTER ──────────────────────────────────────────────────────────────
	//:
	//: On a discrete axis every line lands on one of a handful of lattice points,
	//: so 1,348 coincident lines and 200 draw the same ink. Offsetting each
	//: vertex within its own cell restores density as something the eye can read.
	//:
	//: **IT IS DETERMINISTIC, AND NOT BY SEEDING AN RNG.** The offset is a hash
	//: of (line key, axis index), so it is a pure function of the artifact: a
	//: re-render is byte-identical, and -- the reason that matters more here -- a
	//: word does not JUMP to a new position when the brush changes. A seeded
	//: generator gives the first property and loses the second the moment the
	//: draw order changes, which it does whenever the brush does.
	//:
	//: **IT IS A DRAWING DECISION AND STAYS OUT OF THE ARTIFACT.** The data file
	//: holds ratings. Brushing, counting and the readout all use the TRUE values,
	//: so the offset never reaches a number the reader is given.
	//:
	//: Only axes that DECLARE a `step` are jittered, because only those are known
	//: discrete. Amplitude is a fraction of one step and stays well under a half,
	//: so the lattice remains visible and 4 does not blur into 5.
	const JIT = 0.19;
	const jitterable = $derived(art.axes.some((a) => a.step));
	let jitter = $state(true);

	//: FNV-1a, 32-bit. Any stable string hash does; this one is short and has no
	//: dependency. Returned in [-0.5, 0.5).
	function off(key: string, i: number) {
		let h = 0x811c9dc5;
		const t = key + '\u0000' + i;
		for (let k = 0; k < t.length; k++) {
			h ^= t.charCodeAt(k);
			h = Math.imul(h, 0x01000193);
		}
		return ((h >>> 0) % 4096) / 4096 - 0.5;
	}

	/** Offset in data units: two-sided in the interior, one-sided at either end. */
	function spread(o: number, v: number, a: Axis, st: number) {
		const span = st * JIT * 2;
		if (v <= a.domain[0]) return (o + 0.5) * span;
		if (v >= a.domain[1]) return -(o + 0.5) * span;
		return o * span;
	}

	//: GEOMETRY ONLY, and deliberately not a function of the brush. A `null` ends
	//: the current subpath and starts a new one after the gap, so a declared
	//: missing value draws as a break rather than as a straight line across the
	//: axis it has no value on -- which would be a fabricated reading.
	const paths = $derived(
		art.lines.map((l) => {
			let d = '';
			let pen = false;
			l.values.forEach((v, i) => {
				if (v === null) {
					pen = false;
					return;
				}
				const a = art.axes[i];
				const st = a.step ?? 0;
				//: ONE-SIDED AT THE ENDS OF THE SCALE, and this is not a detail
				//: here: 78-85% of cells sit AT the domain minimum on six of the
				//: nine axes, so the edge is the dominant case. Clamping a
				//: two-sided offset piles every below-floor excursion onto the
				//: floor line itself -- a hard bright edge carrying half the
				//: population, which is the overplotting the jitter exists to
				//: undo. Spread over the same total width, inward only, so band
				//: thickness stays comparable with an interior axis.
				const y = jitter && st ? v + spread(off(l.key, i), v, a, st) : v;
				d += `${pen ? 'L' : 'M'}${xOf(i).toFixed(1)},${yOf[i](y).toFixed(1)}`;
				pen = true;
			});
			return d;
		})
	);

	//: axis key -> [lo, hi] in DATA units. An axis with no entry does not filter.
	let brush = $state<Record<string, [number, number]>>({});
	const active = $derived(art.axes.map((a) => brush[a.key]));
	const anyBrush = $derived(Object.keys(brush).length > 0);

	const hit = $derived(
		art.lines.map((l) =>
			art.axes.every((a, i) => {
				const b = brush[a.key];
				if (!b) return true;
				const v = l.values[i];
				//: A LINE WITH NO VALUE ON A BRUSHED AXIS IS EXCLUDED, not passed
				//: through. It is not known to be in the range, and the readout
				//: reports cells rather than ink, so silently keeping it would
				//: inflate a number the reader is meant to trust.
				return v !== null && v >= b[0] && v <= b[1];
			})
		)
	);

	//: DRAW ORDER INTERLEAVES THE GROUPS. The producer emits cells sorted by
	//: (prompt, word), and every prompt belongs wholly to one group -- so the
	//: groups arrive in blocks and whichever paints last sits on top of the
	//: other everywhere they coincide. On heavily tied axes that is most of the
	//: panel, and it renders as "there is more male here" when the counts in the
	//: legend say 894 female to 836 male. Round-robin rather than a shuffle,
	//: because the order has to be the same on every render.
	const order = $derived.by(() => {
		const q = new Map<string, number[]>(art.groups.map((g) => [g.key, []]));
		art.lines.forEach((l, i) => q.get(l.group)?.push(i));
		const rest: number[] = [];
		art.lines.forEach((l, i) => {
			if (!q.has(l.group)) rest.push(i);
		});
		const out: number[] = [];
		const qs = [...q.values()];
		for (let k = 0; out.length < art.lines.length - rest.length; k++)
			for (const arr of qs) if (k < arr.length) out.push(arr[k]);
		return out.concat(rest);
	});

	const indexOf = $derived(new Map(art.lines.map((l, i) => [l.key, i])));

	const nSel = $derived(hit.filter(Boolean).length);
	const byGroup = $derived.by(() => {
		const m = new Map<string, number>(art.groups.map((g) => [g.key, 0]));
		art.lines.forEach((l, i) => {
			if (hit[i]) m.set(l.group, (m.get(l.group) ?? 0) + 1);
		});
		return m;
	});

	//: Only when the selection is small enough that individual lines are
	//: separable. Above that a hover picks whichever of dozens of coincident
	//: paths is on top, which is a lie about what the reader is pointing at.
	const HOVERABLE = 60;
	let hover = $state<number | null>(null);
	const hoverable = $derived(anyBrush && nSel <= HOVERABLE);

	//: Drag state for the axis brushes, in pixels; converted to data units on the
	//: axis's own scale so the stored range means the same thing the tooltip does.
	let drag = $state<{ axis: number; y0: number; y1: number } | null>(null);

	function commit(d: { axis: number; y0: number; y1: number }) {
		const a = art.axes[d.axis];
		const s = yOf[d.axis];
		const [lo, hi] = [Math.min(d.y0, d.y1), Math.max(d.y0, d.y1)];
		//: A CLICK IS NOT AN EMPTY BRUSH. Under a few pixels of travel this is a
		//: click, and the useful reading of a click on a brushed axis is "clear
		//: it" -- an empty range would instead select nothing and look broken.
		if (hi - lo < 4) {
			const { [a.key]: _, ...rest } = brush;
			brush = rest;
			return;
		}
		//: SNAPPED TO THE AXIS'S OWN GRANULARITY, which the PRODUCER declares. A
		//: pixel-exact brush on an integer scale reads "4-6.7" and invites a
		//: reader to believe a rating of 6.7 exists. The component cannot infer
		//: the step -- integer-looking data may be a rounded continuous quantity
		//: -- so an axis without a `step` is left continuous rather than guessed.
		const st = a.step ?? 0;
		const snap = (v: number, dir: -1 | 1) =>
			st ? (dir < 0 ? Math.floor(v / st) : Math.ceil(v / st)) * st : v;
		const v0 = Math.max(a.domain[0], snap(s.invert(hi), -1));
		const v1 = Math.min(a.domain[1], snap(s.invert(lo), 1));
		brush = { ...brush, [a.key]: [v0, v1] };
	}

	function down(e: PointerEvent, i: number) {
		const box = (e.currentTarget as Element).getBoundingClientRect();
		const y = e.clientY - box.top;
		drag = { axis: i, y0: y, y1: y };
		(e.currentTarget as Element).setPointerCapture(e.pointerId);
	}
	function move(e: PointerEvent) {
		if (!drag) return;
		const box = (e.currentTarget as Element).getBoundingClientRect();
		drag = { ...drag, y1: Math.max(0, Math.min(innerH, e.clientY - box.top)) };
	}
	function up() {
		if (drag) commit(drag);
		drag = null;
	}

	const fmt = (v: number) => (Number.isInteger(v) ? String(v) : v.toFixed(1));

	//: ── THE TABLE ───────────────────────────────────────────────────────────
	//:
	//: Columns are DERIVED FROM THE ARTIFACT: one per axis, plus whichever meta
	//: fields the producer names in `table_meta`. Nothing about any particular
	//: figure is hardcoded, so a second `parcoords` artifact gets its own columns
	//: without touching this file. The producer chooses because it is the only
	//: one that knows which of its meta fields are short enough to be a column --
	//: `reading` is a sentence and belongs in a title attribute, not a cell.
	type Col = { key: string; label: string; num: boolean; axis: number };
	const cols = $derived<Col[]>([
		...(art.table_meta ?? []).map((k) => ({ key: k, label: k, num: false, axis: -1 })),
		...art.axes.map((a, i) => ({ key: a.key, label: a.label, num: true, axis: i }))
	]);

	let sortKey = $state<string>('');
	let sortDesc = $state(false);
	function sortBy(k: string) {
		if (sortKey === k) sortDesc = !sortDesc;
		else {
			sortKey = k;
			//: Numeric columns open DESCENDING. The question a reader brings to a
			//: rating column is "which are the high ones", and opening ascending
			//: puts 1,300 cells scoring 1 in front of them.
			sortDesc = cols.find((c) => c.key === k)?.num ?? false;
		}
	}

	const cellOf = (l: Line, c: Col) => (c.axis >= 0 ? l.values[c.axis] : (l.meta?.[c.key] ?? ''));

	//: SORTED BEFORE IT IS CAPPED, so the cap keeps the top of the CURRENT sort
	//: rather than the top of the producer's order. That makes the cap legible --
	//: "the 300 highest on genitality" is a reading; "300 arbitrary rows of a
	//: sorted view" is not -- and the row count printed above says which.
	const CAP = 300;
	const selected = $derived.by(() => {
		const rows = art.lines.filter((_, i) => hit[i]);
		if (!sortKey) return rows;
		const c = cols.find((x) => x.key === sortKey);
		if (!c) return rows;
		const dir = sortDesc ? -1 : 1;
		return [...rows].sort((a, b) => {
			const x = cellOf(a, c);
			const y = cellOf(b, c);
			if (x === y) return a.key < b.key ? -1 : 1;
			//: A null sorts to the END in either direction. It is not a low value,
			//: and letting it ride the comparator would put "does not apply" at the
			//: bottom of an ascending sort and at the top of a descending one --
			//: two different claims about the same absence.
			if (x === null || x === '') return 1;
			if (y === null || y === '') return -1;
			return (x < y ? -1 : 1) * dir;
		});
	});
	const shown = $derived(selected.slice(0, CAP));

	const clearAll = () => (brush = {});
</script>

<figure class="pc">
	<figcaption>
		<h3>{art.title}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="plot" bind:clientWidth={w}>
		{#if w > 0}
			<svg width="100%" height={H} role="img" aria-label={art.title}>
				<g transform="translate({PAD.left},{PAD.top})">
					{#each order as i (art.lines[i].key)}
						<path
							d={paths[i]}
							class="line"
							class:dim={anyBrush && !hit[i]}
							class:lit={anyBrush && hit[i]}
							class:hov={hover === i}
							stroke={colour.get(art.lines[i].group) ?? '#888'}
							onpointerenter={hoverable ? () => (hover = i) : undefined}
							onpointerleave={hoverable ? () => (hover = null) : undefined}
						/>
					{/each}

					{#each art.axes as a, i (a.key)}
						{@const x = xOf(i)}
						<g transform="translate({x},0)">
							<line y1="0" y2={innerH} class="ax" />
							{#each yOf[i].ticks(Math.min(7, a.domain[1] - a.domain[0] + 1)) as t}
								<g transform="translate(0,{yOf[i](t)})">
									<line x1="-3" x2="3" class="tick" />
									{#if i === 0}<text x="-7" dy="0.32em" class="tl">{fmt(t)}</text>{/if}
								</g>
							{/each}

							{#if active[i]}
								{@const b = active[i]}
								{@const j = jitter && a.step ? a.step * JIT : 0}
								{@const padLo = b[0] <= a.domain[0] ? 0 : j}
								{@const padHi = b[1] >= a.domain[1] ? 0 : j}
								<!--
								  GROWN BY THE JITTER AMPLITUDE, because the rectangle marks
								  where the SELECTED INK IS and jittered ink for rating 4 sits
								  a fraction below 4. Drawn at the exact bounds it would show
								  lit lines poking out below it, which reads as a selection
								  bug. The label above still prints the true bounds.
								-->
								<rect
									class="sel"
									x="-7"
									width="14"
									y={yOf[i](Math.min(a.domain[1], b[1] + padHi))}
									height={Math.max(
										1,
										yOf[i](Math.max(a.domain[0], b[0] - padLo)) -
											yOf[i](Math.min(a.domain[1], b[1] + padHi))
									)}
								/>
							{/if}
							{#if drag && drag.axis === i}
								<rect
									class="drag"
									x="-7"
									width="14"
									y={Math.min(drag.y0, drag.y1)}
									height={Math.abs(drag.y1 - drag.y0)}
								/>
							{/if}

							<!--
							  The grab target is the full axis height and wider than the
							  rule, because a 1px line is not a pointer target. It sits
							  ABOVE the paths so a drag starting on a line still brushes.
							-->
							<rect
								class="grab"
								x="-9"
								width="18"
								y="0"
								height={innerH}
								role="slider"
								tabindex="0"
								aria-label="brush {a.label}"
								aria-valuemin={a.domain[0]}
								aria-valuemax={a.domain[1]}
								aria-valuenow={active[i] ? active[i][1] : a.domain[1]}
								onpointerdown={(e) => down(e, i)}
								onpointermove={move}
								onpointerup={up}
								onpointercancel={up}
							/>

							<text y={innerH + 15} class="al" text-anchor={anchor(i)}>{a.label}</text>
							{#if a.note}
								<text y={innerH + 27} class="an" text-anchor={anchor(i)}>{a.note}</text>
							{/if}
							{#if active[i]}
								<text y="-4" class="ab" text-anchor={anchor(i)}
									>{fmt(active[i][0])}–{fmt(active[i][1])}</text
								>
							{/if}
						</g>
					{/each}
				</g>
			</svg>
		{/if}
	</div>

	<div class="bar">
		<span class="count">
			<strong>{nSel.toLocaleString()}</strong> of {art.lines.length.toLocaleString()} cells
		</span>
		{#each art.groups as g (g.key)}
			<span class="key"><i style:background={g.colour}></i>{g.label} {byGroup.get(g.key)}</span>
		{/each}
		{#if jitterable}
			<label class="tog">
				<input type="checkbox" bind:checked={jitter} />
				jitter
				<span class="hint"
					>{jitter
						? `ink is offset within ±${JIT} of a step, inward only at the ends of a scale; every number here is the unjittered rating`
						: 'ink is exact, so coincident cells are indistinguishable'}</span
				>
			</label>
		{/if}
		{#if anyBrush}
			<button onclick={clearAll}>clear brush</button>
		{:else}
			<span class="hint">drag on an axis to brush; drag two axes to intersect them</span>
		{/if}
	</div>

	<!--
	  ALWAYS RENDERED. Conditionally mounting this strip made the whole table jump
	  by its height on every row hover -- and the jump moves the row you are
	  pointing at, so hovering row N can slide row N+1 under the cursor. The box
	  keeps its height and shows a hint when nothing is hovered, so the reserved
	  space is doing something rather than sitting blank.

	  Fixed height with `overflow-y: auto` rather than `overflow: hidden`: a long
	  `reading` on a narrow panel would otherwise be cut with nothing to say it
	  was, which is the failure mode this project keeps paying for.
	-->
	<div class="meta" class:idle={hover === null || !art.lines[hover]}>
		{#if hover !== null && art.lines[hover]}
			{@const l = art.lines[hover]}
			{#each art.meta_order ?? [] as k}
				{#if l.meta?.[k] !== undefined && l.meta[k] !== ''}
					<span><b>{k}</b> {l.meta[k]}</span>
				{/if}
			{/each}
		{:else}
			<span class="hint">hover a row for its full record</span>
		{/if}
	</div>

	{#if nSel > 0}
		<div class="tablewrap">
			<!--
			  "selected" ONLY WHEN SOMETHING IS SELECTED. Unbrushed, every cell is in
			  the table and calling them selected would name a filter that is not
			  applied -- a caption describing a state the figure is not in.
			-->
			<p class="tcap">
				{#if nSel > CAP}
					showing <strong>{CAP}</strong> of {nSel.toLocaleString()}
					{anyBrush ? 'selected cells' : 'cells'}{sortKey
						? `, by ${sortKey}${sortDesc ? ' descending' : ' ascending'}`
						: ', in the producer\'s order'} — <em>sort a column to change which {CAP}</em>
				{:else}
					all <strong>{nSel.toLocaleString()}</strong>
					{anyBrush ? 'selected cells' : 'cells'}
				{/if}
			</p>
			<div class="scroll">
				<table>
					<thead>
						<tr>
							{#each cols as c (c.key)}
								<th
									class:num={c.num}
									class:on={sortKey === c.key}
									aria-sort={sortKey === c.key
										? sortDesc
											? 'descending'
											: 'ascending'
										: 'none'}
								>
									<button onclick={() => sortBy(c.key)}>
										{c.label}{#if sortKey === c.key}<span class="dir"
												>{sortDesc ? '▾' : '▴'}</span
											>{/if}
									</button>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each shown as l (l.key)}
							<tr
								onpointerenter={() => (hover = indexOf.get(l.key) ?? null)}
								onpointerleave={() => (hover = null)}
							>
								{#each cols as c (c.key)}
									{@const v = cellOf(l, c)}
									<td class:num={c.num} title={c.key === 'word' ? (l.meta?.reading ?? '') : ''}>
										{#if c.key === 'word'}
											<i class="sw" style:background={colour.get(l.group)}></i>
										{/if}<!--
										  A `null` prints as an em dash and NOT as a blank. A blank
										  cell in a numeric column reads as zero at a glance, and
										  these nulls mean the dimension does not apply.
										-->{v === null ? '—' : v}
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</figure>

<style>
	.pc {
		margin: 0;
	}
	figcaption h3 {
		margin: 0 0 0.15rem;
		font-size: 1rem;
	}
	/*
	  A MEASURE, NOT THE PANEL WIDTH. Unconstrained the subtitle runs ~190
	  characters per line on a wide panel, which is far past where a line is
	  readable. 70ch was too tight the other way and turned a long subtitle into a
	  four-line wall above the chart. 120ch is past the usual 45-95 prose band,
	  which is a deliberate trade: a subtitle is read ONCE, next to the thing it
	  describes, and the ragged narrow column above a full-width panel cost more
	  than the long measure does. The cap still bites on an ultrawide display.
	*/
	.sub {
		margin: 0 0 0.7rem;
		font-size: 0.85rem;
		color: var(--text-3);
		max-width: 120ch;
	}
	.plot {
		width: 100%;
	}
	.line {
		fill: none;
		stroke-width: 1;
		stroke-opacity: 0.14;
		pointer-events: none;
	}
	/*
	  Dimmed lines stay on the panel rather than being removed. What a brush
	  selected is only legible against what it did not, and a figure that deletes
	  the remainder cannot show that a selection is a corner of the space.
	*/
	.line.dim {
		stroke: var(--text-3) !important;
		stroke-opacity: 0.045;
	}
	.line.lit {
		stroke-opacity: 0.55;
		stroke-width: 1.2;
		pointer-events: stroke;
	}
	.line.hov {
		stroke-opacity: 1;
		stroke-width: 2.5;
	}
	.ax {
		stroke: var(--text-3);
		stroke-opacity: 0.5;
	}
	.tick {
		stroke: var(--text-3);
		stroke-opacity: 0.5;
	}
	.tl,
	.al,
	.an,
	.ab {
		fill: var(--text-3);
		font-size: 9px;
	}
	.tl {
		text-anchor: end;
	}
	.al {
		font-size: 10px;
		font-weight: 600;
		fill: var(--text-2);
	}
	.an {
		opacity: 0.75;
	}
	.ab {
		font-weight: 600;
		fill: var(--text-2);
	}
	.sel {
		fill: var(--text-2);
		fill-opacity: 0.14;
		stroke: var(--text-2);
		stroke-opacity: 0.4;
	}
	.drag {
		fill: var(--text-2);
		fill-opacity: 0.24;
	}
	.grab {
		fill: transparent;
		cursor: ns-resize;
	}
	/*
	  `tabindex` makes the axis keyboard-reachable, and the browser's default ring
	  then fires on POINTER focus too -- so every click on an axis left a heavy
	  blue capsule around it that read as a selection state the figure does not
	  have. `:focus-visible` is the distinction: keyboard focus keeps an
	  indicator, a click does not paint one.
	*/
	.grab:focus {
		outline: none;
	}
	.grab:focus-visible {
		outline: 1px solid var(--text-2);
		outline-offset: 1px;
	}
	.bar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem 1rem;
		margin-top: 0.5rem;
		font-size: 0.8rem;
		color: var(--text-3);
	}
	.count strong {
		color: var(--text-1);
	}
	.key i {
		display: inline-block;
		width: 14px;
		height: 2px;
		margin-right: 0.35rem;
		vertical-align: middle;
	}
	.hint {
		opacity: 0.7;
		font-style: italic;
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
	.bar button {
		font: inherit;
		color: inherit;
		background: none;
		border: 1px solid currentColor;
		border-radius: 3px;
		padding: 0 0.4rem;
		cursor: pointer;
		opacity: 0.8;
	}
	.meta {
		display: flex;
		flex-wrap: wrap;
		align-content: flex-start;
		gap: 0.25rem 0.9rem;
		margin-top: 0.4rem;
		font-size: 0.78rem;
		line-height: 1.35;
		color: var(--text-2);
		/* two lines of the strip, reserved whether or not anything is hovered */
		height: 2.7em;
		overflow-y: auto;
	}
	.meta.idle {
		color: var(--text-3);
	}
	.meta b {
		color: var(--text-3);
		font-weight: 500;
	}
	.tablewrap {
		margin-top: 0.6rem;
	}
	.tcap {
		margin: 0 0 0.3rem;
		font-size: 0.75rem;
		color: var(--text-3);
	}
	.tcap strong {
		color: var(--text-1);
	}
	.scroll {
		max-height: 20rem;
		overflow: auto;
	}
	table {
		border-collapse: collapse;
		font-size: 0.75rem;
		width: 100%;
	}
	thead th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--bg-1, #12131a);
		text-align: left;
		font-weight: 500;
		color: var(--text-3);
		border-bottom: 1px solid var(--text-3);
		padding: 0;
		white-space: nowrap;
	}
	thead th.on {
		color: var(--text-1);
	}
	thead th button {
		font: inherit;
		color: inherit;
		background: none;
		border: 0;
		padding: 0.25rem 0.45rem;
		cursor: pointer;
		width: 100%;
		text-align: inherit;
	}
	th.num button {
		text-align: right;
	}
	.dir {
		margin-left: 0.15rem;
	}
	tbody td {
		padding: 0.12rem 0.45rem;
		color: var(--text-2);
		border-bottom: 1px solid color-mix(in srgb, var(--text-3) 18%, transparent);
		white-space: nowrap;
		max-width: 22rem;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	td.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	tbody tr:hover td {
		background: color-mix(in srgb, var(--text-3) 12%, transparent);
	}
	.sw {
		display: inline-block;
		width: 7px;
		height: 7px;
		border-radius: 50%;
		margin-right: 0.35rem;
		vertical-align: baseline;
	}
</style>
