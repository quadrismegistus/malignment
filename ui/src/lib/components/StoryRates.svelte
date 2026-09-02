<!--
  Faceted slopegraphs: per-annotation-value rate, base vs aligned,
  with per-lineage spaghetti behind the mean. Auto-wrapping grid.
-->
<script lang="ts">
	let loading = $state(true);
	let data = $state<any>(null);
	let frame = $state('raw');
	let hoverField = $state<string | null>(null);
	let hoverValue = $state<string | null>(null);

	const BASE = '/api';

	async function load() {
		loading = true;
		const r = await fetch(`${BASE}/story/rates?frame=${frame}`);
		data = await r.json();
		loading = false;
	}
	load();
	$effect(() => { frame; load(); });

	function signTestP(up: number, dn: number): number {
		const n = up + dn;
		if (n < 3) return 1;
		const k = Math.min(up, dn);
		let p = 0;
		for (let i = 0; i <= k; i++) {
			let c = 1;
			for (let j = 0; j < i; j++) c = c * (n - j) / (j + 1);
			p += c;
		}
		return Math.min(1, 2 * p / Math.pow(2, n));
	}

	let byField = $derived.by(() => {
		if (!data?.facets) return [];
		const fields = new Map<string, any[]>();
		for (const f of data.facets) {
			const s = stats(f.lines);
			if (!fields.has(f.field)) fields.set(f.field, []);
			fields.get(f.field)!.push({ ...f, _s: s, _absChange: Math.abs(s.ma - s.mb), _p: signTestP(s.up, s.dn) });
		}
		return [...fields.entries()].map(([field, facets]) => ({
			field,
			facets: facets.sort((a: any, b: any) => b._absChange - a._absChange)
		}));
	});

	const FIELD_COLORS: Record<string, string[]> = {};
	const PALETTE = ['#4e79a7', '#e15759', '#f28e2b', '#76b7b2', '#59a14f', '#edc949', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ab'];

	function valColor(field: string, value: string): string {
		if (!FIELD_COLORS[field]) {
			const vals = byField.find((f) => f.field === field)?.facets.map((f: any) => f.value) ?? [];
			FIELD_COLORS[field] = {};
			vals.forEach((v: string, i: number) => { FIELD_COLORS[field][v] = PALETTE[i % PALETTE.length]; });
		}
		return FIELD_COLORS[field][value] ?? '#888888';
	}

	function stats(lines: any[]) {
		const base = lines.filter((l: any) => l.arm === 'base').map((l: any) => l.rate);
		const aligned = lines.filter((l: any) => l.arm === 'aligned').map((l: any) => l.rate);
		const mb = base.length ? base.reduce((a: number, b: number) => a + b, 0) / base.length : 0;
		const ma = aligned.length ? aligned.reduce((a: number, b: number) => a + b, 0) / aligned.length : 0;
		const up = base.reduce((n: number, b: number, i: number) => n + (aligned[i] > b ? 1 : 0), 0);
		const dn = base.reduce((n: number, b: number, i: number) => n + (aligned[i] < b ? 1 : 0), 0);
		return { mb, ma, up, dn, n: base.length };
	}
</script>

<style>
	.controls { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; font-size: 12px; }
	.controls select { background: var(--panel); border: 1px solid var(--rule); color: var(--text); padding: 3px 8px; border-radius: 4px; font-size: 11px; }
	.grid { display: flex; flex-wrap: wrap; gap: 4px; }
	.facet { flex: 0 0 auto; }
	.field-header { font-size: 11px; font-weight: 600; color: var(--text-3); margin: 12px 0 2px; border-bottom: 1px solid var(--rule); padding-bottom: 2px; }
	.muted { color: var(--text-3); font-size: 11px; }
</style>

<div class="controls">
	<label>frame <select bind:value={frame}>
		<option value="raw">raw</option>
		<option value="prefill">prefill</option>
	</select></label>
	{#if data}
		<span class="muted">{data.n_lineages} lineages · {data.n_base} base · {data.n_aligned} aligned</span>
	{/if}
</div>

{#if loading}
	<p class="muted">loading rates...</p>
{:else if data}
	{#each byField as group}
		<div class="field-header"
			onmouseenter={() => hoverField = group.field}
			onmouseleave={() => hoverField = null}>
			{group.field.replace(/_/g, ' ')} <span class="muted">({group.facets.length} values)</span>
		</div>
		<div class="grid">
			{#each group.facets as facet}
				{@const s = stats(facet.lines)}
				{@const w = 120}
				{@const h = 80}
				{@const padL = 6}
				{@const padR = 6}
				{@const padT = 14}
				{@const padB = 14}
				{@const x0 = padL}
				{@const x1 = w - padR}
				{@const maxR = Math.max(s.mb, s.ma, ...facet.lines.map((l) => l.rate), 0.01)}
				{@const y = (v) => padT + (1 - v / maxR) * (h - padT - padB)}
				{@const col = valColor(facet.field, facet.value)}
				{@const active = hoverField === null || hoverField === facet.field}
				{@const hot = hoverValue === facet.field + ':' + facet.value}
				<div class="facet" style="opacity:{active ? 1 : 0.2}">
					<svg viewBox="0 0 {w} {h}" width={w} height={h}
						onmouseenter={() => hoverValue = facet.field + ':' + facet.value}
						onmouseleave={() => hoverValue = null}
						style="cursor:default">
						<line x1={x0} x2={x1} y1={y(0)} y2={y(0)} stroke="#333" stroke-width="0.3" />
						{#each facet.lines.filter((l) => l.arm === 'base') as bl}
							{@const al = facet.lines.find((l) => l.arm === 'aligned' && l.lineage === bl.lineage)}
							{#if al}
								<line x1={x0} y1={y(bl.rate)} x2={x1} y2={y(al.rate)}
									stroke={col} stroke-width={hot ? 1.2 : 0.5}
									opacity={hot ? 0.5 : 0.15} />
							{/if}
						{/each}
						<line x1={x0} y1={y(s.mb)} x2={x1} y2={y(s.ma)}
							stroke={col} stroke-width={hot ? 3 : 2} opacity={hot ? 1 : 0.8} />
						<circle cx={x0} cy={y(s.mb)} r={hot ? 3 : 2} fill={col} />
						<circle cx={x1} cy={y(s.ma)} r={hot ? 3 : 2} fill={col} />
						<text x={w / 2} y="10" text-anchor="middle" font-size="8" fill={col}>
							{facet.value.replace(/_/g, ' ')}
						</text>
					<text x={w / 2} y={h - 2} text-anchor="middle" font-size="7" fill={facet.stats?.significant ? '#cccccc' : '#555555'}>
							{Math.round(s.mb * 100)}→{Math.round(s.ma * 100)}% {s.up}/{s.dn}{facet.stats?.sig_all ? '**' : facet.stats?.significant ? '*' : ''}
						</text>
					</svg>
				</div>
			{/each}
		</div>
	{/each}
{/if}
