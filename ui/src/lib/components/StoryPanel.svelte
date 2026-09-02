<!--
  Norms and fields panel: slopegraphs for fields (pair data),
  dot-interval for norms (delta data). Declared vs exploratory separated.
-->
<script lang="ts">
	let loading = $state(true);
	let data = $state<any>(null);
	let family = $state<'fields'>('fields');
	let hover = $state<string | null>(null);

	const BASE = '/api';

	async function load() {
		loading = true;
		const r = await fetch(`${BASE}/story/panel`);
		data = await r.json();
		loading = false;
	}
	load();

	let rows = $derived.by(() => {
		if (!data?.values) return [];
		return data.values.filter((r: any) =>
			r.contrast === 'arm' && r.family === 'fields');
	});

	let group = $state<string>('field_tokens');
	let declared = $derived(rows.filter((r: any) => r.declared === true && r.group === group));
	let exploratory = $derived(
		rows.filter((r: any) => r.declared !== true && r.group === group)
			.filter((r: any) => (r.h_sign ?? 1) < 0.2)
			.sort((a: any, b: any) => Math.abs(b.dz ?? 0) - Math.abs(a.dz ?? 0))
	);
	let groups = $derived([...new Set(rows.map((r: any) => r.group))].filter(Boolean).sort());

	const PALETTE = ['#4e79a7', '#e15759', '#f28e2b', '#76b7b2', '#59a14f', '#edc949', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ab'];
	function rowColor(i: number) { return PALETTE[i % PALETTE.length]; }

	function sigMark(r: any): string {
		if (r.significant_all) return '**';
		if (r.significant) return '*';
		return '';
	}

	function shortLabel(r: any): string {
		let l = r.label ?? r.id ?? '';
		l = l.replace(/^tok\/usas:/, '').replace(/^typ\/usas:/, '')
		     .replace(/^tok\/rid:/, '').replace(/^typ\/rid:/, '')
		     .replace(/_/g, ' ');
		return l.slice(0, 20);
	}

	let isShare = $derived(group === 'field_tokens' || group === 'field_types' || group === 'coverage');

	function fmtVal(v: number): string {
		if (isShare) return (v * 100).toFixed(2) + '%';
		return v < 0.1 ? v.toFixed(4) : v.toFixed(2);
	}
</script>

<style>
	.controls { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; font-size: 12px; }
	.controls select, .controls button { background: var(--panel); border: 1px solid var(--rule); color: var(--text); padding: 3px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; }
	.controls button.active { background: var(--blue); color: #fff; border-color: var(--blue); }
	.section-header { font-size: 12px; font-weight: 600; color: var(--text-3); margin: 16px 0 4px; border-bottom: 1px solid var(--rule); padding-bottom: 2px; }
	.grid { display: flex; flex-wrap: wrap; gap: 4px; }
	.muted { color: var(--text-3); font-size: 11px; }
</style>

<div class="controls">
	{#each groups as g}
		<button class:active={group === g} onclick={() => group = g}>{g.replace(/_/g, ' ')}</button>
	{/each}
	<span class="muted">{exploratory.length} at p &lt; 0.2{declared.length ? ` · ${declared.length} declared` : ''}</span>
</div>

{#if loading}
	<p class="muted">loading...</p>
{:else}
	{#if declared.length}
		<div class="section-header">declared hypotheses (shown regardless of significance)</div>
		<div class="grid">
			{#each [...declared].sort((a, b) => Math.abs(b.dz ?? 0) - Math.abs(a.dz ?? 0)) as r, i}
				{@const w = 150}
				{@const h = 85}
				{@const padT = 14}
				{@const padB = 16}
				{@const padL = 32}
				{@const padR = 32}
				{@const col = rowColor(i)}
				{@const hot = hover === r.id}
				{@const pl = r.per_lineage ?? {}}
				{@const isPair = r.per_lineage_kind === 'pair'}
				<div style="opacity:{hover === null || hot ? 1 : 0.25}"
					onmouseenter={() => hover = r.id}
					onmouseleave={() => hover = null}>
					{#if isPair}
						{@const vals = Object.values(pl).flat()}
						{@const minV = Math.min(...vals)}
						{@const maxV = Math.max(...vals)}
						{@const pad = Math.max((maxV - minV) * 0.12, 0.0001)}
						{@const lo = minV - pad}
						{@const hi = maxV + pad}
						{@const x0 = padL}
						{@const x1 = w - padR}
						{@const y = (v) => padT + (1 - (v - lo) / (hi - lo)) * (h - padT - padB)}
						<svg viewBox="0 0 {w} {h}" width={w} height={h} style="cursor:default">
							{#each Object.entries(pl) as [lin, pair]}
								<line x1={x0} y1={y(pair[0])} x2={x1} y2={y(pair[1])}
									stroke={col} stroke-width={hot ? 1 : 0.5} opacity={hot ? 0.5 : 0.15} />
							{/each}
							{#if r.a != null && r.b != null}
								<line x1={x0} y1={y(r.a)} x2={x1} y2={y(r.b)}
									stroke={col} stroke-width={hot ? 3 : 2} opacity={hot ? 1 : 0.8} />
								<circle cx={x0} cy={y(r.a)} r={hot ? 3 : 2} fill={col} />
								<circle cx={x1} cy={y(r.b)} r={hot ? 3 : 2} fill={col} />
								<text x={x0 - 1} y={y(r.a) + 3} text-anchor="end" font-size="5.5" fill="#ddd">{fmtVal(r.a)}</text>
								<text x={x1 + 1} y={y(r.b) + 3} text-anchor="start" font-size="5.5" fill="#ddd">{fmtVal(r.b)}</text>
							{/if}
							<text x={w/2} y="10" text-anchor="middle" font-size="7" fill={col}>
								{shortLabel(r)}
							</text>
							<text x={w/2} y={h - 2} text-anchor="middle" font-size="6.5"
								fill={r.significant ? '#cccccc' : '#555555'}>
								{r.up}/{r.down}{r.ties ? `/${r.ties}t` : ''} {sigMark(r)}
							</text>
						</svg>
					{:else}
						{@const deltas = Object.values(pl)}
						{@const maxD = Math.max(...deltas.map(Math.abs), 0.001)}
						{@const cy = h / 2}
						{@const x = (v) => padL + ((v + maxD) / (2 * maxD)) * (w - padL - padR)}
						<svg viewBox="0 0 {w} {h}" width={w} height={h} style="cursor:default">
							<line x1={x(0)} x2={x(0)} y1={padT} y2={h - padB} stroke="#555" stroke-width="0.5" />
							{#each deltas as d, di}
								<circle cx={x(d)} cy={cy + (di - deltas.length/2) * 0.8} r="1.2"
									fill={col} opacity={hot ? 0.5 : 0.2} />
							{/each}
							{#if r.effect != null}
								<line x1={x(r.effect)} x2={x(r.effect)} y1={cy - 8} y2={cy + 8}
									stroke={col} stroke-width={hot ? 3 : 2} />
							{/if}
							{#if r.ci}
								<line x1={x(r.ci[0])} x2={x(r.ci[1])} y1={cy} y2={cy}
									stroke={col} stroke-width={hot ? 2 : 1} opacity="0.6" />
							{/if}
							<text x={w/2} y="10" text-anchor="middle" font-size="7" fill={col}>
								{shortLabel(r)}
							</text>
							<text x={w/2} y={h - 2} text-anchor="middle" font-size="6.5"
								fill={r.significant ? '#cccccc' : '#555555'}>
								{r.up}/{r.down}{r.ties ? `/${r.ties}t` : ''} {sigMark(r)}
							</text>
						</svg>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	{#if exploratory.length}
		<details open>
			<summary class="section-header" style="cursor:pointer">
				exploratory (p &lt; 0.2, {exploratory.length} scales, sorted by |effect|)
			</summary>
			<div class="grid">
				{#each exploratory as r, i}
					{@const w = 130}
					{@const h = 70}
					{@const padT = 12}
					{@const padB = 14}
					{@const padL = 28}
					{@const padR = 28}
					{@const col = rowColor(i)}
					{@const hot = hover === r.id}
					{@const pl = r.per_lineage ?? {}}
					{@const isPair = r.per_lineage_kind === 'pair'}
					<div style="opacity:{hover === null || hot ? 1 : 0.25}"
						onmouseenter={() => hover = r.id}
						onmouseleave={() => hover = null}>
						{#if isPair}
							{@const vals = Object.values(pl).flat()}
							{@const minV = Math.min(...vals)}
							{@const maxV = Math.max(...vals)}
							{@const vpad = Math.max((maxV - minV) * 0.12, 0.0001)}
							{@const lo = minV - vpad}
							{@const hi = maxV + vpad}
							{@const x0 = padL}
							{@const x1 = w - padR}
							{@const y = (v) => padT + (1 - (v - lo) / (hi - lo)) * (h - padT - padB)}
							<svg viewBox="0 0 {w} {h}" width={w} height={h} style="cursor:default">
								{#each Object.entries(pl) as [lin, pair]}
									<line x1={x0} y1={y(pair[0])} x2={x1} y2={y(pair[1])}
										stroke={col} stroke-width={hot ? 1 : 0.4} opacity={hot ? 0.5 : 0.12} />
								{/each}
								{#if r.a != null && r.b != null}
									<line x1={x0} y1={y(r.a)} x2={x1} y2={y(r.b)}
										stroke={col} stroke-width={hot ? 2.5 : 1.5} opacity={hot ? 1 : 0.8} />
									<text x={x0 - 1} y={y(r.a) + 3} text-anchor="end" font-size="5" fill="#ddd">{fmtVal(r.a)}</text>
									<text x={x1 + 1} y={y(r.b) + 3} text-anchor="start" font-size="5" fill="#ddd">{fmtVal(r.b)}</text>
								{/if}
								<text x={w/2} y="9" text-anchor="middle" font-size="6.5" fill={col}>
									{shortLabel(r)}
								</text>
								<text x={w/2} y={h - 2} text-anchor="middle" font-size="6"
									fill={r.significant ? '#cccccc' : '#555555'}>
									{r.up}/{r.down} {sigMark(r)}
								</text>
							</svg>
						{:else}
							{@const deltas = Object.values(pl)}
							{@const maxD = Math.max(...deltas.map(Math.abs), 0.001)}
							{@const cy = h / 2}
							{@const x = (v) => padL + ((v + maxD) / (2 * maxD)) * (w - padL - padR)}
							<svg viewBox="0 0 {w} {h}" width={w} height={h} style="cursor:default">
								<line x1={x(0)} x2={x(0)} y1={padT} y2={h - padB} stroke="#555" stroke-width="0.5" />
								{#each deltas as d, di}
									<circle cx={x(d)} cy={cy + (di - deltas.length/2) * 0.6} r="1"
										fill={col} opacity={hot ? 0.4 : 0.15} />
								{/each}
								{#if r.effect != null}
									<line x1={x(r.effect)} x2={x(r.effect)} y1={cy - 6} y2={cy + 6}
										stroke={col} stroke-width={hot ? 2.5 : 1.5} />
								{/if}
								{#if r.ci}
									<line x1={x(r.ci[0])} x2={x(r.ci[1])} y1={cy} y2={cy}
										stroke={col} stroke-width={hot ? 1.5 : 0.8} opacity="0.5" />
								{/if}
								<text x={w/2} y="9" text-anchor="middle" font-size="6.5" fill={col}>
									{shortLabel(r)}
								</text>
								<text x={w/2} y={h - 2} text-anchor="middle" font-size="6"
									fill={r.significant ? '#cccccc' : '#555555'}>
									{r.up}/{r.down} {sigMark(r)}
								</text>
							</svg>
						{/if}
					</div>
				{/each}
			</div>
		</details>
	{/if}
{/if}
