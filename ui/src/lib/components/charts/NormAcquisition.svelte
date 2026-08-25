<!--
  K-scale norm composition across the training ladder.
  Small multiples, one panel per scale, with phase bands.
  Tab per ladder. Same smoothing convention as CapacityCurves.
-->
<script lang="ts">
	import { LineChart } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type Row = { ladder: string; ckpt_idx: number; scale: string;
	             value: number; smooth: number; role: string; seg: string };

	let rows: Row[] = $derived(art.rows ?? []);
	let scales: string[] = $derived(art.scales ?? []);
	let colours: Record<string, string> = $derived(art.colours ?? {});
	let boundaries: Record<string, Record<string, [number, number]>> = $derived(art.boundaries ?? {});
	let ladders: string[] = $derived(art.ladders ?? []);

	let activeLadder = $state('olmo');

	function scaleRows(ladder: string, scale: string): Row[] {
		return rows.filter((r) => r.ladder === ladder && r.scale === scale)
			.sort((a, b) => a.ckpt_idx - b.ckpt_idx);
	}

	let xd = $derived.by(() => {
		const xs = rows.filter((r) => r.ladder === activeLadder).map((r) => r.ckpt_idx);
		if (!xs.length) return [0, 100] as [number, number];
		return [Math.min(...xs), Math.max(...xs)] as [number, number];
	});

	function yDomain(scale: string): [number, number] {
		const vs = scaleRows(activeLadder, scale).map((r) => r.value);
		if (!vs.length) return [0, 1];
		const lo = Math.min(...vs);
		const hi = Math.max(...vs);
		const pad = (hi - lo) * 0.15 || 0.01;
		return [lo - pad, hi + pad];
	}

	let bounds = $derived(boundaries[activeLadder] ?? {});

	const PHASE_COLOURS: Record<string, string> = {
		SFT: 'rgba(200, 190, 160, 0.3)',
		DPO: 'rgba(180, 170, 140, 0.4)',
		RLVR: 'rgba(200, 190, 160, 0.3)'
	};

	let hover = $state<{ scale: string; row: Row } | null>(null);
</script>

