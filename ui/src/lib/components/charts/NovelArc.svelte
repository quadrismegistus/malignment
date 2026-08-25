<!--
  Alignment on the literary-history timeline: abstraction and interiority.
  Two panels. Historical series as a line; model arms as horizontal markers.
-->
<script lang="ts">
	import { LineChart } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type HistRow = { year: number; value: number; n: number; source: string };
	type ModelRow = { category: string; value: number; n: number };
	type Anchor = { category: string; abs: number; int: number | null; n: number };

	const PANELS: { key: string; label: string; yLabel: string; flip: boolean }[] = [
		{ key: 'abstraction', label: 'Abstraction (concreteness axis)', yLabel: 'high = concrete, low = abstract', flip: false },
		{ key: 'interiority', label: 'Interiority (usas_x)', yLabel: 'higher = more interior', flip: false },
	];

	const MODEL_COLOURS: Record<string, string> = {
		base: '#4e79a7', aligned: '#e15759', API: '#f28e2b'
	};
	const SOURCE_COLOURS: Record<string, string> = {
		chadwyck: '#555', chicago: '#888'
	};
	const ANCHOR_COLOUR = '#bbb';

	function hist(key: string): HistRow[] {
		return (art[key]?.history ?? []).sort((a: HistRow, b: HistRow) => a.year - b.year);
	}
	function models(key: string): ModelRow[] {
		return art[key]?.models ?? [];
	}
	let anchors: Anchor[] = $derived(art.anchors ?? []);

	function xDomain(key: string): [number, number] {
		const h = hist(key);
		if (!h.length) return [1600, 2000];
		return [Math.min(...h.map((r: HistRow) => r.year)) - 10,
		        Math.max(...h.map((r: HistRow) => r.year)) + 40];
	}
	function yDomain(key: string): [number, number] {
		const h = hist(key);
		const m = models(key);
		const all = [...h.map((r: HistRow) => r.value), ...m.map((r: ModelRow) => r.value)];
		if (!all.length) return [0, 1];
		const lo = Math.min(...all);
		const hi = Math.max(...all);
		const pad = (hi - lo) * 0.12 || 0.05;
		return [lo - pad, hi + pad];
	}

	let hover = $state<{ panel: string; label: string; value: number; year?: number } | null>(null);
</script>

<figure class="novel-arc">
	<figcaption>
		<h3>{art.title ?? 'Novel arc'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="panels">
		{#each PANELS as panel}
			{@const h = hist(panel.key)}
			{@const m = models(panel.key)}
			{@const xd = xDomain(panel.key)}
			{@const yd = yDomain(panel.key)}
			{@const sources = [...new Set(h.map((r) => r.source))]}
			{#if h.length > 0}
				<div class="panel">
					<div class="panel-label">{panel.label}</div>
					<div class="chart-area" onmouseleave={() => { if (hover?.panel === panel.key) hover = null; }}>
						<LineChart
							data={[]}
							x="year" y="value"
							xScale={scaleLinear()}
							xDomain={xd} yDomain={yd}
							padding={{ left: 44, bottom: 32, top: 12, right: 80 }}
							axis={{ x: { format: (d: number) => String(Math.round(d)) },
									y: { format: (d: number) => d.toFixed(2) } }}
							grid={{ x: false, y: true }}
							rule={false}
							series={sources.map((s) => ({
								key: s, color: SOURCE_COLOURS[s] ?? '#888',
								data: h.filter((r) => r.source === s)
							}))}
							props={{ spline: { strokeWidth: 0 }, xAxis: { rule: false }, yAxis: { rule: false } }}
						>
							{#snippet marks({ context }: { context: any })}
								<!-- historical lines -->
								{#each sources as src}
									{@const sd = h.filter((r) => r.source === src).sort((a, b) => a.year - b.year)}
									{#if sd.length > 1}
										<polyline
											points={sd.map((r) => `${context.xScale(r.year)},${context.yScale(r.value)}`).join(' ')}
											fill="none" stroke={SOURCE_COLOURS[src] ?? '#888'}
											stroke-width="2"
										/>
										{#each sd as r}
											<circle cx={context.xScale(r.year)} cy={context.yScale(r.value)}
												r="2.5" fill={SOURCE_COLOURS[src] ?? '#888'} opacity="0.6"
												onmouseenter={() => hover = { panel: panel.key, label: `${src} ${r.year}`, value: r.value, year: r.year }}
											/>
										{/each}
									{/if}
								{/each}

								<!-- model arm markers as horizontal lines spanning right margin -->
								{#each m as mr}
									{@const y = context.yScale(mr.value)}
									{@const x1 = context.xScale(xd[1] - 30)}
									{@const x2 = context.xScale(xd[1])}
									<line {x1} {x2} y1={y} y2={y}
										stroke={MODEL_COLOURS[mr.category] ?? '#888'}
										stroke-width="3" stroke-dasharray="6 3"
									/>
									<text x={x2 + 4} y={y + 4} font-size="10" font-weight="600"
										fill={MODEL_COLOURS[mr.category] ?? '#888'}
									>{mr.category}</text>
									<!-- invisible hover target -->
									<rect x={x1} y={y - 8} width={x2 - x1 + 60} height="16"
										fill="transparent"
										onmouseenter={() => hover = { panel: panel.key, label: mr.category, value: mr.value }}
									/>
								{/each}

								<!-- anchor markers (faint) on abstraction panel -->
								{#if panel.key === 'abstraction'}
									{#each anchors as a}
										{@const y = context.yScale(a.abs)}
										<line x1={context.xScale(xd[1] - 20)} x2={context.xScale(xd[1] - 5)}
											y1={y} y2={y}
											stroke={ANCHOR_COLOUR} stroke-width="1" stroke-dasharray="2 2"
										/>
										<text x={context.xScale(xd[1] - 3)} y={y + 3} font-size="7"
											fill={ANCHOR_COLOUR}
										>{a.category.replace(/_/g, ' ')}</text>
									{/each}
								{/if}

								<!-- hover indicator -->
								{#if hover && hover.panel === panel.key}
									<text x={context.xScale(xd[0]) + 4} y={context.yScale(yd[1]) + 14}
										font-size="10" fill="var(--text-2, #666)"
									>{hover.label}: {hover.value.toFixed(4)}</text>
								{/if}
							{/snippet}
						</LineChart>
					</div>
				</div>
			{/if}
		{/each}
	</div>

	<div class="legend">
		{#each Object.entries(SOURCE_COLOURS) as [k, c]}
			<span class="leg"><i style:background={c}></i>{k}</span>
		{/each}
		{#each Object.entries(MODEL_COLOURS) as [k, c]}
			<span class="leg"><i style:background={c} style:height="3px"></i>{k} (model)</span>
		{/each}
	</div>
</figure>

<style>
	.novel-arc { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub { margin: 0 0 0.6rem; font-size: 0.8rem; color: var(--text-3); max-width: 100ch; }
	.panels {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	@media (max-width: 800px) { .panels { grid-template-columns: 1fr; } }
	.panel { min-width: 0; }
	.panel-label {
		text-align: center; font-size: 0.8rem; font-weight: 600;
		color: var(--text-2); padding: 2px 0;
	}
	.chart-area { height: 320px; position: relative; }
	.chart-area :global(.tick text) { font-size: 9px; fill: var(--text-3); }
	.legend {
		display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem;
		margin-top: 0.6rem; font-size: 0.75rem; color: var(--text-3);
	}
	.leg { display: flex; align-items: center; gap: 4px; }
	.leg i { display: inline-block; width: 16px; height: 2px; border-radius: 1px; }
</style>
