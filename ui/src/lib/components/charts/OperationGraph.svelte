<!--
  The annotation graph: `M##_word -> [operation] -> M##_word`, drawn live.

  RH, 2026-08-22: *"I simply can't process the quality of the annotations."* A PNG
  cannot answer that. What a reader needs is to point at a hub, read the statement
  its rater wrote, see which models it placed and with which words, and pull the
  thing apart by hand. So this is a force simulation with drag and a detail panel,
  not a picture of one.

  ## TWO GRAINS FROM ONE ARTIFACT

  Word grain is the truth: every cited word, and it is what makes a component
  checkable. It is also 800 nodes, which is more than a browser force simulation
  is comfortable with and more than a reader can scan. Model grain collapses each
  model's words to one node, about 50, which is enough to answer "who is in this
  operation". Both come from the same nodes because every word node carries its
  `model`; nothing is recomputed, so the two views cannot disagree.
-->
<script lang="ts">
	import { ForceSimulation } from 'layerchart/force';
	import { forceManyBody, forceLink, forceCenter, forceCollide, forceX, forceY } from 'd3-force';

	type Node = {
		id: string;
		kind: 'op' | 'word';
		label: string;
		group: string | null;
		component: number;
		model?: string;
		side?: 'from' | 'to';
		n?: number;
		statement?: string;
		models?: string[];
	};
	type Art = {
		title: string;
		subtitle?: string;
		nodes: Node[];
		links: { source: string; target: string }[];
		groups: { key: string; label: string; colour: string }[];
		meta?: {
			components?: { operations: number; models: number }[];
			coverage?: { reading: string; placed: number; reversed: number; unassigned: number }[];
		};
	};
	let { art }: { art: Art } = $props();

	const DASH = '—';
	const H = 620;
	let grain = $state<'model' | 'word'>('model');
	let hidden = $state<string[]>([]);
	let picked = $state<Node | null>(null);
	let hover = $state<string | null>(null);
	let w = $state(0);
	let panel: HTMLDivElement | undefined = $state();

	const colour = $derived(new Map(art.groups.map((g) => [g.key, g.colour])));
	const live = $derived(art.nodes.filter((n) => n.kind !== 'op' || !hidden.includes(n.group!)));
	const liveIds = $derived(new Set(live.map((n) => n.id)));

	//: BUILT FRESH EVERY TIME, never handed the artifact's own objects. d3-force
	//: WRITES x/y/vx/vy onto the nodes it is given, so passing `art.nodes` in would
	//: let a grain switch inherit the previous layout and start the simulation from
	//: a shape it should have been free to find.
	const view = $derived.by(() => {
		if (grain === 'word') {
			const ns = live.map((n) => ({ ...n }));
			const ok = new Set(ns.map((n) => n.id));
			return {
				nodes: ns,
				links: art.links
					.filter((l) => ok.has(l.source) && ok.has(l.target))
					.map((l) => ({ ...l }))
			};
		}
		//: Model grain: one node per model, linked to every operation that placed it.
		//: Multiplicity is dropped deliberately. The question here is "is this model
		//: in that operation", not how many of its words the rater chose to list.
		const keep = new Map<string, any>();
		for (const n of live) if (n.kind === 'op') keep.set(n.id, { ...n });
		for (const n of live) {
			if (n.kind === 'word' && n.model && !keep.has('M::' + n.model)) {
				keep.set('M::' + n.model, {
					id: 'M::' + n.model,
					kind: 'word',
					label: n.model,
					group: null,
					component: n.component,
					model: n.model
				});
			}
		}
		const seen = new Set<string>();
		const ls: any[] = [];
		for (const l of art.links) {
			if (!liveIds.has(l.source) || !liveIds.has(l.target)) continue;
			const s = l.source.startsWith('OP[') ? l.source : 'M::' + l.source.split('::')[0];
			const t = l.target.startsWith('OP[') ? l.target : 'M::' + l.target.split('::')[0];
			const k = s + ' ' + t;
			if (!seen.has(k) && keep.has(s) && keep.has(t)) {
				seen.add(k);
				ls.push({ source: s, target: t });
			}
		}
		return { nodes: [...keep.values()], links: ls };
	});

	const forces = $derived({
		link: forceLink(view.links)
			.id((d: any) => d.id)
			.distance(grain === 'word' ? 26 : 60)
			.strength(0.35),
		charge: forceManyBody().strength(grain === 'word' ? -22 : -180),
		collide: forceCollide().radius((d: any) => (d.kind === 'op' ? 22 : 9)),
		center: forceCenter(w / 2, H / 2),
		//: A WEAK PULL TO CENTRE ON BOTH AXES. Disjoint components feel no link
		//: force between them, so with `center` alone the small ones drift off the
		//: panel and read as absent rather than as separate.
		x: forceX(w / 2).strength(0.035),
		y: forceY(H / 2).strength(0.035)
	});

	//: Recovered from the ARTIFACT, never from the simulation's nodes, which d3 has
	//: mutated in place.
	function wordsFor(model: string, op?: string) {
		const f = new Set<string>();
		const t = new Set<string>();
		for (const l of art.links) {
			if (l.source.startsWith(model + '::') && (!op || l.target === op))
				f.add(l.source.split('::')[1]);
			if (l.target.startsWith(model + '::') && (!op || l.source === op))
				t.add(l.target.split('::')[1]);
		}
		return { from: [...f].sort(), to: [...t].sort() };
	}
	const placedBy = (m: string) =>
		art.nodes.filter((x) => x.kind === 'op' && x.models?.includes(m));
	const toggle = (k: string) =>
		(hidden = hidden.includes(k) ? hidden.filter((x) => x !== k) : [...hidden, k]);

	let drag = $state<any>(null);
	function down(e: PointerEvent, n: any, sim: any) {
		drag = n;
		sim.alphaTarget(0.25).restart();
	}
	function move(e: PointerEvent, sim: any) {
		const box = panel?.getBoundingClientRect();
		if (!drag || !box) return;
		drag.fx = e.clientX - box.left;
		drag.fy = e.clientY - box.top;
		sim.alpha(Math.max(sim.alpha(), 0.2)).restart();
	}
	function up(sim: any) {
		if (drag) {
			drag.fx = null;
			drag.fy = null;
		}
		drag = null;
		sim?.alphaTarget(0);
	}
