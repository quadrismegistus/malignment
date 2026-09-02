<!--
  Sunburst of displacement flow: faller/riser -> source kind -> destination kind.
  Uses d3-hierarchy partition directly in radial coordinates.
-->
<script lang="ts">
	import { hierarchy, partition } from 'd3-hierarchy';
	import { arc as d3Arc } from 'd3-shape';

	let { art: data }: { art: any } = $props();
	let hover = $state<string | null>(null);

	const KINDS: Record<string, string> = {
		SEXUAL: '#c44e52', VIOLENT: '#e15759', DEGRADING: '#f28e2b',
		COERCIVE: '#b07aa1', ILLICIT: '#9c755f', NONE: '#76b7b2', OTHER: '#888'
	};
	const CLS_COL: Record<string, string> = { faller: '#e15759', riser: '#4e79a7' };

	const SIZE = 500;
	const CX = SIZE / 2;

	let tree = $derived.by(() => {
		if (!data?.flows?.length) return null;
		const flows = data.flows as { from: string; to: string; mass: number }[];
		const children = [
			{
				name: 'faller', cls: 'faller',
				children: (() => {
					const byFrom = new Map<string, { name: string; to: string; mass: number }[]>();
					for (const f of flows) {
						if (!byFrom.has(f.from)) byFrom.set(f.from, []);
						byFrom.get(f.from)!.push({ name: f.to, to: f.to, mass: f.mass });
					}
					return [...byFrom.entries()]
						.sort(([a], [b]) => a === 'NONE' ? 1 : b === 'NONE' ? -1 : a.localeCompare(b))
						.map(([k, kids]) => ({
							name: k, kind: k, cls: 'faller',
							children: kids.sort((a, b) => b.mass - a.mass)
								.map((c) => ({ name: `→ ${c.to.toLowerCase()}`, kind: c.to, cls: 'faller', value: c.mass }))
						}));
				})()
			},
			{
				name: 'riser', cls: 'riser',
				children: (() => {
					const byTo = new Map<string, { name: string; from: string; mass: number }[]>();
					for (const f of flows) {
						if (!byTo.has(f.to)) byTo.set(f.to, []);
						byTo.get(f.to)!.push({ name: f.from, from: f.from, mass: f.mass });
					}
					return [...byTo.entries()]
						.sort(([a], [b]) => a === 'NONE' ? 1 : b === 'NONE' ? -1 : a.localeCompare(b))
						.map(([k, kids]) => ({
							name: k, kind: k, cls: 'riser',
							children: kids.sort((a, b) => b.mass - a.mass)
								.map((c) => ({ name: `← ${c.from.toLowerCase()}`, kind: c.from, cls: 'riser', value: c.mass }))
						}));
				})()
			}
		];
		return { name: 'root', children };
	});

	let nodes = $derived.by(() => {
		if (!tree) return [];
		const root = hierarchy(tree).sum((d: any) => d.value ?? 0);
		const p = partition().size([2 * Math.PI, CX - 30]).padding(0.005);
		return p(root).descendants().filter((d) => d.depth > 0);
	});

	const arcGen = d3Arc<any>()
		.startAngle((d) => d.x0)
		.endAngle((d) => d.x1)
		.innerRadius((d) => d.y0)
		.outerRadius((d) => d.y1);

	function nodeColor(d: any): string {
		const dat = d.data;
		if (d.depth === 1) return CLS_COL[dat.cls] ?? '#666';
		return KINDS[dat.kind] ?? '#666';
	}

	function nodeKey(d: any): string {
		if (d.depth === 1) return d.data.cls;
		if (d.depth === 2) return d.data.kind;
		return d.data.kind + '_' + d.data.cls;
	}

	function isHl(d: any): boolean {
		if (!hover) return true;
		if (d.depth === 2 && d.data.kind === hover) return true;
		if (d.depth === 3 && d.data.kind === hover) return true;
		if (d.depth === 1 && d.data.cls === hover) return true;
		return false;
	}

	let within = $derived(data?.flows?.filter((f: any) => f.from === f.to).reduce((s: number, f: any) => s + f.mass, 0) ?? 0);
	let cross = $derived(data?.flows?.filter((f: any) => f.from !== f.to).reduce((s: number, f: any) => s + f.mass, 0) ?? 0);
	let withinPct = $derived(within + cross > 0 ? Math.round(100 * within / (within + cross)) : 0);
</script>

