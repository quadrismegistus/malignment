<!--
  Dose-response trend lines: z-scored delta vs base transgressiveness.
  Faceted by significance category (marginal only / dose only / both).
  Tab per language. Lines coloured by norm, with SE ribbons.
  SHARED Y-AXIS across facets so the slopes are visually comparable.
-->
<script lang="ts">
	import { LineChart, Tooltip } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type Row = { dose: number; z: number; raw: number; se: number; n: number;
	             scale: string; facet: string; lang: string };
	type ScaleInfo = { scale: string; lang: string; facet: string;
	                   p_m: number; p_d: number; mu: number; sd: number };

	let rows: Row[] = $derived(art.rows ?? []);
	let langs: string[] = $derived(art.langs ?? ['en']);
	let facets: string[] = $derived(art.facets ?? []);
	let scaleInfo: ScaleInfo[] = $derived(art.scale_info ?? []);

	let activeLang = $state('en');

	const COLOURS: Record<string, string> = {
		'bodily harm': '#e15759', 'register': '#4e79a7', 'valence': '#59a14f',
		'concreteness': '#f28e2b', 'vulgarity': '#b07aa1', 'charge': '#edc948',
		'valence (W)': '#76b7b2', 'arousal (W)': '#ff9da7',
		'dominance (W)': '#9c755f', 'concreteness (B)': '#bab0ac',
		'concreteness (zh)': '#f28e2b', 'transgressiveness': '#e15759'
	};
	function cm(s: string): string { return COLOURS[s] ?? '#888'; }

	function langRows(lang: string): Row[] {
		return rows.filter((r) => r.lang === lang);
	}
	function facetScales(lang: string, facet: string): string[] {
		return [...new Set(rows.filter((r) => r.lang === lang && r.facet === facet).map((r) => r.scale))];
	}
	function allScales(lang: string): string[] {
		return [...new Set(rows.filter((r) => r.lang === lang).map((r) => r.scale))];
	}
	function seriesData(lang: string, facet: string, scale: string): Row[] {
		return rows
			.filter((r) => r.lang === lang && r.facet === facet && r.scale === scale)
			.sort((a, b) => a.dose - b.dose);
	}

	let xd = $derived.by(() => {
		const xs = langRows(activeLang).map((r) => r.dose);
		if (!xs.length) return [1, 2] as [number, number];
		return [Math.min(...xs), Math.max(...xs)] as [number, number];
	});

	let yd = $derived.by(() => {
		const rs = langRows(activeLang);
		if (!rs.length) return [-1, 1] as [number, number];
		const lo = Math.min(...rs.map((r) => r.z - r.se));
		const hi = Math.max(...rs.map((r) => r.z + r.se));
		const pad = (hi - lo) * 0.08 || 0.1;
		return [lo - pad, hi + pad] as [number, number];
	});

	let activeFacets = $derived(facets.filter((f) => facetScales(activeLang, f).length > 0));

	function pFmt(p: number): string {
		if (p < 0.0001) return '<.0001';
		if (p < 0.01) return p.toFixed(4);
		return p.toFixed(2);
	}

	let hover = $state<{ facet: string; scale: string; bin: Row } | null>(null);
</script>