</script>

<figure class="og">
	<figcaption>
		<h3>{art.title}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="bar">
		<span class="seg">
			{#each ['model', 'word'] as g (g)}
				<button class:on={grain === g} onclick={() => (grain = g as any)}>{g} grain</button>
			{/each}
		</span>
		<span class="count">{view.nodes.length} nodes, {view.links.length} links</span>
		{#each art.groups as g (g.key)}
			<button class="key" class:off={hidden.includes(g.key)} onclick={() => toggle(g.key)}>
				<i style:background={g.colour}></i>{g.label}
			</button>
		{/each}
		{#each art.meta?.components ?? [] as c, i (i)}
			<span class="cmp">component {i + 1}: {c.operations} op, {c.models} models</span>
		{/each}
	</div>

	<div class="stage">
		<div class="plot" bind:clientWidth={w} bind:this={panel}>
			{#if w > 0}
				{#key grain + hidden.join()}
					<ForceSimulation data={view} {forces} cloneNodes={false} alphaDecay={0.02}>
						{#snippet children({ nodes, linkPositions, simulation })}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<svg
								width={w}
								height={H}
								onpointermove={(e) => move(e, simulation)}
								onpointerup={() => up(simulation)}
								onpointerleave={() => up(simulation)}
							>
								{#each linkPositions as l, i (i)}
									<line x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} class="edge" />
								{/each}
								{#each nodes as n (n.id)}
									{@const op = n.kind === 'op'}
									<!-- svelte-ignore a11y_click_events_have_key_events -->
									<circle
										cx={n.x}
										cy={n.y}
										class:hov={hover === n.id}
										r={op ? Math.min(20, 7 + (n.n ?? 1) * 0.35) : grain === 'model' ? 6 : 3}
										fill={op && n.group ? colour.get(n.group) : n.component === 0 ? '#8b94a3' : '#ffd43b'}
										class:op
										class:sel={picked?.id === n.id}
										onpointerdown={(e) => down(e, n, simulation)}
										onpointerenter={() => (hover = n.id)}
										onpointerleave={() => (hover = null)}
										onclick={() => (picked = n)}
									>
										<title>{op ? n.label + ' (' + n.n + ')' : n.label}</title>
									</circle>
									{#if op || hover === n.id || picked?.id === n.id}
										<!--
										  HUBS ALWAYS, MODELS ONLY ON HOVER OR SELECTION. Labelling
										  every model node at 55 nodes produced an unreadable smear
										  exactly where the graph is densest, which is where a reader
										  looks. The panel carries the identity anyway, so the label
										  was redundant as well as illegible.
										-->
										<text x={n.x} y={n.y - (op ? 15 : 10)} class="lab" class:oplab={op}
											>{n.label}</text
										>
									{/if}
								{/each}
							</svg>
						{/snippet}
					</ForceSimulation>
				{/key}
			{/if}
		</div>

		<aside class="side">
			{#if !picked}
				<p class="hint">
					Click an operation to read the statement its rater wrote, or a model to see the words it
					contributed. Drag anything. Switch to <b>word grain</b> for every cited word, which is what
					makes a component checkable and is roughly 800 nodes.
				</p>
				{#if art.meta?.coverage}
					<p class="covh">what reached this graph</p>
					<table class="cov">
						<thead>
							<tr><th>reading</th><th class="n">placed</th><th class="n">rev</th><th class="n">unas</th></tr>
						</thead>
						<tbody>
							{#each art.meta.coverage as c (c.reading)}
								<tr>
									<td>{c.reading}</td><td class="n">{c.placed}</td>
									<td class="n">{c.reversed}</td><td class="n">{c.unassigned}</td>
								</tr>
							{/each}
						</tbody>
					</table>
					<p class="hint sm">
						<code>unassigned</code> carries no words and <code>reversed</code> is excluded, so a model
						in neither column is absent from this graph entirely.
					</p>
				{/if}
			{:else if picked.kind === 'op'}
				<header>
					<i style:background={picked.group ? colour.get(picked.group) : undefined}></i>
					<strong>{picked.label}</strong>
					<span class="muted">{picked.group}, {picked.n} members</span>
					<button class="close" onclick={() => (picked = null)}>close</button>
				</header>
				<p class="stmt">{picked.statement}</p>
				<p class="covh">members, and the words that placed them</p>
				<div class="mems">
					{#each picked.models ?? [] as m (m)}
						{@const ws = wordsFor(m, picked.id)}
						<div class="mem">
							<b>{m}</b>
							<span class="fr">{ws.from.join(' ') || DASH}</span>
							<span class="to">{ws.to.join(' ') || DASH}</span>
						</div>
					{/each}
				</div>
			{:else}
				{@const who = picked.model ?? picked.label}
				{@const ws = wordsFor(who)}
				<header>
					<strong>{who}</strong>
					<span class="muted">component {picked.component + 1}</span>
					<button class="close" onclick={() => (picked = null)}>close</button>
				</header>
				<p class="covh">pooled over every operation that placed it</p>
				<p class="fr">{ws.from.join(' ') || DASH}</p>
				<p class="to">{ws.to.join(' ') || DASH}</p>
				<p class="covh">placed by</p>
				<ul class="ops">
					{#each placedBy(who) as o (o.id)}
						<li><i style:background={o.group ? colour.get(o.group) : undefined}></i>{o.label}
							<span class="muted">{o.group}</span></li>
					{/each}
				</ul>
			{/if}
		</aside>
	</div>
</figure>

<style>
	.og {
		margin: 0;
	}
	figcaption h3 {
		margin: 0 0 0.15rem;
		font-size: 1rem;
	}
	.sub {
		margin: 0 0 0.6rem;
		font-size: 0.85rem;
		color: var(--text-3);
		max-width: 120ch;
	}
	.bar {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.35rem 0.9rem;
		font-size: 0.78rem;
		color: var(--text-3);
		margin-bottom: 0.4rem;
	}
	.seg button {
		font: inherit;
		color: inherit;
		background: none;
		cursor: pointer;
		border: 1px solid var(--text-3);
		padding: 0 0.4rem;
	}
	.seg button:first-child {
		border-radius: 3px 0 0 3px;
	}
	.seg button:last-child {
		border-radius: 0 3px 3px 0;
		border-left: 0;
	}
	.seg button.on {
		color: var(--text-1);
		background: color-mix(in srgb, var(--text-3) 22%, transparent);
	}
	.key {
		font: inherit;
		color: inherit;
		background: none;
		border: 0;
		padding: 0;
		cursor: pointer;
	}
	.key.off {
		opacity: 0.32;
	}
	.key i,
	header i,
	.ops i {
		display: inline-block;
		width: 9px;
		height: 9px;
		border-radius: 50%;
		margin-right: 0.3rem;
		vertical-align: baseline;
	}
	.cmp {
		font-style: italic;
		opacity: 0.75;
	}
	.stage {
		display: grid;
		grid-template-columns: 1fr minmax(300px, 25rem);
		gap: 1rem;
		align-items: start;
	}
	.plot {
		position: relative;
	}
	.side {
		max-height: 620px;
		overflow-y: auto;
		font-size: 0.8rem;
	}
	.edge {
		stroke: #5c6472;
		stroke-opacity: 0.3;
		stroke-width: 0.7;
	}
	circle {
		cursor: grab;
	}
	circle.op {
		stroke: var(--bg-1, #12131a);
		stroke-width: 1.5;
	}
	circle.sel {
		stroke: #fff;
		stroke-width: 2;
	}
	circle.hov {
		stroke: var(--text-1);
		stroke-width: 1.5;
	}
	.lab {
		font-size: 8.5px;
		fill: var(--text-3);
		text-anchor: middle;
		pointer-events: none;
	}
	.oplab {
		font-size: 10px;
		fill: var(--text-1);
		font-weight: 600;
		paint-order: stroke;
		stroke: var(--bg-1, #12131a);
		stroke-width: 3px;
	}
	.hint {
		margin: 0 0 0.7rem;
		color: var(--text-3);
		font-style: italic;
		line-height: 1.5;
	}
	.hint.sm {
		font-size: 0.74rem;
	}
	header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.4rem;
		margin-bottom: 0.4rem;
	}
	.close {
		margin-left: auto;
		font: inherit;
		color: inherit;
		background: none;
		border: 1px solid currentColor;
		border-radius: 3px;
		padding: 0 0.4rem;
		cursor: pointer;
	}
	.stmt {
		margin: 0 0 0.7rem;
		color: var(--text-2);
		line-height: 1.5;
	}
	.covh {
		margin: 0.6rem 0 0.25rem;
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-3);
	}
	.mem {
		margin-bottom: 0.45rem;
	}
	.mem b {
		display: block;
		font-weight: 600;
		color: var(--text-2);
		font-size: 0.76rem;
	}
	.fr,
	.to {
		margin: 0;
		font-size: 0.76rem;
		line-height: 1.45;
	}
	.fr {
		color: #fa5252;
	}
	.to {
		color: #4dabf7;
	}
	.fr::before {
		content: 'from ';
		color: var(--text-3);
	}
	.to::before {
		content: 'to ';
		color: var(--text-3);
	}
	.cov {
		border-collapse: collapse;
		font-size: 0.74rem;
	}
	.cov th {
		text-align: left;
		font-weight: 500;
		color: var(--text-3);
		padding: 0.1rem 0.5rem 0.1rem 0;
	}
	.cov td {
		padding: 0.1rem 0.5rem 0.1rem 0;
		color: var(--text-2);
	}
	.cov .n {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.ops {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.ops li {
		padding: 0.1rem 0;
		color: var(--text-2);
		font-size: 0.76rem;
	}
	.muted {
		color: var(--text-3);
	}
	@media (max-width: 900px) {
		.stage {
			grid-template-columns: 1fr;
		}
	}
</style>
