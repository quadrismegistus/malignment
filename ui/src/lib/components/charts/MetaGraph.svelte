<script lang="ts">
	//: THE CROSS-FRAME NETWORK, WITH A PANEL THAT DRILLS FOUR LEVELS.
	//:
	//:     meta-relation -> component -> within-prompt relation -> model + words
	//:
	//: `OperationGraph` cannot serve this and was not stretched to. Its panel
	//: recovers words by WALKING LINKS, which works because every word is a node
	//: on its canvas. Here only two of the four levels are drawn; the lower two
	//: ride on the leaf and are read from it, so the panel is a different object
	//: even though the canvas looks similar.
	//:
	//: Pointed at this file by `chart: "metagraph"`, which the producer sets
	//: AFTER `graph()` validates the artifact -- the dangling-endpoint assert is
	//: wanted, the two-level drawing is not.
	import { ForceSimulation } from 'layerchart/force';
	import { forceManyBody, forceLink, forceCollide, forceCenter, forceX, forceY } from 'd3-force';

	type Word = { w: string; ra: number | null; rb: number | null };
	type Member = { model: string; from: Word[]; to: Word[] };
	type Relation = { name: string; reading: string; statement: string; n: number; members: Member[] };
	type Node = {
		id: string;
		kind: 'op' | 'word';
		label: string;
		group: string | null;
		//: hubs
		n?: number;
		statement?: string;
		spans?: string;
		why?: string;
		sentences?: number;
		domains?: Record<string, number>;
		models?: string[];
		//: leaves
		cid?: string;
		sentence?: string;
		n_models?: number;
		stripped?: boolean;
		relations?: Relation[];
	};
	type Art = {
		title: string;
		subtitle?: string;
		nodes: Node[];
		links: { source: string; target: string; cross?: boolean; weak?: boolean }[];
		groups: { key: string; label: string; colour: string }[];
	};
	let { art }: { art: Art } = $props();

	const H = 640;
	let w = $state(0);
	let panel: HTMLDivElement | undefined = $state();
	let hidden = $state<string[]>([]);
	let hover = $state<string | null>(null);
	//: TWO SELECTIONS, NOT ONE. A component reached from a hub keeps the hub, so
	//: the panel can offer a way back; a component reached by clicking the canvas
	//: has no hub and says so. One `picked` would lose that distinction.
	let hub = $state<Node | null>(null);
	let leaf = $state<Node | null>(null);
	let rel = $state<number>(0);

	const colour = $derived(new Map(art.groups.map((g) => [g.key, g.colour])));
	const byId = $derived(new Map(art.nodes.map((n) => [n.id, n])));
	const hubs = $derived(art.nodes.filter((n) => n.kind === 'op'));
	const live = $derived(
		art.nodes.filter((n) => n.kind === 'op' || !hidden.includes(n.group ?? ''))
	);
	const liveIds = $derived(new Set(live.map((n) => n.id)));

	//: BUILT FRESH, never handed the artifact's own objects: d3-force writes
	//: x/y/vx/vy onto whatever it is given.
	const view = $derived.by(() => {
		//: `any[]`, deliberately. d3-force types its nodes as `SimulationNodeDatum`
		//: and MUTATES them with x/y/vx/vy, so a precisely-typed array is rejected
		//: at the boundary and every field read back out of the snippet is an
		//: error. The artifact's shape is checked by `graph()` on the producer
		//: side; asserting it again here buys nothing and costs the render.
		const ns: any[] = live.map((n) => ({ ...n }));
		const ok = new Set(ns.map((n) => n.id));
		return {
			nodes: ns,
			links: art.links.filter((l) => ok.has(l.source) && ok.has(l.target)).map((l) => ({ ...l }))
		};
	});

	const forces = $derived({
		//: A WEAK LINK IS DRAWN AND EXERTS NO FORCE. It is a component sitting in
		//: one rater's relation and a DIFFERENT rater's, where those two relations
		//: share fewer than k components -- so the picture should show the two
		//: relations touching without letting one component weld them into one
		//: cluster. Dropping it would make the graph agree with the threshold by
		//: hiding what the threshold is a judgement about.
		link: forceLink(view.links)
			.id((d: any) => d.id)
			.distance((l: any) => (l.weak ? 90 : 34))
			.strength((l: any) => (l.weak ? 0 : 0.4)),
		charge: forceManyBody().strength(-70),
		collide: forceCollide().radius((d: any) => (d.kind === 'op' ? 18 : 6)),
		center: forceCenter(w / 2, H / 2),
		//: Unplaced components have no link at all, so without a weak pull to
		//: centre they drift off the panel and read as absent rather than as
		//: unplaced -- which is the one thing about them worth seeing.
		x: forceX(w / 2).strength(0.04),
		y: forceY(H / 2).strength(0.04)
	});

	const linked = $derived(
		new Set(art.links.filter((l) => l.target === hub?.id).map((l) => l.source))
	);
	const members = $derived(
		hub ? art.nodes.filter((n) => n.kind === 'word' && linked.has(n.id)) : []
	);
	const unplaced = $derived(
		new Set(
			art.nodes
				.filter((n) => n.kind === 'word' && !art.links.some((l) => l.source === n.id))
				.map((n) => n.id)
		)
	);

	function openHub(n: Node) {
		hub = n;
		leaf = null;
		rel = 0;
	}
	function openLeaf(n: Node) {
		leaf = n;
		rel = 0;
	}
	const fmt = (xs: Word[]) =>
		xs.length ? xs.map((x) => `${x.w} (${x.ra ?? '-'}→${x.rb ?? '-'})`).join('; ') : '—';

	let drag = $state<any>(null);
	let pan = $state({ x: 0, y: 0 });
	let grab: { x: number; y: number } | null = $state(null);
	function down(e: PointerEvent, n: any, sim: any) {
		drag = n;
		sim.alphaTarget(0.25).restart();
	}
	function panDown(e: PointerEvent) {
		grab = { x: e.clientX - pan.x, y: e.clientY - pan.y };
	}
	function move(e: PointerEvent, sim: any) {
		if (grab) {
			pan = { x: e.clientX - grab.x, y: e.clientY - grab.y };
			return;
		}
		const box = panel?.getBoundingClientRect();
		if (!drag || !box) return;
		drag.fx = e.clientX - box.left - pan.x;
		drag.fy = e.clientY - box.top - pan.y;
		sim.alpha(Math.max(sim.alpha(), 0.2)).restart();
	}
	function up(sim: any) {
		if (drag) {
			drag.fx = null;
			drag.fy = null;
		}
		drag = null;
		grab = null;
		sim?.alphaTarget(0);
	}
	const toggle = (k: string) =>
		(hidden = hidden.includes(k) ? hidden.filter((x) => x !== k) : [...hidden, k]);