<figure class="norm-acq">
	<figcaption>
		<h3>{art.title ?? 'Norm acquisition'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="tabs">
		{#each ladders as ladder}
			<button class:active={activeLadder === ladder} onclick={() => { activeLadder = ladder; hover = null; }}>
				{ladder === 'olmo' ? 'OLMo-3' : 'Pythia-6.9b'}
			</button>
		{/each}
	</div>

	<div class="grid">
		{#each scales as scale}
			{@const sd = scaleRows(activeLadder, scale)}
			{@const yd = yDomain(scale)}
			{@const segs = [...new Set(sd.map((r) => r.seg))]}
			{#if sd.length > 0}
				<div class="panel">
					<div class="panel-label" style:color={colours[scale] ?? '#888'}>{scale}</div>
					<div class="chart-area" onmouseleave={() => { if (hover?.scale === scale) hover = null; }}>
						<LineChart
							data={[]}
							x="ckpt_idx" y="value"
							xScale={scaleLinear()}
							xDomain={xd} yDomain={yd}
							padding={{ left: 36, bottom: 20, top: 6, right: 8 }}
							axis={{ x: { format: (d: number) => String(Math.round(d)) },
									y: { format: (d: number) => d.toFixed(2), ticks: 3 } }}
							grid={{ x: false, y: true }}
							rule={false}
							series={[{ key: scale, color: colours[scale] ?? '#888', data: sd }]}
							props={{ spline: { strokeWidth: 0 }, xAxis: { rule: false }, yAxis: { rule: false } }}
						>
							{#snippet marks({ context }: { context: any })}
								<!-- phase bands -->
								{#each Object.entries(bounds) as [phase, [lo, hi]]}
									{#if PHASE_COLOURS[phase]}
										<rect
											x={context.xScale(lo - 0.5)}
											y={context.yScale(yd[1])}
											width={context.xScale(hi + 0.5) - context.xScale(lo - 0.5)}
											height={context.yScale(yd[0]) - context.yScale(yd[1])}
											fill={PHASE_COLOURS[phase]}
										/>
										<text
											x={(context.xScale(lo) + context.xScale(hi)) / 2}
											y={context.yScale(yd[1]) + 10}
											text-anchor="middle" font-size="8" fill="#888"
										>{phase}</text>
									{/if}
								{/each}
								<!-- raw line -->
								{#if sd.length > 1}
									<polyline
										points={sd.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.value)}`).join(' ')}
										fill="none" stroke={colours[scale] ?? '#888'}
										stroke-width="0.8" opacity="0.25"
									/>
								{/if}
								<!-- smoothed per segment -->
								{#each segs as seg}
									{@const sr = sd.filter((r) => r.seg === seg)}
									{#if sr.length > 1}
										<polyline
											points={sr.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.smooth)}`).join(' ')}
											fill="none" stroke={colours[scale] ?? '#888'} stroke-width="2"
										/>
									{:else if sr.length === 1}
										<circle cx={context.xScale(sr[0].ckpt_idx)} cy={context.yScale(sr[0].smooth)}
											r="3" fill={colours[scale] ?? '#888'} />
									{/if}
								{/each}
								<!-- hover target -->
								{#if sd.length > 1}
									<polyline
										points={sd.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.smooth)}`).join(' ')}
										fill="none" stroke="transparent" stroke-width="14"
										onmousemove={(e: MouseEvent) => {
											const svg = (e.target as SVGElement).closest('svg');
											if (!svg) return;
											const pt = svg.createSVGPoint();
											pt.x = e.clientX; pt.y = e.clientY;
											const svgPt = pt.matrixTransform(svg.getScreenCTM()?.inverse());
											const mouseX = context.xScale.invert(svgPt.x);
											let closest = sd[0];
											let minDist = Infinity;
											for (const r of sd) {
												const d = Math.abs(r.ckpt_idx - mouseX);
												if (d < minDist) { minDist = d; closest = r; }
											}
											hover = { scale, row: closest };
										}}
									/>
								{/if}
								{#if hover && hover.scale === scale}
									<circle
										cx={context.xScale(hover.row.ckpt_idx)}
										cy={context.yScale(hover.row.smooth)}
										r="4" fill={colours[scale] ?? '#888'}
										stroke="#fff" stroke-width="1.5"
										style="pointer-events: none"
									/>
								{/if}
							{/snippet}
						</LineChart>
						{#if hover && hover.scale === scale}
							<div class="tip">
								<strong style:color={colours[scale]}>{scale}</strong>
								<div class="tip-row">checkpoint {hover.row.ckpt_idx} ({hover.row.role})</div>
								<div class="tip-row">raw: {hover.row.value.toFixed(4)}</div>
								<div class="tip-row">smooth: {hover.row.smooth.toFixed(4)}</div>
							</div>
						{/if}
					</div>
				</div>
			{/if}
		{/each}
	</div>
</figure>

<style>
	.norm-acq { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub { margin: 0 0 0.6rem; font-size: 0.8rem; color: var(--text-3); max-width: 100ch; }
	.tabs { display: flex; gap: 2px; margin-bottom: 0.6rem; }
	.tabs button {
		background: var(--panel-2, #eee); border: 1px solid var(--rule, #ddd);
		border-radius: 4px 4px 0 0; padding: 4px 14px; cursor: pointer;
		font-size: 0.8rem; color: var(--text-3);
	}
	.tabs button.active {
		background: var(--panel, #fff); border-bottom-color: transparent;
		color: var(--text); font-weight: 600;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.5rem;
	}
	.panel { min-width: 0; }
	.panel-label {
		text-align: center; font-size: 0.75rem; font-weight: 700;
		padding: 2px 0;
	}
	.chart-area { height: 160px; position: relative; }
	.chart-area :global(.tick text) { font-size: 8px; fill: var(--text-3); }
	.tip {
		position: absolute; bottom: 24px; left: 40px;
		background: var(--panel, #fff); border: 1px solid var(--rule, #ddd);
		border-radius: 5px; padding: 4px 8px; font-size: 0.68rem;
		box-shadow: 0 2px 6px rgba(0,0,0,0.1); pointer-events: none; z-index: 10;
	}
	.tip-row { color: var(--text-2, #666); line-height: 1.4; }
</style>
