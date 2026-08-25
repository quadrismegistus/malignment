<!--
  Dose-response trend lines: z-scored delta vs base transgressiveness.
  Faceted by significance category (marginal only / dose only / both).
  Tab per language. Lines coloured by norm, with SE ribbons.
-->
<script lang="ts">
	import { LineChart } from 'layerchart';
	import { scaleLinear } from 'd3-scale';

	let { art }: { art: any } = $props();

	type Row = { dose: number; z: number; se: number; scale: string; facet: string; lang: string };
	type ScaleInfo = { scale: string; lang: string; facet: string; p_m: number; p_d: number };

	let rows: Row[] = $derived(art.rows ?? []);
	let langs: string[] = $derived(art.langs ?? ['en']);
	let facets: string[] = $derived(art.facets ?? []);
	let scaleInfo: ScaleInfo[] = $derived(art.scale_info ?? []);

	let activeLang = $state('en');

	const COLOURS = [
		'#4e79a7', '#e15759', '#76b7b2', '#59a14f', '#edc948',
		'#f28e2b', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac'
	];

	function langRows(lang: string): Row[] {
		return rows.filter((r) => r.lang === lang);
	}

	function facetScales(lang: string, facet: string): string[] {
		return [...new Set(rows.filter((r) => r.lang === lang && r.facet === facet).map((r) => r.scale))];
	}

	function allScales(lang: string): string[] {
		return [...new Set(rows.filter((r) => r.lang === lang).map((r) => r.scale))];
	}

	function colourMap(lang: string): Record<string, string> {
		const scales = allScales(lang);
		const m: Record<string, string> = {};
		scales.forEach((s, i) => (m[s] = COLOURS[i % COLOURS.length]));
		return m;
	}

	function seriesData(lang: string, facet: string, scale: string): Row[] {
		return rows
			.filter((r) => r.lang === lang && r.facet === facet && r.scale === scale)
			.sort((a, b) => a.dose - b.dose);
	}

	function xDomain(lang: string): [number, number] {
		const xs = langRows(lang).map((r) => r.dose);
		if (!xs.length) return [1, 2];
		return [Math.min(...xs), Math.max(...xs)];
	}

	function yDomain(lang: string, facet: string): [number, number] {
		const rs = rows.filter((r) => r.lang === lang && r.facet === facet);
		if (!rs.length) return [-1, 1];
		const lo = Math.min(...rs.map((r) => r.z - r.se));
		const hi = Math.max(...rs.map((r) => r.z + r.se));
		const pad = (hi - lo) * 0.1 || 0.1;
		return [lo - pad, hi + pad];
	}

	function pFmt(p: number): string {
		if (p < 0.0001) return '<0.0001';
		if (p < 0.01) return p.toFixed(4);
		return p.toFixed(2);
	}
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

	{@const cm = colourMap(activeLang)}
	{@const xd = xDomain(activeLang)}

	<div class="facet-grid" style="--cols: {facets.filter((f) => facetScales(activeLang, f).length > 0).length}">
		{#each facets as facet}
			{@const scales = facetScales(activeLang, facet)}
			{#if scales.length > 0}
				{@const yd = yDomain(activeLang, facet)}
				<div class="facet">
					<div class="facet-label">{facet}</div>
					<div class="chart-area">
						<LineChart
							data={[]}
							x="dose"
							y="z"
							xScale={scaleLinear()}
							xDomain={xd}
							yDomain={yd}
							padding={{ left: 36, bottom: 28, top: 8, right: 12 }}
							axis={{ x: { format: (d: number) => d.toFixed(1) },
									y: { format: (d: number) => d.toFixed(1) } }}
							grid={{ x: false, y: true }}
							rule={{ x: false, y: 0 }}
							series={scales.map((s) => ({
								key: s,
								color: cm[s],
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
											fill={cm[s]}
											opacity="0.12"
										/>
									{/if}
								{/each}
								<!-- lines -->
								{#each scales as s}
									{@const sd = seriesData(activeLang, facet, s)}
									{#if sd.length > 1}
										<polyline
											points={sd.map((r) => `${context.xScale(r.dose)},${context.yScale(r.z)}`).join(' ')}
											fill="none"
											stroke={cm[s]}
											stroke-width="2"
										/>
									{/if}
								{/each}
							{/snippet}
						</LineChart>
					</div>
				</div>
			{/if}
		{/each}
	</div>

	<div class="legend">
		{#each allScales(activeLang) as s}
			{@const info = scaleInfo.find((i) => i.scale === s && i.lang === activeLang)}
			<span class="leg-item">
				<i style:background={cm[s]}></i>
				{s}
				{#if info}
					<span class="leg-p">
						m:{pFmt(info.p_m)} d:{pFmt(info.p_d)}
					</span>
				{/if}
			</span>
		{/each}
	</div>
</figure>

<style>
	.dose-trends { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub { margin: 0 0 0.6rem; font-size: 0.8rem; color: var(--text-3); max-width: 100ch; }
	.tabs {
		display: flex; gap: 2px; margin-bottom: 0.6rem;
	}
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
	.chart-area { height: 240px; }
	.chart-area :global(.tick text) { font-size: 9px; fill: var(--text-3); }
	.legend {
		display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem;
		margin-top: 0.8rem; font-size: 0.75rem; color: var(--text-3);
	}
	.leg-item { display: flex; align-items: center; gap: 4px; }
	.leg-item i {
		display: inline-block; width: 16px; height: 3px; border-radius: 1px;
	}
	.leg-p { font-size: 0.65rem; opacity: 0.7; }
</style>
