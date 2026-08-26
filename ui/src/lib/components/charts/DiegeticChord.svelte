<!--
  Directed chord diagram of tag-to-tag transitions, base vs aligned.
  Uses d3-chord directly (Chart wrapper doesn't resolve dimensions reliably in headless).
-->
<script lang="ts">
	import { chordDirected, ribbon as d3Ribbon } from 'd3-chord';
	import { arc as d3Arc } from 'd3-shape';
	import { descending } from 'd3-array';

	let { art }: { art: any } = $props();

	let tags: string[] = $derived(art.tags ?? []);
	let colours: string[] = $derived(art.colours ?? []);

	const SIZE = 380;
	const OUTER = SIZE / 2 - 30;
	const INNER = OUTER * 0.88;
	const CX = SIZE / 2;

	function layout(matrix: number[][]) {
		const chord = chordDirected().padAngle(0.06).sortSubgroups(descending);
		return chord(matrix);
	}

	let baseChords = $derived(layout(art.base.matrix));
	let alignedChords = $derived(layout(art.aligned.matrix));

	const groupArc = d3Arc<any>().innerRadius(INNER).outerRadius(OUTER);
	const ribbonPath = d3Ribbon<any, any>().radius(INNER);

	let hover = $state<{ arm: string; from: string; to: string; value: number; pct: string } | null>(null);
</script>

<figure class="chord-fig">
	<figcaption>
		<h3>{art.title ?? 'Chord diagram'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="pair">
		{#each [{ label: 'Base', chords: baseChords, data: art.base, key: 'base' },
		        { label: 'Aligned', chords: alignedChords, data: art.aligned, key: 'aligned' }] as arm}
			<div class="arm">
				<div class="arm-label">{arm.label} <span class="arm-n">({arm.data.total.toLocaleString()} transitions)</span></div>
				<div class="chord-area">
					<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" preserveAspectRatio="xMidYMid meet">
						<g transform="translate({CX},{CX})">
							<!-- group arcs -->
							{#each arm.chords.groups as group}
								<path
									d={groupArc(group)}
									fill={colours[group.index] ?? '#888'}
									stroke="#222" stroke-width="0.5"
								/>
								<!-- label -->
								{@const angle = (group.startAngle + group.endAngle) / 2}
								{@const labelR = OUTER + 8}
								{@const flip = angle > Math.PI}
								<text
									transform="rotate({(angle * 180 / Math.PI) - 90}) translate({labelR},0){flip ? ' rotate(180)' : ''}"
									text-anchor={flip ? 'end' : 'start'}
									font-size="10"
									fill="var(--text-2, #ccc)"
									dy="0.35em"
									font-family="-apple-system, BlinkMacSystemFont, sans-serif"
								>{tags[group.index]}</text>
							{/each}
							<!-- ribbons -->
							{#each arm.chords as chord}
								{@const fromTag = tags[chord.source.index]}
								{@const toTag = tags[chord.target.index]}
								{@const dimmed = hover && hover.arm === arm.key &&
									hover.from !== fromTag && hover.to !== toTag &&
									hover.from !== toTag && hover.to !== fromTag}
								<path
									d={ribbonPath(chord)}
									fill={colours[chord.source.index] ?? '#888'}
									opacity={dimmed ? 0.04 : 0.55}
									stroke="none"
									onmouseenter={() => {
										const val = arm.data.matrix[chord.source.index][chord.target.index];
										hover = {
											arm: arm.key,
											from: fromTag,
											to: toTag,
											value: val,
											pct: (100 * val / arm.data.total).toFixed(1)
										};
									}}
									onmouseleave={() => hover = null}
								/>
							{/each}
						</g>
					</svg>
					{#if hover && hover.arm === arm.key}
						<div class="tip">
							{#if hover.from === hover.to}
								<strong>{hover.from} only</strong> (no other tag): {hover.value.toLocaleString()} ({hover.pct}%)
							{:else}
								<strong>{hover.from} → {hover.to}</strong>: {hover.value.toLocaleString()} ({hover.pct}%)
							{/if}
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>

	<div class="legend">
		{#each tags as tag, i}
			<span class="leg"><i style:background={colours[i]}></i>{tag}</span>
		{/each}
	</div>
</figure>

<style>
	.chord-fig { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub { margin: 0 0 0.8rem; font-size: 0.8rem; color: var(--text-3); max-width: 100ch; }
	.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
	@media (max-width: 800px) { .pair { grid-template-columns: 1fr; } }
	.arm { min-width: 0; }
	.arm-label {
		text-align: center; font-size: 0.85rem; font-weight: 700;
		color: var(--text-2); margin-bottom: 2px;
	}
	.arm-n { font-weight: 400; color: var(--text-3); font-size: 0.75rem; }
	.chord-area { position: relative; }
	svg { display: block; width: 100%; }
	.tip {
		position: absolute; bottom: 8px; left: 8px;
		background: var(--panel, #fff); border: 1px solid var(--rule, #ddd);
		border-radius: 5px; padding: 4px 10px; font-size: 0.75rem;
		box-shadow: 0 2px 6px rgba(0,0,0,0.1); pointer-events: none; z-index: 10;
	}
	.legend {
		display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem;
		margin-top: 0.6rem; font-size: 0.75rem; color: var(--text-3);
	}
	.leg { display: flex; align-items: center; gap: 4px; }
	.leg i { display: inline-block; width: 12px; height: 12px; border-radius: 2px; }
</style>