</script>

<figure class="mg">
	<figcaption>
		<h3>{art.title}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="bar">
		<span class="count">{hubs.length} relations, {view.nodes.length - hubs.length} components</span>
		{#each art.groups as g (g.key)}
			<button class="key" class:off={hidden.includes(g.key)} onclick={() => toggle(g.key)}>
				<i style:background={g.colour}></i>{g.label}
			</button>
		{/each}
		<span class="count dim">{unplaced.size} unplaced</span>
		<span class="count dim"
			>{art.links.filter((l) => l.weak).length} weak bridges (below k=3, drawn without pull)</span
		>
	</div>

	<div class="stage">
		<div class="plot" bind:clientWidth={w} bind:this={panel}>
			{#if w > 0}
				{#key hidden.join()}
					<ForceSimulation data={view} {forces} cloneNodes={false} alphaDecay={0.02}>
						{#snippet children({ nodes, linkPositions, simulation })}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<svg
								width={w}
								height={H}
								class:grabbing={grab}
								onpointermove={(e) => move(e, simulation)}
								onpointerup={() => up(simulation)}
								onpointerleave={() => up(simulation)}
							>
								<rect
									x="0"
									y="0"
									width={w}
									height={H}
									fill="transparent"
									onpointerdown={panDown}
									ondblclick={() => (pan = { x: 0, y: 0 })}
								/>
								<g transform="translate({pan.x},{pan.y})">
									{#each linkPositions as l, i (i)}
										<line
											x1={l.x1}
											y1={l.y1}
											x2={l.x2}
											y2={l.y2}
											class="edge"
											class:cross={view.links[i]?.cross}
											class:weak={view.links[i]?.weak}
										/>
									{/each}
									{#each nodes as n (n.id)}
										{@const op = n.kind === 'op'}
										<!-- svelte-ignore a11y_click_events_have_key_events -->
										<circle
											cx={n.x}
											cy={n.y}
											r={op ? Math.min(17, 6 + (n.n ?? 1) * 0.55) : 5}
											fill={op ? '#c8ccd4' : (colour.get(n.group ?? '') ?? '#8b94a3')}
											class:op
											class:sel={hub?.id === n.id || leaf?.id === n.id}
											class:hov={hover === n.id}
											class:unplaced={unplaced.has(n.id)}
											onpointerdown={(e) => down(e, n, simulation)}
											onpointerenter={() => (hover = n.id)}
											onpointerleave={() => (hover = null)}
											onclick={() => (op ? openHub(n as Node) : openLeaf(byId.get(n.id) as Node))}
										>
											<title
												>{op
													? `${n.label} — ${n.n} components, ${n.sentences} sentences`
													: `${n.cid} — ${n.sentence}`}</title
											>
										</circle>
										{#if op || hover === n.id || leaf?.id === n.id}
											<text x={n.x} y={n.y - (op ? 13 : 9)} class="lab" class:oplab={op}
												>{op ? n.label : n.cid}</text
											>
										{/if}
									{/each}
								</g>
							</svg>
						{/snippet}
					</ForceSimulation>
				{/key}
			{/if}
		</div>

		<aside class="side">
			{#if !hub && !leaf}
				<p class="hint">
					Click a <b>relation</b> to see the components it grouped, then a component to reach the
					readers who named it and the models they placed. Grey hubs are relations; coloured dots are
					components, coloured by the domain the grouping reader never saw. Drag the background to
					pan.
				</p>
				<p class="covh">relations, widest first</p>
				<table class="cov">
					<thead><tr><th>relation</th><th class="n">comps</th><th class="n">sent</th></tr></thead>
					<tbody>
						{#each [...hubs].sort((a, b) => (b.n ?? 0) - (a.n ?? 0)) as h (h.id)}
							<tr class="click" onclick={() => openHub(h)}>
								<td>{h.label}</td><td class="n">{h.n}</td><td class="n">{h.sentences}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{:else if hub && !leaf}
				<header>
					<strong>{hub.label}</strong>
					<span class="muted">{hub.n} components, {hub.sentences} sentences</span>
					<button class="close" onclick={() => (hub = null)}>close</button>
				</header>
				<p class="stmt">{hub.statement}</p>
				{#if hub.spans}<p class="why"><b>spans</b> {hub.spans}</p>{/if}
				{#if hub.why}<p class="why"><b>why</b> {hub.why}</p>{/if}
				<p class="covh">components — click one to drill down</p>
				{#each members as m (m.id)}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="mem click" onclick={() => openLeaf(m)}>
						<b><i style:background={colour.get(m.group ?? '')}></i>{m.cid}</b>
						<span class="sent">{m.sentence}</span>
						<span class="muted"
							>{m.relations?.length} reading(s), {m.n_models} systems{m.stripped
								? ', blanks stripped'
								: ''}</span
						>
					</div>
				{/each}
			{:else if leaf}
				<header>
					<button class="back" onclick={() => (leaf = null)} disabled={!hub}
						>{hub ? '← ' + hub.label : 'component'}</button
					>
					<button class="close" onclick={() => ((leaf = null), (hub = null))}>close</button>
				</header>
				<p class="sent big">{leaf.sentence}</p>
				<p class="muted sm">
					{leaf.cid} · {leaf.n_models} systems{leaf.stripped ? ' · blanks stripped' : ''}
					{#if unplaced.has(leaf.id)} · <b>no relation grouped this</b>{/if}
				</p>
				<p class="covh">readings of this component</p>
				<div class="tabs">
					{#each leaf.relations ?? [] as r, i (r.name + r.reading)}
						<button class:on={rel === i} onclick={() => (rel = i)}>{r.name} ({r.n})</button>
					{/each}
				</div>
				{#if leaf.relations?.[rel]}
					{@const r = leaf.relations[rel]}
					<p class="stmt">{r.statement}</p>
					<p class="covh">{r.members.length} systems, and the words that placed them</p>
					<div class="mems">
						{#each r.members as m (m.model)}
							<div class="mem">
								<b>{m.model}</b>
								<span class="fr">{fmt(m.from)}</span>
								<span class="to">{fmt(m.to)}</span>
							</div>
						{/each}
					</div>
				{/if}
			{/if}
		</aside>
	</div>
</figure>

<style>
	.mg {
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
		margin-bottom: 0.4rem;
	}
	.count {
		color: var(--text-3);
	}
	.count.dim {
		opacity: 0.7;
	}
	.key {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		background: none;
		border: 1px solid var(--line, #2a2f3a);
		border-radius: 3px;
		padding: 0.1rem 0.4rem;
		color: var(--text-2);
		cursor: pointer;
		font-size: 0.75rem;
	}
	.key.off {
		opacity: 0.35;
	}
	.key i,
	.mem i {
		width: 0.55rem;
		height: 0.55rem;
		border-radius: 50%;
		display: inline-block;
		margin-right: 0.3rem;
	}
	.stage {
		display: grid;
		grid-template-columns: 1fr 380px;
		gap: 0.8rem;
	}
	.plot {
		min-width: 0;
		border: 1px solid var(--line, #2a2f3a);
		border-radius: 4px;
		overflow: hidden;
	}
	svg {
		cursor: grab;
		touch-action: none;
		display: block;
	}
	svg.grabbing {
		cursor: grabbing;
	}
	.edge {
		stroke: #5c6472;
		stroke-opacity: 0.35;
		stroke-width: 0.7;
	}
	/* A link into a relation whose components come from more than one domain.
	   That is the whole question the picture exists for, so it is marked. */
	.edge.cross {
		stroke: #ffd43b;
		stroke-opacity: 0.5;
		stroke-width: 1;
	}
	/* Below the threshold: two relations touch here, but not enough to be one.
	   Faint and dotted so it reads as contact rather than as structure. */
	.edge.weak {
		stroke: #5c6472;
		stroke-opacity: 0.22;
		stroke-width: 0.6;
		stroke-dasharray: 1.5 3;
	}
	circle {
		cursor: pointer;
	}
	circle.op {
		stroke: var(--ground);
		stroke-width: 1.5;
	}
	circle.sel {
		stroke: #fff;
		stroke-width: 2;
	}
	circle.hov {
		stroke: #fff;
		stroke-width: 1.2;
	}
	/* Drawn, not hidden: a component no reader could place is a fact about the
	   corpus and omitting it would flatter the grouping. */
	circle.unplaced {
		stroke: #5c6472;
		stroke-width: 1.4;
		stroke-dasharray: 2 2;
	}
	.lab {
		fill: var(--text-2, #c8ccd4);
		font-size: 0.55rem;
		text-anchor: middle;
		pointer-events: none;
		stroke: none;
	}
	.lab.oplab {
		fill: var(--text, #f2f4f8);
		font-size: 0.68rem;
	}
	.side {
		border: 1px solid var(--line, #2a2f3a);
		border-radius: 4px;
		padding: 0.6rem 0.7rem;
		overflow-y: auto;
		max-height: 640px;
		font-size: 0.8rem;
	}
	.side header {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
		margin-bottom: 0.4rem;
	}
	.side header strong {
		font-size: 0.95rem;
	}
	.close,
	.back {
		margin-left: auto;
		background: none;
		border: 1px solid var(--line, #2a2f3a);
		border-radius: 3px;
		color: var(--text-3);
		cursor: pointer;
		font-size: 0.7rem;
		padding: 0.05rem 0.35rem;
	}
	.back {
		margin-left: 0;
		color: var(--text-2);
	}
	.back:disabled {
		opacity: 0.4;
		cursor: default;
	}
	.muted {
		color: var(--text-3);
		font-size: 0.75rem;
	}
	.muted.sm {
		font-size: 0.72rem;
	}
	.hint {
		color: var(--text-3);
		line-height: 1.45;
		margin: 0 0 0.6rem;
	}
	.covh {
		text-transform: uppercase;
		letter-spacing: 0.04em;
		font-size: 0.66rem;
		color: var(--text-3);
		margin: 0.7rem 0 0.3rem;
	}
	.stmt {
		margin: 0.2rem 0 0.4rem;
		line-height: 1.45;
	}
	.why {
		margin: 0.2rem 0;
		color: var(--text-3);
		font-size: 0.75rem;
		line-height: 1.4;
	}
	.sent {
		color: var(--text-2);
		font-style: italic;
	}
	.sent.big {
		font-size: 0.9rem;
		margin: 0.1rem 0 0.2rem;
	}
	.cov {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.75rem;
	}
	.cov th,
	.cov td {
		text-align: left;
		padding: 0.12rem 0.25rem;
		border-bottom: 1px solid var(--line, #2a2f3a);
	}
	.cov .n {
		text-align: right;
		color: var(--text-3);
	}
	.click {
		cursor: pointer;
	}
	.click:hover {
		background: rgba(255, 255, 255, 0.04);
	}
	.mems {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.mem {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		padding: 0.25rem 0.3rem;
		border-left: 2px solid var(--line, #2a2f3a);
	}
	.mem b {
		font-size: 0.78rem;
	}
	.fr {
		color: #fa5252;
		font-size: 0.72rem;
		line-height: 1.35;
	}
	.to {
		color: #4dabf7;
		font-size: 0.72rem;
		line-height: 1.35;
	}
	.tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
		margin: 0.2rem 0 0.4rem;
	}
	.tabs button {
		background: none;
		border: 1px solid var(--line, #2a2f3a);
		border-radius: 3px;
		color: var(--text-3);
		cursor: pointer;
		font-size: 0.7rem;
		padding: 0.1rem 0.35rem;
	}
	.tabs button.on {
		color: var(--text);
		border-color: var(--text-3);
	}
</style>