{#if nodes.length}
	<svg viewBox="0 0 {SIZE} {SIZE}" style="width:100%;max-width:520px;display:block;margin:8px auto">
		<g transform="translate({CX},{CX})">
			{#each nodes as node}
				{@const col = nodeColor(node)}
				<path d={arcGen(node)} fill={col}
					opacity={isHl(node) ? (node.depth === 1 ? 0.7 : 0.85) : 0.1}
					stroke="#1a1a2e" stroke-width="0.5"
					onmouseenter={() => {
						if (node.depth >= 2) hover = node.data.kind;
						else hover = node.data.cls;
					}}
					onmouseleave={() => hover = null}
					style="cursor:default" />
			{/each}
			{#each nodes.filter((n) => n.depth <= 2 && n.x1 - n.x0 > 0.08) as node}
				{@const angle = (node.x0 + node.x1) / 2}
				{@const radius = (node.y0 + node.y1) / 2}
				{@const flip = angle > Math.PI}
				<text
					transform="rotate({angle * 180 / Math.PI - 90}) translate({radius},0){flip ? ' rotate(180)' : ''}"
					text-anchor={flip ? 'end' : 'start'}
					font-size={node.depth === 1 ? '11' : '9'}
					fill={nodeColor(node)}
					opacity={isHl(node) ? 1 : 0.25}
					dominant-baseline="middle"
					style="pointer-events:none">
					{node.data.name.toLowerCase()}
				</text>
			{/each}
		</g>
	</svg>

	<p class="muted small" style="margin:0 0 4px;font-size:11px;text-align:center">
		inner ring: <span style="color:{CLS_COL.faller}">faller</span> / <span style="color:{CLS_COL.riser}">riser</span>
		· middle: source kind · outer: destination kind
		· within-kind {withinPct}% · {data.n_lineages} lineages, {data.n_cells?.toLocaleString()} cells
	</p>

	{#if data.flows?.length}
		<details style="margin:8px 0">
			<summary class="muted small">flow table (top 20)</summary>
			<table style="font-size:11px;margin:4px 0">
				<thead><tr><th>faller kind</th><th>riser kind</th><th style="text-align:right">mass</th><th style="text-align:right">%</th></tr></thead>
				<tbody>
					{#each data.flows.slice(0, 20) as f}
						{@const total = within + cross}
						<tr style="opacity:{f.from === f.to ? 1 : 0.7}">
							<td style="color:{KINDS[f.from] ?? '#888'}">{f.from.toLowerCase()}</td>
							<td style="color:{KINDS[f.to] ?? '#888'}">{f.to.toLowerCase()}</td>
							<td style="text-align:right">{f.mass.toFixed(1)}</td>
							<td style="text-align:right">{total > 0 ? (100 * f.mass / total).toFixed(1) : '—'}%</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</details>
	{/if}

	{#if data.examples?.length}
		<h3 style="margin-top:24px">examples <span class="muted" style="font-weight:normal;font-size:12px">top movers in one cell per domain</span></h3>
		{#each data.examples as ex}
			{@const words = [...ex.words].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)).slice(0, 20)}
			{@const maxP = Math.max(...words.flatMap((w) => [w.p_base, w.p_aligned]), 0.001)}
			{@const eW = 500}
			{@const rowH = 15}
			{@const labelW = 76}
			{@const eH = words.length * rowH + 24}
			{@const ex_x = (v) => labelW + (v / maxP) * (eW - labelW - 10)}
			<p style="margin:12px 0 2px;font-size:12px">
				<span style="color:{KINDS[ex.label] ?? '#ccc'};font-weight:600">{ex.label.toLowerCase()}</span>
				<span class="muted"> {ex.prompt.slice(0, 55)}{ex.prompt.length > 55 ? '...' : ''} · {ex.base.split('/').pop()} → {ex.aligned.split('/').pop()} · {words.length} of {ex.n_words} words</span>
			</p>
			<svg viewBox="0 0 {eW} {eH}" style="width:100%;max-width:600px;display:block;margin:0 0 4px">
				<defs>
					<marker id="ex-arr-r-{ex.label}" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#4e79a7"/></marker>
					<marker id="ex-arr-l-{ex.label}" viewBox="0 0 6 6" refX="1" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M6,0 L0,3 L6,6 Z" fill="#e15759"/></marker>
				</defs>
				{#each words as w, i}
					{@const y = i * rowH + 6}
					{@const col = KINDS[w.kind] ?? '#888'}
					{@const falling = w.delta < 0}
					<text x={labelW - 4} y={y + 4} text-anchor="end" font-size="8" font-family="var(--mono)"
						fill={col}
						opacity={hover === w.word ? 1 : 0.85}
						onmouseenter={() => hover = w.word}
						onmouseleave={() => hover = null}
						style="cursor:default">{w.word}</text>
					<line
						x1={ex_x(Math.min(w.p_base, w.p_aligned))}
						y1={y} x2={ex_x(Math.max(w.p_base, w.p_aligned))} y2={y}
						stroke={falling ? '#e15759' : '#4e79a7'}
						stroke-width={hover === w.word ? 2.5 : 1.5}
						opacity={hover === w.word ? 1 : 0.6}
						marker-end={falling ? '' : 'url(#ex-arr-r-{ex.label})'}
						marker-start={falling ? 'url(#ex-arr-l-{ex.label})' : ''}
						onmouseenter={() => hover = w.word}
						onmouseleave={() => hover = null}
						style="cursor:default" />
					<circle cx={ex_x(w.p_base)} cy={y} r="1.5" fill="#888" opacity="0.5" />
					<circle cx={ex_x(w.p_aligned)} cy={y} r="1.5" fill={falling ? '#e15759' : '#4e79a7'} opacity="0.7" />
					{#if hover === w.word}
						<text x={ex_x(Math.max(w.p_base, w.p_aligned)) + 5} y={y + 3} font-size="7" fill="#ccc">
							{w.p_base.toFixed(4)}→{w.p_aligned.toFixed(4)} {(w.kind ?? '').toLowerCase()}
						</text>
					{/if}
				{/each}
				{#each [0, maxP / 2, maxP] as tick}
					<text x={ex_x(tick)} y={eH - 4} text-anchor="middle" font-size="7" fill="#666">{tick.toFixed(3)}</text>
				{/each}
			</svg>
		{/each}
		<p class="muted small" style="margin:4px 0">grey dot = base · arrow tip = aligned · <span style="color:#e15759">red</span> = falling · <span style="color:#4e79a7">blue</span> = rising · word color = kind</p>
	{/if}
{:else}
	<p class="muted">No flow data.</p>
{/if}
