<!--
  Draws a producer's `<name>.data.json` with a LayerChart component.

  THE FILE NAMES ITS OWN CHART TYPE. `art.chart` selects the component, so the
  pairing of data to drawing lives in the repo beside the numbers rather than in
  a filename registry three directories away. A producer that invents a new chart
  type gets a named refusal here rather than a blank panel.

  Nothing in this path renders a PNG. The point of the data artifact is that the
  browser draws it live and reflows on resize; serving an image would defeat it.
-->
<script lang="ts">
	import SlopeGrid from './charts/SlopeGrid.svelte';

	let { url, name }: { url: string; name: string } = $props();

	let art = $state<any>(null);
	let error = $state<string | null>(null);

	$effect(() => {
		const u = url;
		let dead = false;
		art = null;
		error = null;
		(async () => {
			try {
				const r = await fetch(u);
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				const j = await r.json();
				if (!dead) art = j;
			} catch (e) {
				if (!dead) error = e instanceof Error ? e.message : String(e);
			}
		})();
		return () => {
			dead = true;
		};
	});
</script>

{#if error}
	<p class="err">could not load <code>{name}</code>: {error}</p>
{:else if art}
	{#if art.chart === 'slopes'}
		<SlopeGrid {art} />
	{:else}
		<p class="err">
			<code>{name}</code> declares <code>chart: {art.chart}</code>, which this app has no
			component for.
		</p>
	{/if}
	<p class="prov">
		<code>{name}</code>
		<span class="muted">drawn live from the producer's data, {art.rows?.length ?? 0} rows</span>
		<a href={url} target="_blank" rel="noreferrer">open the data</a>
	</p>
{:else}
	<p class="muted">reading…</p>
{/if}

<style>
	.err {
		font-size: 0.85rem;
		color: #b03a2e;
	}
	.prov {
		display: flex;
		gap: 0.75rem;
		align-items: baseline;
		flex-wrap: wrap;
		margin: 0.6rem 0 0;
		font-size: 0.8rem;
	}
	.muted {
		opacity: 0.6;
	}
</style>
