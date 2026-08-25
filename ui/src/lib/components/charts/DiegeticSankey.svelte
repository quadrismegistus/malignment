<!--
  Diegetic superego Sankey: where does the passage go? Base vs aligned.
  Uses d3-sankey directly (no LayerChart Chart wrapper — the Sankey needs
  explicit dimensions and Chart's container-measurement was not resolving).
-->
<script lang="ts">
	import { sankey as d3Sankey, sankeyJustify, sankeyLinkHorizontal } from 'd3-sankey';

	let { art }: { art: any } = $props();

	const W = 500, H = 370;
	const NODE_COLOURS: Record<string, string> = {
		'all passages': '#888',
		'sexual scene': '#c2477f',
		'no sexual scene': '#76b7b2',
		'clean scene': '#59a14f',
		'superego in scene': '#e15759',
		'consent hesitation': '#f28e2b',
		'guilt / shame': '#e15759',
		'moralisation': '#b07aa1',
		'frame exit': '#4e79a7',
		'continues': '#76b7b2',
		'refusal': '#edc948'
	};

	function layout(arm: any) {
		const nodeNames: string[] = arm.nodes;
		const nodeMap: Record<string, number> = {};
		nodeNames.forEach((n: string, i: number) => (nodeMap[n] = i));
		const data = {
			nodes: nodeNames.map((n: string) => ({ name: n })),
			links: arm.links.map((l: any) => ({
				source: nodeMap[l.source],
				target: nodeMap[l.target],
				value: l.value,
				sourceName: l.source,
				targetName: l.target
			}))
		};
		const sk = d3Sankey()
			.nodeWidth(14)
			.nodePadding(14)
			.nodeAlign(sankeyJustify)
			.size([W - 8, H - 8]);
		return sk(data as any);
	}

	let baseLayout = $derived(layout(art.base));
	let alignedLayout = $derived(layout(art.aligned));

	const path = sankeyLinkHorizontal();

	function linkColour(link: any): string {
		return NODE_COLOURS[link.targetName] ?? NODE_COLOURS[link.sourceName] ?? '#ccc';
	}

	let hover = $state<{ arm: string; label: string; value: number; pct: string } | null>(null);
</script>

<figure class="sankey-fig">
	<figcaption>
		<h3>{art.title ?? 'Diegetic superego'}</h3>
		{#if art.subtitle}<p class="sub">{art.subtitle}</p>{/if}
	</figcaption>

	<div class="pair">
		{#each [{ label: 'Base', sk: baseLayout, total: art.base.total, key: 'base' },
		        { label: 'Aligned', sk: alignedLayout, total: art.aligned.total, key: 'aligned' }] as arm}
			<div class="arm">
				<div class="arm-label">{arm.label} <span class="arm-n">({arm.total.toLocaleString()} passages)</span></div>
				<div class="sankey-area">
					<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMidYMid meet">
						<g transform="translate(4, 4)">
							{#each arm.sk.links as link}
								<path
									d={path(link)}
									fill="none"
									stroke={linkColour(link)}
									stroke-opacity={hover && hover.arm === arm.key && hover.label !== link.targetName && hover.label !== link.sourceName ? 0.08 : 0.35}
									stroke-width={Math.max(1, link.width)}
									onmouseenter={() => hover = {
										arm: arm.key,
										label: link.targetName,
										value: link.value,
										pct: (100 * link.value / arm.total).toFixed(1)
									}}
									onmouseleave={() => hover = null}
								/>
							{/each}
							{#each arm.sk.nodes as node}
								<rect
									x={node.x0} y={node.y0}
									width={node.x1 - node.x0}
									height={Math.max(1, node.y1 - node.y0)}
									fill={NODE_COLOURS[node.name] ?? '#888'}
									rx="2"
								/>
								{#if node.y1 - node.y0 > 10}
									<text
										x={node.x0 < W / 2 ? node.x1 + 6 : node.x0 - 6}
										y={(node.y0 + node.y1) / 2 + 4}
										text-anchor={node.x0 < W / 2 ? 'start' : 'end'}
										font-size="10" fill="var(--text-2, #ccc)"
										font-family="-apple-system, BlinkMacSystemFont, sans-serif"
									>{node.name}</text>
								{/if}
							{/each}
						</g>
					</svg>
					{#if hover && hover.arm === arm.key}
						<div class="tip">
							<strong>{hover.label}</strong>: {hover.value.toLocaleString()} ({hover.pct}%)
						</div>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</figure>

<style>
	.sankey-fig { margin: 0; }
	figcaption h3 { margin: 0 0 0.15rem; font-size: 1rem; }
	.sub { margin: 0 0 0.8rem; font-size: 0.8rem; color: var(--text-3); max-width: 100ch; }
	.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
	@media (max-width: 800px) { .pair { grid-template-columns: 1fr; } }
	.arm { min-width: 0; }
	.arm-label {
		text-align: center; font-size: 0.85rem; font-weight: 700;
		color: var(--text-2); margin-bottom: 4px;
	}
	.arm-n { font-weight: 400; color: var(--text-3); font-size: 0.75rem; }
	.sankey-area { position: relative; }
	svg { display: block; width: 100%; }
	.tip {
		position: absolute; bottom: 8px; left: 8px;
		background: var(--panel, #fff); border: 1px solid var(--rule, #ddd);
		border-radius: 5px; padding: 4px 10px; font-size: 0.72rem;
		box-shadow: 0 2px 6px rgba(0,0,0,0.1); pointer-events: none; z-index: 10;
	}
</style>
