<!--
  Dose-response scatter: x = base-arm transgressiveness, y = delta on each scale.
  Small multiples, one panel per scale. Cloud of sampled cells + binned mean trend.
-->
<script lang="ts">
	import { ScatterChart, Tooltip } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type SampleRow = { dose: number; delta: number; scale: string };
	type BinnedRow = { dose: number; delta: number; se: number; n: number; scale: string };

	let scales: string[] = $derived(art.scales ?? []);
	let sample: SampleRow[] = $derived(art.sample ?? []);
	let binned: BinnedRow[] = $derived(art.binned ?? []);

	function panelData(scale: string) {
		return sample.filter((r: SampleRow) => r.scale === scale);
	}
	function trendData(scale: string) {
		return binned
			.filter((r: BinnedRow) => r.scale === scale)
			.sort((a: BinnedRow, b: BinnedRow) => a.dose - b.dose);
	}

	let xDomain = $derived.by(() => {
		if (!sample.length) return [0, 1];
		const xs = sample.map((r: SampleRow) => r.dose);
		return [Math.min(...xs), Math.max(...xs)];
	});
</script>

{#if art.title}
	<h3 class="title">{art.title}</h3>
{/if}
{#if art.subtitle}
	<p class="subtitle">{art.subtitle}</p>
{/if}

<div class="grid" style="--cols: {Math.min(scales.length, 4)}">
	{#each scales as scale}
		{@const pts = panelData(scale)}
		{@const trend = trendData(scale)}
		{@const ys = pts.map((r: SampleRow) => r.delta)}
		{@const yLo = Math.min(...ys, 0)}
		{@const yHi = Math.max(...ys, 0)}
		{@const yPad = (yHi - yLo) * 0.1 || 0.01}
		<div class="panel">
			<div class="panel-label">{scale}</div>
			<div class="chart-wrap">
				<ScatterChart
					data={pts}
					x="dose"
					y="delta"
					xScale={scaleLinear().domain(xDomain)}
					yScale={scaleLinear().domain([yLo - yPad, yHi + yPad])}
					series={[
						{
							data: pts,
							props: { r: 2, fill: '#4e79a7', opacity: 0.25, stroke: 'none' }
						}
					]}
					padding={{ top: 4, bottom: 24, left: 36, right: 8 }}
					grid={{ x: false, y: true }}
					axis={{ x: { label: '' }, y: { label: '' } }}
				>
					<!-- zero line -->
					{#snippet children({ xScale: xs, yScale: ysf })}
						{@const zeroY = ysf(0)}
						<line
							x1={xs(xDomain[0])}
							x2={xs(xDomain[1])}
							y1={zeroY}
							y2={zeroY}
							stroke="#aaa"
							stroke-dasharray="4 3"
							stroke-width="0.8"
						/>
						<!-- trend line -->
						{#if trend.length > 1}
							<polyline
								points={trend.map((t: BinnedRow) => `${xs(t.dose)},${ysf(t.delta)}`).join(' ')}
								fill="none"
								stroke="#e15759"
								stroke-width="2"
							/>
							{#each trend as t}
								<line
									x1={xs(t.dose)}
									x2={xs(t.dose)}
									y1={ysf(t.delta - t.se)}
									y2={ysf(t.delta + t.se)}
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

<style>
	.title {
		margin: 0 0 4px;
		font-size: 14px;
		font-weight: 600;
	}
	.subtitle {
		margin: 0 0 12px;
		font-size: 11px;
		color: var(--text-3, #888);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(var(--cols, 4), 1fr);
		gap: 8px;
	}
	.panel {
		border: 1px solid var(--rule, #e0e0e0);
		border-radius: 6px;
		padding: 6px 4px 0;
		background: var(--panel, #fafafa);
	}
	.panel-label {
		text-align: center;
		font-size: 11px;
		font-weight: 600;
		color: var(--text-2, #555);
		margin-bottom: 2px;
	}
	.chart-wrap {
		height: 180px;
	}
</style>
