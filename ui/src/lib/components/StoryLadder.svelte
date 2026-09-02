<!--
  Training ladder: x = rung (base → SFT → DPO → Instruct), y = annotation rate.
  One line per annotation value, faceted by family. The monotonicity is the message.
-->
<script lang="ts">
	let loading = $state(true);
	let data = $state<any>(null);
	let hover = $state<string | null>(null);
	let view = $state<'combined' | 'families'>('combined');

	const BASE = '/api';
	const FIELDS = [
		'mood=affirming', 'mood=unsettling',
		'protagonist_change=self', 'protagonist_change=none',
		'conflict_mode=enacted', 'opponent=none',
		'tradition', 'nostalgia', 'renewal', 'small_community',
		'collective_action', 'ending=loss', 'resolution_scale=inward',
	];
	const COLORS: Record<string, string> = {
		'mood=affirming': '#59a14f', 'mood=unsettling': '#e15759',
		'protagonist_change=self': '#4e79a7', 'protagonist_change=none': '#9c755f',
		'conflict_mode=enacted': '#f28e2b', 'opponent=none': '#b07aa1',
		'tradition': '#edc949', 'nostalgia': '#76b7b2', 'renewal': '#59a14f',
		'small_community': '#ff9da7', 'collective_action': '#4e79a7',
		'ending=loss': '#e15759', 'resolution_scale=inward': '#b07aa1',
	};

	async function load() {
		loading = true;
		const r = await fetch(`${BASE}/story/ladder?frame=raw`);
		data = await r.json();
		loading = false;
	}
	load();

	let families = $derived(data ? Object.keys(data.ladders) : []);
	let rungs = $derived(data?.rungs ?? []);
</script>

<style>
	.grid { display: flex; flex-wrap: wrap; gap: 16px; }
	.panel { flex: 1 1 320px; max-width: 380px; }
	.panel h4 { margin: 0 0 4px; font-size: 12px; color: var(--text-2); }
	.legend { display: flex; flex-wrap: wrap; gap: 6px; font-size: 10px; margin: 8px 0; }
	.legend span { padding: 1px 6px; cursor: default; }
	.muted { color: var(--text-3); font-size: 11px; }
</style>

