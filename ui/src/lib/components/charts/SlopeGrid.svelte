<!--
  Small multiples of two-point slopegraphs, drawn from a producer's data file.

  RH, 2026-08-21: python produces the minimal data LayerChart needs, LayerChart
  draws. So this component owns NO arithmetic. Every number it renders -- the
  centred y, the panel order, the label, the boundary mark -- was computed and
  asserted in `institutional/plot.py:_slopes_frame` and read off
  `<figure>.data.json`. If a value looks wrong the producer is where it is wrong.

  ## WHY A CSS GRID RATHER THAN A FACET COMPONENT

  LayerChart 2.3.0 exports no faceting primitive, and it does not need one: each
  `LineChart` measures its own container, so a grid of them reflows for free.
  That is the property we came for. Vega-Lite's `width: "container"` does not
  apply to faceted specs, which is why the Vega-Lite version could only be
  SCALED -- shrinking its text -- rather than re-laid-out.

  ## THE Y DOMAIN IS SHARED AND COMES FROM THE FILE

  Every panel uses `art.y_domain`, never its own extent. Levels run 1.00 to 5.86
  across scales, so the producer centres each panel on its own midpoint and hands
  us one domain; a per-panel auto-domain would rescale each and make `harm`
  moving 0.003 look as steep as `directedness` moving 0.267. The whole point of
  the figure is that a steeper line IS a bigger movement.
-->
<script lang="ts">
	import { LineChart } from 'layerchart';
	import { scalePoint } from 'd3-scale';

	type Row = { panel: string; series: string; x: string; y: number; level: number };
	type Panel = { key: string; label: string; note: string; did: number; mark: string };
	type Art = {
		title: string;
		subtitle?: string;
		x_order: string[];
		y_domain: [number, number];
		series: { key: string; colour: string }[];
		panels: Panel[];
		rows: Row[];
	};

	let { art }: { art: Art } = $props();

	//: Grouped once rather than filtered inside the panel loop: `rows.find` per
	//: point is 24 x 2 x 2 scans of the whole array, and the shape LayerChart
	//: wants is one `data` array per series anyway.
	const byPanel = $derived.by(() => {
		const m = new Map<string, Map<string, Row[]>>();
		for (const r of art.rows) {
			if (!m.has(r.panel)) m.set(r.panel, new Map());
			const s = m.get(r.panel)!;
			if (!s.has(r.series)) s.set(r.series, []);
			s.get(r.series)!.push(r);
		}
		//: Sorted into the producer's declared x order, because object order in
		//: JSON is not a guarantee and a slopegraph drawn backwards still looks
		//: like a slopegraph.
		for (const s of m.values())
			for (const arr of s.values())
				arr.sort((a, b) => art.x_order.indexOf(a.x) - art.x_order.indexOf(b.x));
		return m;
	});

	const seriesFor = (panel: string) =>
		art.series.map((s) => ({
			key: s.key,
			color: s.colour,
			data: byPanel.get(panel)?.get(s.key) ?? []
		}));
</script>

<figure class="slopegrid">
	<figcaption>
		<h3>{art.title}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="grid">
		{#each art.panels as p (p.key)}
			<div class="panel">
				<div class="head">
					<span class="name">{p.label}</span>
					<span class="note" title="absolute range across all four points">{p.note}</span>
				</div>
				<div class="chart">
					<LineChart
						x="x"
						y="y"
						xScale={scalePoint().padding(0.5)}
						yDomain={art.y_domain}
						series={seriesFor(p.key)}
						padding={{ left: 24, bottom: 24, top: 4, right: 18 }}
						points={{ r: 2.5 }}
						props={{
							spline: { strokeWidth: 1.8 },
							xAxis: { grid: false, rule: false, tickLength: 0 },
							yAxis: { grid: false, ticks: [-0.5, 0, 0.5] },
							grid: { x: false, y: false }
						}}
					/>
				</div>
			</div>
		{/each}
	</div>

	<div class="legend">
		{#each art.series as s (s.key)}
			<span><i style:background={s.colour}></i>{s.key}</span>
		{/each}
	</div>
</figure>

<style>
	.slopegrid {
		margin: 0;
	}
	figcaption h3 {
		margin: 0 0 0.15rem;
		font-size: 1rem;
	}
	.sub {
		margin: 0 0 0.9rem;
		font-size: 0.85rem;
		color: var(--text-3);
	}
	/*
	  auto-fit with a minimum, so the grid REFLOWS on resize -- six across on a
	  wide panel, two on a narrow one -- and every chart re-lays-out inside its
	  cell rather than being scaled. That is the whole reason for this component.
	*/
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.5rem 0.6rem;
	}
	.panel {
		min-width: 0;
	}
	.head {
		display: flex;
		flex-direction: column;
		font-size: 0.7rem;
		line-height: 1.25;
		/*
		  FIXED TWO LINES. A one-row header let a long label wrap and push its own
		  chart down while its neighbours stayed put, so the grid rows came out
		  ragged. Reserving the space keeps every chart on the same baseline.
		*/
		height: 2.5em;
		overflow: hidden;
	}
	.name {
		font-weight: 600;
		color: var(--text-2);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.note {
		color: var(--text-3);
		opacity: 0.7;
		white-space: nowrap;
	}
	.chart {
		height: 124px;
	}
	/*
	  The axis text is LayerChart's default size, which is sized for one chart
	  rather than 24 in a grid. Scoped to this component so nothing else moves.
	*/
	.chart :global(.tick text) {
		font-size: 9px;
		fill: var(--text-3);
	}
	.legend {
		display: flex;
		gap: 1rem;
		margin-top: 0.8rem;
		font-size: 0.8rem;
		color: var(--text-3);
	}
	.legend i {
		display: inline-block;
		width: 14px;
		height: 2px;
		margin-right: 0.35rem;
		vertical-align: middle;
	}
</style>