<figure class="dose-trends">
	<figcaption>
		<h3>{art.title ?? 'Dose-response trends'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="tabs">
		{#each langs as lang}
			<button class:active={activeLang === lang} onclick={() => (activeLang = lang)}>
				{lang === 'en' ? 'English' : 'Chinese'}
			</button>
		{/each}
	</div>

	<div class="facet-grid" style="--cols: {activeFacets.length}">
		{#each activeFacets as facet}
			{@const scales = facetScales(activeLang, facet)}
			<div class="facet">
				<div class="facet-label">{facet}</div>
				<div class="chart-area"
					onmouseleave={() => hover = null}>
					<LineChart
						data={[]}
						x="dose" y="z"
						xScale={scaleLinear()}
						xDomain={xd} yDomain={yd}
						padding={{ left: 36, bottom: 28, top: 8, right: 12 }}
						axis={{ x: { format: (d: number) => d.toFixed(1) },
								y: { format: (d: number) => d.toFixed(1) } }}
						grid={{ x: false, y: true }}
						rule={{ x: false, y: 0 }}
						series={scales.map((s) => ({
							key: s, color: cm(s),
							data: seriesData(activeLang, facet, s)
						}))}
						props={{
							spline: { strokeWidth: 2 },
							xAxis: { rule: false },
							yAxis: { rule: false }
						}}
					>
						{#snippet marks({ context }: { context: any })}
							<!-- SE ribbons -->
							{#each scales as s}
								{@const sd = seriesData(activeLang, facet, s)}
								{#if sd.length > 1}
									<polygon
										points={[
											...sd.map((r) => `${context.xScale(r.dose)},${context.yScale(r.z + r.se)}`),
											...sd.toReversed().map((r) => `${context.xScale(r.dose)},${context.yScale(r.z - r.se)}`)
										].join(' ')}
										fill={cm(s)} opacity="0.12"
									/>
								{/if}
							{/each}
							<!-- lines with hover targets -->
							{#each scales as s}
								{@const sd = seriesData(activeLang, facet, s)}
								{#if sd.length > 1}
									<!-- fat invisible stroke for easier hovering -->
									<polyline
										points={sd.map((r) => `${context.xScale(r.dose)},${context.yScale(r.z)}`).join(' ')}
										fill="none" stroke="transparent" stroke-width="12"
										onmouseenter={() => hover = { facet, scale: s, bin: sd[0] }}
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
												const d = Math.abs(r.dose - mouseX);
												if (d < minDist) { minDist = d; closest = r; }
											}
											hover = { facet, scale: s, bin: closest };
										}}
									/>
									<!-- visible line -->
									<polyline
										points={sd.map((r) => `${context.xScale(r.dose)},${context.yScale(r.z)}`).join(' ')}
										fill="none" stroke={cm(s)} stroke-width="2"
										opacity={hover && hover.facet === facet && hover.scale !== s ? 0.25 : 1}
										style="pointer-events: none"
									/>
								{/if}
							{/each}
							<!-- tooltip dot -->
							{#if hover && hover.facet === facet}
								{@const b = hover.bin}
								<circle
									cx={context.xScale(b.dose)} cy={context.yScale(b.z)}
									r="4" fill={cm(hover.scale)} stroke="#fff" stroke-width="1.5"
									style="pointer-events: none"
								/>
							{/if}
						{/snippet}
					</LineChart>
					<!-- custom tooltip overlay -->
					{#if hover && hover.facet === facet}
						{@const b = hover.bin}
						{@const info = scaleInfo.find((i) => i.scale === hover.scale && i.lang === activeLang)}
						<div class="tip">
							<div class="tip-head">
								<span class="tip-swatch" style:background={cm(hover.scale)}></span>
								<strong>{hover.scale}</strong>
							</div>
							<div class="tip-row">dose: {b.dose.toFixed(2)}</div>
							<div class="tip-row">z-score: {b.z >= 0 ? '+' : ''}{b.z.toFixed(3)}</div>
							<div class="tip-row">raw delta: {b.raw >= 0 ? '+' : ''}{b.raw.toFixed(4)}</div>
							<div class="tip-row">n cells: {b.n.toLocaleString()}</div>
							{#if info}
								<div class="tip-row tip-p">marginal p={pFmt(info.p_m)}  dose p={pFmt(info.p_d)}</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>

	<div class="legend">
		{#each allScales(activeLang) as s}
			{@const info = scaleInfo.find((i) => i.scale === s && i.lang === activeLang)}
			<span class="leg-item">
				<i style:background={cm(s)}></i>
				{s}
				{#if info}
					<span class="leg-p">m:{pFmt(info.p_m)} d:{pFmt(info.p_d)}</span>
				{/if}
			</span>
		{/each}
	</div>
</figure>

<style>
	.dose-trends { margin: 0; }
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
	.facet-grid {
		display: grid;
		grid-template-columns: repeat(var(--cols, 3), 1fr);
		gap: 0.5rem;
	}
	.facet { min-width: 0; }
	.facet-label {
		text-align: center; font-size: 0.75rem; font-weight: 600;
		color: var(--text-2); padding: 2px 0; text-transform: uppercase;
		letter-spacing: 0.5px;
	}
	.chart-area { height: 280px; position: relative; }
	.chart-area :global(.tick text) { font-size: 9px; fill: var(--text-3); }
	.tip {
		position: absolute; top: 8px; right: 8px;
		background: var(--panel, #fff); border: 1px solid var(--rule, #ddd);
		border-radius: 6px; padding: 6px 10px; font-size: 0.72rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.12); pointer-events: none;
		z-index: 10; min-width: 140px;
	}
	.tip-head { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
	.tip-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
	.tip-row { color: var(--text-2, #666); line-height: 1.5; }
	.tip-p { font-size: 0.65rem; opacity: 0.7; margin-top: 2px; }
	.legend {
		display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem;
		margin-top: 0.8rem; font-size: 0.75rem; color: var(--text-3);
	}
	.leg-item { display: flex; align-items: center; gap: 4px; }
	.leg-item i { display: inline-block; width: 16px; height: 3px; border-radius: 1px; }
	.leg-p { font-size: 0.65rem; opacity: 0.7; }
</style>
