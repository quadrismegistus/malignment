<!--
  Dose-response scatter: x = base-arm transgressiveness, y = delta on each scale.
  Small multiples, one panel per scale. Cloud of sampled cells + binned mean trend.
-->
<script lang="ts">
	let { art }: { art: any } = $props();

	type SampleRow = { dose: number; delta: number; scale: string };
	type BinnedRow = { dose: number; delta: number; se: number; n: number; scale: string };

	let scales: string[] = $derived(art.scales ?? []);
	let sample: SampleRow[] = $derived(art.sample ?? []);
	let binned: BinnedRow[] = $derived(art.binned ?? []);

	const PAD = { top: 12, right: 12, bottom: 28, left: 44 };
	const W = 280;
	const H = 200;
	const iw = W - PAD.left - PAD.right;
	const ih = H - PAD.top - PAD.bottom;

	function panelData(scale: string) {
		return sample.filter((r: SampleRow) => r.scale === scale);
	}
	function trendData(scale: string) {
		return binned
			.filter((r: BinnedRow) => r.scale === scale)
			.sort((a: BinnedRow, b: BinnedRow) => a.dose - b.dose);
	}

	let xDomain = $derived.by(() => {
		if (!sample.length) return [0, 1] as [number, number];
		const xs = sample.map((r: SampleRow) => r.dose);
		return [Math.min(...xs), Math.max(...xs)] as [number, number];
	});

	function xScale(v: number) {
		return PAD.left + ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * iw;
	}

	function yDomain(pts: SampleRow[]): [number, number] {
		if (!pts.length) return [-0.1, 0.1];
		const ys = pts.map((r) => r.delta);
		const lo = Math.min(...ys, 0);
		const hi = Math.max(...ys, 0);
		const pad = (hi - lo) * 0.12 || 0.02;
		return [lo - pad, hi + pad];
	}

	function makeYScale(dom: [number, number]) {
		return (v: number) => PAD.top + ((dom[1] - v) / (dom[1] - dom[0])) * ih;
	}

	function ticks(dom: [number, number], n: number): number[] {
		const step = (dom[1] - dom[0]) / n;
		const out: number[] = [];
		for (let i = 0; i <= n; i++) out.push(dom[0] + step * i);
		return out;
	}

	function fmt(v: number): string {
		if (Math.abs(v) < 0.001) return '0';
		return v.toFixed(2);
	}
</script>

{#if art.title}
	<h3 class="title">{art.title}</h3>
{/if}
{#if art.subtitle}
	<p class="subtitle">{art.subtitle}</p>
{/if}

<div class="grid">
	{#each scales as scale}
		{@const pts = panelData(scale)}
		{@const trend = trendData(scale)}
		{@const yDom = yDomain(pts)}
		{@const ys = makeYScale(yDom)}
		<div class="panel">
			<div class="panel-label">{scale}</div>
			<svg viewBox="0 0 {W} {H}" width="100%" height="100%">
				<!-- y gridlines -->
				{#each ticks(yDom, 4) as t}
					<line x1={PAD.left} x2={W - PAD.right} y1={ys(t)} y2={ys(t)}
						stroke="#eee" stroke-width="0.5" />
					<text x={PAD.left - 4} y={ys(t) + 3} text-anchor="end"
						font-size="8" fill="#999">{fmt(t)}</text>
				{/each}

				<!-- zero line -->
				<line x1={PAD.left} x2={W - PAD.right} y1={ys(0)} y2={ys(0)}
					stroke="#aaa" stroke-dasharray="4 3" stroke-width="0.8" />

				<!-- sample cloud -->
				{#each pts as p}
					<circle cx={xScale(p.dose)} cy={ys(p.delta)} r="1.8"
						fill="#4e79a7" opacity="0.2" />
				{/each}

				<!-- trend line + SE bars -->
				{#if trend.length > 1}
					<polyline
						points={trend.map((t) => `${xScale(t.dose)},${ys(t.delta)}`).join(' ')}
						fill="none" stroke="#e15759" stroke-width="2" />
					{#each trend as t}
						<line x1={xScale(t.dose)} x2={xScale(t.dose)}
							y1={ys(t.delta - t.se)} y2={ys(t.delta + t.se)}
							stroke="#e15759" stroke-width="1" opacity="0.5" />
					{/each}
				{/if}

				<!-- x axis ticks -->
				{#each ticks(xDomain, 3) as t}
					<text x={xScale(t)} y={H - 6} text-anchor="middle"
						font-size="8" fill="#999">{t.toFixed(1)}</text>
				{/each}
			</svg>
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
		max-width: 80ch;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 8px;
	}
	@media (max-width: 900px) {
		.grid { grid-template-columns: repeat(2, 1fr); }
	}
	.panel {
		border: 1px solid var(--rule, #e0e0e0);
		border-radius: 6px;
		padding: 4px 4px 0;
		background: var(--panel, #fafafa);
	}
	.panel-label {
		text-align: center;
		font-size: 11px;
		font-weight: 600;
		color: var(--text-2, #555);
		margin-bottom: 0;
	}
	svg {
		display: block;
	}
</style>
