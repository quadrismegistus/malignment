<!--
  All capacities across the training ladder: one line per family,
  raw + smoothed, with phase boundaries marked.
  Tab per ladder (OLMo / Pythia).
-->
<script lang="ts">
	import { LineChart } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type Row = { ladder: string; ckpt_idx: number; family: string;
	             value: number; smooth: number; role: string; seg: string };

	let rows: Row[] = $derived(art.rows ?? []);
	let families: string[] = $derived(art.families ?? []);
	let colours: Record<string, string> = $derived(art.colours ?? {});
	let boundaries: Record<string, Record<string, [number, number]>> = $derived(art.boundaries ?? {});
	let ladders: string[] = $derived(art.ladders ?? []);

	let activeLadder = $state('olmo');

	function ladderRows(ladder: string): Row[] {
		return rows.filter((r) => r.ladder === ladder);
	}

	function familySmooth(ladder: string, fam: string): Row[] {
		return rows
			.filter((r) => r.ladder === ladder && r.family === fam)
			.sort((a, b) => a.ckpt_idx - b.ckpt_idx);
	}

	let xd = $derived.by(() => {
		const xs = ladderRows(activeLadder).map((r) => r.ckpt_idx);
		if (!xs.length) return [0, 100] as [number, number];
		return [Math.min(...xs), Math.max(...xs)] as [number, number];
	});

	let yd = $derived.by(() => {
		const vs = ladderRows(activeLadder).map((r) => r.value);
		if (!vs.length) return [0, 1] as [number, number];
		return [-0.02, Math.max(...vs) + 0.05] as [number, number];
	});

	let bounds = $derived(boundaries[activeLadder] ?? {});

	const PHASE_COLOURS: Record<string, string> = {
		SFT: 'rgba(200, 190, 160, 0.3)',
		DPO: 'rgba(180, 170, 140, 0.4)',
		RLVR: 'rgba(200, 190, 160, 0.3)'
	};

	let hover = $state<{ family: string; row: Row } | null>(null);
</script>

<figure class="cap-curves">
	<figcaption>
		<h3>{art.title ?? 'Capacity curves'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="tabs">
		{#each ladders as ladder}
			<button class:active={activeLadder === ladder} onclick={() => { activeLadder = ladder; hover = null; }}>
				{ladder === 'olmo' ? 'OLMo-3' : 'Pythia-6.9b'}
			</button>
		{/each}
	</div>

	<div class="chart-area" onmouseleave={() => hover = null}>
		<LineChart
			data={[]}
			x="ckpt_idx" y="value"
			xScale={scaleLinear()}
			xDomain={xd} yDomain={yd}
			padding={{ left: 40, bottom: 32, top: 12, right: 140 }}
			axis={{ x: { label: 'training position (ordinal)',
						 format: (d: number) => String(Math.round(d)) },
					y: { format: (d: number) => d.toFixed(1) } }}
			grid={{ x: false, y: true }}
			rule={false}
			series={families.map((f) => ({
				key: f, color: colours[f] ?? '#888',
				data: familySmooth(activeLadder, f)
			}))}
			props={{
				spline: { strokeWidth: 0 },
				xAxis: { rule: false },
				yAxis: { rule: false }
			}}
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
							y={context.yScale(yd[1]) + 12}
							text-anchor="middle"
							font-size="10" fill="#888" font-weight="600"
						>{phase}</text>
					{/if}
				{/each}

				<!-- raw lines (faint) -->
				{#each families as fam}
					{@const sd = familySmooth(activeLadder, fam)}
					{#if sd.length > 1}
						<polyline
							points={sd.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.value)}`).join(' ')}
							fill="none" stroke={colours[fam] ?? '#888'}
							stroke-width="0.8" opacity="0.2"
						/>
					{/if}
				{/each}

				<!-- smoothed lines (bold), per segment -->
				{#each families as fam}
					{@const sd = familySmooth(activeLadder, fam)}
					{@const segs = [...new Set(sd.map((r) => r.seg))]}
					{#each segs as seg}
						{@const sr = sd.filter((r) => r.seg === seg)}
						{#if sr.length > 1}
							<polyline
								points={sr.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.smooth)}`).join(' ')}
								fill="none" stroke={colours[fam] ?? '#888'}
								stroke-width="2.5"
								opacity={hover && hover.family !== fam ? 0.15 : 1}
								style="pointer-events: none"
							/>
						{:else if sr.length === 1}
							<circle
								cx={context.xScale(sr[0].ckpt_idx)}
								cy={context.yScale(sr[0].smooth)}
								r="3" fill={colours[fam] ?? '#888'}
								opacity={hover && hover.family !== fam ? 0.15 : 1}
							/>
						{/if}
					{/each}
					<!-- fat hover target -->
					{#if sd.length > 1}
						<polyline
							points={sd.map((r) => `${context.xScale(r.ckpt_idx)},${context.yScale(r.smooth)}`).join(' ')}
							fill="none" stroke="transparent" stroke-width="14"
							onmouseenter={() => hover = { family: fam, row: sd[sd.length - 1] }}
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
								hover = { family: fam, row: closest };
							}}
						/>
					{/if}
				{/each}

				<!-- right-edge labels -->
				{@const xMax = xd[1]}
				{@const labelX = context.xScale(xMax) + 6}
				{@const lastValues = families.map((f) => {
					const sd = familySmooth(activeLadder, f);
					return { fam: f, y: sd.length ? sd[sd.length - 1].smooth : 0 };
				}).sort((a, b) => b.y - a.y)}
				{#each lastValues as { fam, y }, i}
					{@const repelY = (() => {
						const gap = 13;
						let py = context.yScale(y);
						for (let j = 0; j < i; j++) {
							const prev = context.yScale(lastValues[j].y);
							if (Math.abs(py - prev) < gap) py = prev + gap;
						}
						return py;
					})()}
					<text
						x={labelX} y={repelY + 4}
						font-size="9" font-weight="600"
						fill={colours[fam] ?? '#888'}
						opacity={hover && hover.family !== fam ? 0.2 : 1}
					>{fam}</text>
				{/each}

				<!-- hover dot -->
				{#if hover}
					<circle
						cx={context.xScale(hover.row.ckpt_idx)}
						cy={context.yScale(hover.row.smooth)}
						r="5" fill={colours[hover.family] ?? '#888'}
						stroke="#fff" stroke-width="1.5"
						style="pointer-events: none"
					/>
				{/if}
			{/snippet}
		</LineChart>

		<!-- tooltip -->
		{#if hover}
			<div class="tip">
				<div class="tip-head">
					<span class="tip-swatch" style:background={colours[hover.family] ?? '#888'}></span>
					<strong>{hover.family}</strong>
				</div>
				<div class="tip-row">checkpoint: {hover.row.ckpt_idx} ({hover.row.role})</div>
				<div class="tip-row">raw: {hover.row.value.toFixed(4)}</div>
				<div class="tip-row">smoothed: {hover.row.smooth.toFixed(4)}</div>
			</div>
		{/if}
	</div>
</figure>

<style>
	.cap-curves { margin: 0; }
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
	.chart-area { height: 420px; position: relative; }
	.chart-area :global(.tick text) { font-size: 9px; fill: var(--text-3); }
	.tip {
		position: absolute; bottom: 36px; left: 44px;
		background: var(--panel, #fff); border: 1px solid var(--rule, #ddd);
		border-radius: 6px; padding: 6px 10px; font-size: 0.72rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.12); pointer-events: none;
		z-index: 10; min-width: 160px;
	}
	.tip-head { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
	.tip-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
	.tip-row { color: var(--text-2, #666); line-height: 1.5; }
</style>