{#if loading}
	<p class="muted">loading ladder...</p>
{:else if data}
	<div style="display:flex;gap:12px;align-items:center;margin-bottom:8px">
		<button class:active={view === 'combined'} onclick={() => view = 'combined'}
			style="background:{view === 'combined' ? 'var(--blue)' : 'var(--panel)'};color:{view === 'combined' ? '#fff' : 'var(--text)'};border:1px solid var(--rule);padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer">
			combined (median)
		</button>
		<button class:active={view === 'families'} onclick={() => view = 'families'}
			style="background:{view === 'families' ? 'var(--blue)' : 'var(--panel)'};color:{view === 'families' ? '#fff' : 'var(--text)'};border:1px solid var(--rule);padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer">
			per family
		</button>
	</div>

	{#if view === 'combined'}
		{@const allFams = Object.values(data.ladders)}
		{@const w = 600}
		{@const h = 380}
		{@const padT = 20}
		{@const padB = 36}
		{@const padL = 44}
		{@const padR = 160}
		{@const x = (i) => padL + (i / (rungs.length - 1)) * (w - padL - padR)}
		{@const y = (v) => padT + (1 - v) * (h - padT - padB)}
		{@const allMedians = FIELDS.map((f) => ({
			f,
			col: COLORS[f] ?? '#888',
			meds: rungs.map((_: any, ri: number) => {
				const vals = allFams.map((fam: any) => fam[ri]?.[f] ?? null).filter((v: any) => v !== null);
				if (!vals.length) return null;
				const s = [...vals].sort((a: number, b: number) => a - b);
				return s[Math.floor(s.length / 2)];
			}),
		}))}
		{@const labelPositions = (() => {
			const items = allMedians
				.filter((m) => m.meds[m.meds.length - 1] !== null)
				.map((m) => ({ f: m.f, col: m.col, raw: y(m.meds[m.meds.length - 1]) }))
				.sort((a, b) => a.raw - b.raw);
			const gap = 13;
			let prev = -1e9;
			return items.map((it) => {
				let ly = Math.max(it.raw, prev + gap);
				prev = ly;
				return { ...it, ly };
			});
		})()}
		<svg viewBox="0 0 {w} {h}" style="width:100%;max-width:800px;display:block;margin:0 auto">
			{#each [0, 0.25, 0.5, 0.75, 1] as tick}
				<line x1={padL} x2={w - padR} y1={y(tick)} y2={y(tick)} stroke="#333" stroke-width="0.3" />
				<text x={padL - 6} y={y(tick) + 3} text-anchor="end" font-size="9" fill="#888">{Math.round(tick * 100)}%</text>
			{/each}
			{#each rungs as rung, ri}
				<text x={x(ri)} y={h - 10} text-anchor="middle" font-size="11" fill="#aaa">{rung}</text>
			{/each}
			{#each allMedians as m}
				{@const hoverPrefix = hover?.split('=')[0]}
				{@const myPrefix = m.f.split('=')[0]}
				{@const groupActive = hover === null || hover === m.f || (hoverPrefix === myPrefix && m.f.includes('='))}
				{@const exact = hover === m.f}
				{#each m.meds as med, ri}
					{#if med !== null && ri > 0 && m.meds[ri - 1] !== null}
						<line x1={x(ri - 1)} y1={y(m.meds[ri - 1])} x2={x(ri)} y2={y(med)}
							stroke={m.col} stroke-width={exact ? 3.5 : groupActive ? 2.5 : 2}
							opacity={groupActive ? 0.9 : 0.8} />
					{/if}
					{#if med !== null}
						<circle cx={x(ri)} cy={y(med)} r={exact ? 5 : 3.5}
							fill={m.col} opacity={groupActive ? 0.95 : 0.8}
							onmouseenter={() => hover = m.f}
							onmouseleave={() => hover = null}
							style="cursor:default" />
						{#if exact}
							<text x={x(ri)} y={y(med) - 8} text-anchor="middle" font-size="9" fill="#eee">
								{Math.round(med * 100)}%
							</text>
						{/if}
					{/if}
				{/each}
			{/each}
			{#each labelPositions as lp}
				{@const hoverPrefix = hover?.split('=')[0]}
				{@const myPrefix = lp.f.split('=')[0]}
				{@const groupActive = hover === null || hover === lp.f || (hoverPrefix === myPrefix && lp.f.includes('='))}
				{@const exact = hover === lp.f}
				<text x={w - padR + 8} y={lp.ly + 4}
					font-size={exact ? "11" : "10"} fill={lp.col}
					font-weight={exact ? "bold" : groupActive && hover !== null ? "600" : "normal"}
					opacity={groupActive ? 1 : 0.8}
					onmouseenter={() => hover = lp.f}
					onmouseleave={() => hover = null}
					style="cursor:default">
					{lp.f.replace(/=/g, ': ').replace(/_/g, ' ')}
				</text>
			{/each}
		</svg>
		<p class="muted" style="text-align:center;margin:4px 0">median across {Object.keys(data.ladders).length} families · raw frame · hover to highlight</p>
	{:else}
	<div class="legend">
		{#each FIELDS as f}
			<span style="color:{COLORS[f] ?? '#888'};opacity:{hover === null || hover === f ? 1 : 0.3}"
				onmouseenter={() => hover = f}
				onmouseleave={() => hover = null}>
				{f.replace(/_/g, ' ')}
			</span>
		{/each}
	</div>

	<div class="grid">
		{#each families as fam}
			{@const ladder = data.ladders[fam]}
			{@const w = 340}
			{@const h = 200}
			{@const padT = 20}
			{@const padB = 32}
			{@const padL = 36}
			{@const padR = 12}
			{@const x = (i) => padL + (i / (rungs.length - 1)) * (w - padL - padR)}
			{@const y = (v) => padT + (1 - v) * (h - padT - padB)}
			<div class="panel">
				<h4>{fam}
					<span class="muted">n = {ladder.map((r) => r._n).join(' / ')}</span>
				</h4>
				<svg viewBox="0 0 {w} {h}" style="width:100%;display:block">
					{#each [0, 0.25, 0.5, 0.75, 1] as tick}
						<line x1={padL} x2={w - padR} y1={y(tick)} y2={y(tick)} stroke="#333" stroke-width="0.3" />
						<text x={padL - 4} y={y(tick) + 3} text-anchor="end" font-size="7" fill="#666">{Math.round(tick * 100)}%</text>
					{/each}
					{#each rungs as rung, ri}
						<text x={x(ri)} y={h - 8} text-anchor="middle" font-size="8" fill="#888">{rung}</text>
						<text x={x(ri)} y={h - 1} text-anchor="middle" font-size="6" fill="#555">n={ladder[ri]?._n ?? 0}</text>
					{/each}
					{#each FIELDS as f}
						{@const col = COLORS[f] ?? '#888'}
						{@const pts = ladder.map((r, i) => ({ x: x(i), y: y(r[f] ?? 0), v: r[f] ?? 0, n: r._n }))}
						{@const active = hover === null || hover === f}
						{#each pts as pt, pi}
							{#if pi > 0}
								<line x1={pts[pi-1].x} y1={pts[pi-1].y} x2={pt.x} y2={pt.y}
									stroke={col} stroke-width={hover === f ? 2.5 : 1.2}
									opacity={0.8} />
							{/if}
							<circle cx={pt.x} cy={pt.y} r={hover === f ? 4 : 2.5}
								fill={col} opacity={0.85}
								onmouseenter={() => hover = f}
								onmouseleave={() => hover = null}
								style="cursor:default" />
							{#if hover === f}
								<text x={pt.x} y={pt.y - 6} text-anchor="middle" font-size="7" fill="#ddd">
									{Math.round(pt.v * 100)}%
								</text>
							{/if}
						{/each}
					{/each}
				</svg>
			</div>
		{/each}
	</div>
	{/if}
{/if}
