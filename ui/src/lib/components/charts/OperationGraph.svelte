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
		links: { source: string; target: string; cross?: boolean }[];
		groups: { key: string; label: string; colour: string }[];
		meta?: {
			components?: { operations: number; models: number }[];
			coverage?: { reading: string; placed: number; reversed: number; unassigned: number }[];
			reversals?: Rev[];
		};
	};
	//: A MODEL THE RATER SAYS RUNS THE OPERATION BACKWARDS. Not a member -- it
	//: would put the opposite movement inside the cluster -- but a judgement about
	//: that operation, so it is drawn as a red dashed line to the hub rather than
	//: left out of the picture entirely.
	type Rev = {
		model: string;
		op: string;
		reading: string;
		a_words: string[];
		b_words: string[];
		how_you_know: string;
	};
	let { art }: { art: Art } = $props();

	const DASH = '—';
	const H = 620;
	let grain = $state<'model' | 'word'>('model');
	let hidden = $state<string[]>([]);
	let picked = $state<Node | null>(null);
	let hover = $state<string | null>(null);
	let showRev = $state(true);
	let w = $state(0);
	let panel: HTMLDivElement | undefined = $state();

	const colour = $derived(new Map(art.groups.map((g) => [g.key, g.colour])));
	const live = $derived(art.nodes.filter((n) => n.kind !== 'op' || !hidden.includes(n.group!)));
	const liveIds = $derived(new Set(live.map((n) => n.id)));
	const revs = $derived(art.meta?.reversals ?? []);
	//: Live reversals only: a reversal whose OPERATION has been filtered out of the
	//: legend has nothing to point at, and a red line to a hidden hub is a line to
	//: nowhere. Keyed on the op node so the filter needs no second rule.
	const revLive = $derived(revs.filter((r) => liveIds.has(r.op)));
	const revByOp = $derived.by(() => {
		const m = new Map<string, Rev[]>();
		for (const r of revLive) m.set(r.op, [...(m.get(r.op) ?? []), r]);
		return m;
	});
	const revByModel = $derived.by(() => {
		const m = new Map<string, Rev[]>();
		for (const r of revLive) m.set(r.model, [...(m.get(r.model) ?? []), r]);
		return m;
	});

	//: BUILT FRESH EVERY TIME, never handed the artifact's own objects. d3-force
	//: WRITES x/y/vx/vy onto the nodes it is given, so passing `art.nodes` in would
	//: let a grain switch inherit the previous layout and start the simulation from
	//: a shape it should have been free to find.
	//: A REVERSAL IS A CLAIM ABOUT A MODEL, NOT ABOUT A WORD PAIR, so it enters
	//: both grains as a MODEL node -- at word grain that is the only third kind in
	//: the picture, and it is honest for it to look different from the words around
	//: it. Most reversed models already exist because another reading placed them;
	//: on the sexual frame not one of the five does, since every reading that names
	//: them calls them reversed. Those are synthesised, and carry `rev` so the
	//: panel can say they are here for no other reason.
	function withRevs(ns: any[], ls: any[]) {
		if (!showRev) return { nodes: ns, links: ls };
		const at = new Map(ns.map((n) => [n.id, n]));
		for (const r of revLive) {
			const id = 'M::' + r.model;
			if (!at.has(id)) {
				const n = {
					id,
					kind: 'model',
					label: r.model,
					group: null,
					component: null,
					model: r.model,
					rev: true
				};
				at.set(id, n);
				ns.push(n);
			}
			ls.push({ source: id, target: r.op, rev: true });
		}
		return { nodes: ns, links: ls };
	}

	const view = $derived.by(() => {
		if (grain === 'word') {
			const ns = live.map((n) => ({ ...n }));
			const ok = new Set(ns.map((n) => n.id));
			return withRevs(
				ns,
				art.links
					.filter((l) => ok.has(l.source) && ok.has(l.target))
					.map((l) => ({ ...l }))
			);
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
		const seen = new Map<string, number>();
		const ls: any[] = [];
		for (const l of art.links) {
			if (!liveIds.has(l.source) || !liveIds.has(l.target)) continue;
			const s = l.source.startsWith('OP[') ? l.source : 'M::' + l.source.split('::')[0];
			const t = l.target.startsWith('OP[') ? l.target : 'M::' + l.target.split('::')[0];
			const k = s + ' ' + t;
			if (!keep.has(s) || !keep.has(t)) continue;
			//: A COLLAPSED LINK IS CROSSING ONLY IF EVERY WORD LINK UNDER IT IS. One
			//: non-crossing word link means this model really is inside that
			//: component, so the pair must pull like any other.
			const prev = seen.get(k);
			if (prev === undefined) {
				seen.set(k, ls.length);
				ls.push({ source: s, target: t, cross: !!l.cross });
			} else if (!l.cross) {
				ls[prev].cross = false;
			}
		}
		return withRevs([...keep.values()], ls);
	});

	//: CROSSING LINKS ARE DRAWN BUT EXERT NO FORCE. They stay in `data.links` --
	//: LayerChart reads `link.source.x`, so a link forceLink never resolved would
	//: draw from the origin -- and are neutralised with a per-link strength of 0
	//: instead. That is the whole point of k=2: a single model bridging two
	//: operations is not evidence they are one relation, so it must not drag them
	//: into one blob, and it must still be visible where two clusters touch.
	const forces = $derived({
		link: forceLink(view.links)
			.id((d: any) => d.id)
			//: A REV LINK PULLS, WEAKLY, AND THAT IS NOT A CONTRADICTION OF THE ABOVE.
			//: forceLink weights displacement by degree, so a reversed model with one
			//: link moves almost all of the distance and a 30-member hub almost none:
			//: the model parks beside the operation it runs backwards without dragging
			//: the operation anywhere. A cross link joins two HUBS and has no such
			//: asymmetry to protect it, which is why that one stays at zero.
			.strength((l: any) => (l.cross ? 0 : l.rev ? 0.2 : 0.35))
			.distance((l: any) => (l.rev ? 70 : grain === 'word' ? 26 : 60)),
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
	//: PAN, because the weak centring force cannot hold three components inside one
	//: panel without also squashing them together, and the small ones are the ones
	//: k=2 exists to separate. Panning moves the VIEW; the simulation is untouched,
	//: so nothing about the layout depends on where the reader has scrolled to.
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
		//: THE PAN COMES OFF THE POINTER BEFORE THE NODE IS PINNED. `fx`/`fy` are
		//: simulation coordinates and the pointer is in screen ones, so without this
		//: a node jumps by the pan offset the moment it is grabbed.
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
		{#if revs.length}
			<button class="key rev" class:off={!showRev} onclick={() => (showRev = !showRev)}>
				<i></i>{revLive.length} reversed
				<span class="muted">{revByModel.size} models</span>
			</button>
		{/if}
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
				{#key grain + hidden.join() + showRev}
					<ForceSimulation data={view} {forces} cloneNodes={false} alphaDecay={0.02}>
						{#snippet children({ nodes, linkPositions, simulation })}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<svg
								width={w}
								height={H}
								onpointermove={(e) => move(e, simulation)}
								onpointerup={() => up(simulation)}
								onpointerleave={() => up(simulation)}
								class:grabbing={grab}
							>
								<rect
									x="0"
									y="0"
									width={w}
									height={H}
									fill="transparent"
									class="bg"
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
										class:rev={view.links[i]?.rev}
									/>
								{/each}
								{#each nodes as n (n.id)}
									{@const op = n.kind === 'op'}
									<!--
									  ONLY A MODEL NODE CAN BE REVERSED, and `M::` is what makes one. At
									  word grain a reversed model's WORD nodes are present because a
									  DIFFERENT reading placed it forward, so testing the model name
									  alone would paint ~460 words red on the asylum frame and assert
									  the opposite of what the reading says about them.
									-->
									{@const rev = n.id.startsWith('M::') && revByModel.has(n.model ?? '')}
									<!-- svelte-ignore a11y_click_events_have_key_events -->
									<circle
										cx={n.x}
										cy={n.y}
										class:hov={hover === n.id}
										r={op ? Math.min(20, 7 + (n.n ?? 1) * 0.35) : rev ? 6 : grain === 'model' ? 6 : 3}
										fill={op && n.group
											? colour.get(n.group)
											: n.rev
												? '#3a2226'
												: n.component === 0
													? '#8b94a3'
													: '#ffd43b'}
										class:op
										class:revnode={rev}
										class:sel={picked?.id === n.id}
										onpointerdown={(e) => down(e, n, simulation)}
										onpointerenter={() => (hover = n.id)}
										onpointerleave={() => (hover = null)}
										onclick={() => (picked = n)}
									>
										<title
											>{op
												? n.label + ' (' + n.n + ')'
												: rev
													? n.label +
														' - reversed by ' +
														(revByModel.get(n.model ?? '') ?? []).length +
														' reading(s)'
													: n.label}</title
										>
									</circle>
									<!--
									  REVERSED MODELS ARE ALWAYS LABELLED. The hover rule below exists
									  because 55 model labels at once are a smear, but a red dot with no
									  name answers none of the question a reader brings to this layer,
									  which is WHICH model the annotator called backwards. There are 5,
									  2 and 23 of them on the three prompts, and on the one where 23 is
									  the answer the crowding IS the finding.
									-->
									{#if op || rev || hover === n.id || picked?.id === n.id}
										<!--
										  HUBS ALWAYS, MODELS ONLY ON HOVER OR SELECTION. Labelling
										  every model node at 55 nodes produced an unreadable smear
										  exactly where the graph is densest, which is where a reader
										  looks. The panel carries the identity anyway, so the label
										  was redundant as well as illegible.
										-->
										<text
											x={n.x}
											y={n.y - (op ? 15 : 10)}
											class="lab"
											class:oplab={op}
											class:revlab={rev && !op && hover !== n.id && picked?.id !== n.id}
											>{n.label}</text
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
						<code>unassigned</code> carries no words, so a model in that column is absent from this
						graph entirely. <code>reversed</code> is excluded from the COMPONENTS -- it is the same
						operation run backwards, and putting it inside the cluster would average the two
						directions away -- but it is drawn, as a red dashed line to the operation it reverses.
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
				{#if revByOp.get(picked.id)?.length}
					<p class="covh rev">runs it backwards, and is not a member</p>
					<div class="mems">
						{#each revByOp.get(picked.id) ?? [] as r (r.model)}
							<div class="mem rv">
								<b>{r.model}</b>
								<span class="fr">{r.a_words.join(' ') || DASH}</span>
								<span class="to">{r.b_words.join(' ') || DASH}</span>
								<p class="why">{r.how_you_know}</p>
							</div>
						{/each}
					</div>
				{/if}
			{:else}
				{@const who = picked.model ?? picked.label}
				{@const ws = wordsFor(who)}
				<header>
					<strong>{who}</strong>
					<span class="muted"
						>{picked.component == null
							? 'in no component'
							: 'component ' + (picked.component + 1)}</span
					>
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
					{:else}
						<li class="muted">no operation places it; it is here only as a reversal</li>
					{/each}
				</ul>
				{#if revByModel.get(who)?.length}
					<p class="covh rev">
						called REVERSED by {revByModel.get(who)?.length} of {art.meta?.coverage?.length ?? DASH}
						reading(s)
					</p>
					{#each revByModel.get(who) ?? [] as r (r.reading + r.op)}
						<div class="mem rv">
							<b>{r.reading}</b>
							<span class="muted">{r.op.replace(/^OP\[[^\]]*\]\s*/, '')}</span>
							<span class="fr">{r.a_words.join(' ') || DASH}</span>
							<span class="to">{r.b_words.join(' ') || DASH}</span>
							<p class="why">{r.how_you_know}</p>
						</div>
					{/each}
				{/if}
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
		color: var(--text);
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
	/* A BRIDGE THAT WAS NOT COUNTED, DRAWN AS ONE. Dashed and yellow so it reads
	   as an annotation on the gap rather than as structure spanning it. Hiding
	   these would make the picture agree with the component count by concealing
	   exactly the thing the count is a judgement about. */
	.edge.cross {
		stroke: #ffd43b;
		stroke-opacity: 0.55;
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	/* Longer dash and a warmer red than the group palette's #fa5252, so a
	   reversal does not read as membership of the first reading. */
	.edge.rev {
		stroke: #ff6b6b;
		stroke-opacity: 0.85;
		stroke-width: 1.4;
		stroke-dasharray: 6 3;
	}
	circle.revnode {
		stroke: #ff6b6b;
		stroke-width: 1.6;
	}
	text.revlab {
		fill: #ff8787;
		font-size: 0.55rem;
	}
	.key.rev i {
		background: #ff6b6b;
	}
	.covh.rev {
		color: #ff8787;
	}
	.mem.rv {
		border-left: 2px solid #ff6b6b;
		padding-left: 0.4rem;
	}
	.mem.rv .why {
		margin: 0.2rem 0 0;
		font-size: 0.7rem;
		line-height: 1.35;
		color: var(--text-3);
	}
	svg {
		cursor: grab;
		touch-action: none;
	}
	svg.grabbing {
		cursor: grabbing;
	}
	circle {
		cursor: grab;
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
		stroke: var(--text);
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
		fill: var(--text);
		font-weight: 600;
		paint-order: stroke;
		stroke: var(--ground);
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
