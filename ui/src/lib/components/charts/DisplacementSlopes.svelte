<!--
  Slopegraph: mean probability by kind, base vs aligned.
  One line per lineage, colored by kind. Raw SVG inside a sized container.
-->
<script lang="ts">
	let { art: data }: { art: any } = $props();
	let hover = $state<string | null>(null);

	const KINDS: Record<string, string> = {
		SEXUAL: '#c44e52', VIOLENT: '#e15759', DEGRADING: '#f28e2b',
		COERCIVE: '#b07aa1', ILLICIT: '#9c755f', NONE: '#76b7b2', OTHER: '#888'
	};

	const W = 600, H = 400;
	const padL = 60, padR = 30, padT = 16, padB = 30;
	const x0 = padL, x1 = W - padR;

	let maxP = $derived(Math.max(...(data?.slopes ?? []).map((s: any) => Math.max(s.p_base, s.p_aligned)), 0.001));
	let y = $derived((v: number) => padT + (1 - v / (maxP * 1.05)) * (H - padT - padB));

	let yTicks = $derived.by(() => {
		const top = maxP * 1.05;
		const raw = top / 6;
		const mag = Math.pow(10, Math.floor(Math.log10(raw)));
		const step = [1, 2, 5, 10].map((m) => m * mag).find((c) => c >= raw) ?? raw;
		const ticks = [];
		for (let t = 0; t <= top; t += step) ticks.push(t);
		return ticks;
	});
</script>

{#if data?.slopes?.length}
	<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:700px;display:block;margin:8px 0">
		{#each yTicks as tick}
			<line x1={x0} x2={x1} y1={y(tick)} y2={y(tick)} stroke="#333" stroke-width="0.3" />
			<text x={x0 - 6} y={y(tick) + 3} text-anchor="end" font-size="8" fill="#888">{tick.toFixed(3)}</text>
		{/each}
		<text x={x0} y={H - 6} font-size="10" fill="#888">base</text>
		<text x={x1} y={H - 6} font-size="10" fill="#888" text-anchor="end">aligned</text>
		{#each data.kinds as kind}
			{#each data.slopes.filter((s) => s.kind === kind) as s (s.lineage)}
				<line
					x1={x0} y1={y(s.p_base)} x2={x1} y2={y(s.p_aligned)}
					stroke={KINDS[kind] ?? '#888'}
					stroke-width={hover === kind ? 2.2 : 0.7}
					opacity={hover === null ? 0.4 : hover === kind ? 0.75 : 0.03}
					onmouseenter={() => hover = kind}
					onmouseleave={() => hover = null}
					style="cursor:default"
				/>
			{/each}
		{/each}
		{#each data.kinds as kind}
			{@const slopes = data.slopes.filter((s) => s.kind === kind)}
			{@const meanBase = slopes.reduce((a, s) => a + s.p_base, 0) / slopes.length}
			{@const meanAligned = slopes.reduce((a, s) => a + s.p_aligned, 0) / slopes.length}
			{#if hover === kind || hover === null}
				<text x={x1 + 6} y={y(meanAligned) + 3} font-size="9"
					fill={KINDS[kind] ?? '#888'}
					opacity={hover === null ? 0.7 : hover === kind ? 1 : 0.15}>
					{kind.toLowerCase()}
				</text>
			{/if}
		{/each}
	</svg>

	<p class="muted small" style="margin:4px 0;font-size:11px">
		{#each data.kinds as k}
			<span style="color:{KINDS[k] ?? '#888'};cursor:default"
				onmouseenter={() => hover = k}
				onmouseleave={() => hover = null}>
				{k.toLowerCase()}
			</span>{' '}
		{/each}
		· {data.n_lineages} lineages · 1 line per (kind, lineage)
	</p>
{:else}
	<p class="muted">No slope data.</p>
{/if}
