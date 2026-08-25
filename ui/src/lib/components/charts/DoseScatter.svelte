<!--
  Dose-response scatter: x = base-arm transgressiveness, y = delta on each scale.
  Small multiples via CSS grid, same pattern as SlopeGrid.
-->
<script lang="ts">
	import { ScatterChart, Tooltip } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	type SampleRow = { dose: number; delta: number; scale: string };
	type BinnedRow = { dose: number; delta: number; se: number; n: number; scale: string };

	let { art }: { art: any } = $props();

	let scales: string[] = $derived(art.scales ?? []);
	let sample: SampleRow[] = $derived(art.sample ?? []);
	let binned: BinnedRow[] = $derived(art.binned ?? []);

	function panelData(scale: string): SampleRow[] {
		return sample.filter((r) => r.scale === scale);
	}
	function trendData(scale: string): BinnedRow[] {
		return binned.filter((r) => r.scale === scale).sort((a, b) => a.dose - b.dose);
	}

	let xDomain = $derived.by(() => {
		if (!sample.length) return [0, 1] as [number, number];
		const xs = sample.map((r) => r.dose);
		return [Math.min(...xs), Math.max(...xs)] as [number, number];
	});

	function yDomain(pts: SampleRow[]): [number, number] {
		if (!pts.length) return [-0.1, 0.1];
		const ys = pts.map((r) => r.delta);
		const lo = Math.min(...ys, 0);
		const hi = Math.max(...ys, 0);
		const pad = (hi - lo) * 0.12 || 0.02;
		return [lo - pad, hi + pad];
	}
</script>

<figure class="dose-scatter">
	<figcaption>
		<h3>{art.title ?? 'Dose-response'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="grid">
		{#each scales as scale}
			{@const pts = panelData(scale)}
			{@const trend = trendData(scale)}
			{@const yDom = yDomain(pts)}
			<div class="panel">
				<div class="head">{scale}</div>
				<div class="chart">
					<ScatterChart
						data={pts}
						x="dose"
						y="delta"
						xScale={scaleLinear()}
						xDomain={xDomain}
						yDomain={yDom}
						padding={{ left: 32, bottom: 24, top: 6, right: 8 }}
						axis={{ x: { format: (d: number) => d.toFixed(1) },
								y: { format: (d: number) => d.toFixed(2) } }}
						grid={{ x: false, y: true }}
						rule={{ x: false, y: 0 }}
						props={{
							points: { r: 1.8, fill: '#4e79a7', opacity: 0.22, stroke: 'none' },
							yAxis: { rule: false }
						}}
					>
						{#snippet marks({ context }: { context: any })}
							<!-- default points -->
							{#each pts as p}
								<circle
									cx={context.xScale(p.dose)}
									cy={context.yScale(p.delta)}
									r="1.8"
									fill="#4e79a7"
									opacity="0.22"
								/>
							{/each}
							<!-- trend line -->
							{#if trend.length > 1}
								<polyline
									points={trend
										.map((t) => `${context.xScale(t.dose)},${context.yScale(t.delta)}`)
										.join(' ')}
									fill="none"
									stroke="#e15759"
									stroke-width="2"
								/>
								{#each trend as t}
									<line
										x1={context.xScale(t.dose)}
										x2={context.xScale(t.dose)}
										y1={context.yScale(t.delta - t.se)}
										y2={context.yScale(t.delta + t.se)}
										stroke="#e15759"
										stroke-width="1"
										opacity="0.5"
									/>
								{/each}
							{/if}
						{/snippet}
					</ScatterChart>
				</div>
			</div>
		{/each}
	</div>
</figure>

<style>
	.dose-scatter { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub {
		margin: 0 0 0.9rem; font-size: 0.85rem;
		color: var(--text-3); max-width: 90ch;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 0.5rem 0.6rem;
	}
	.panel { min-width: 0; }
	.head {
		font-size: 0.75rem; font-weight: 600;
		color: var(--text-2); text-align: center;
		padding: 2px 0;
	}
	.chart { height: 180px; }
	.chart :global(.tick text) {
		font-size: 9px; fill: var(--text-3);
	}
</style>
