<!--
  Renders a Vega-Lite spec written into an experiment's `figures/` folder.

  THE SPEC AND THE 300 DPI PNG BESIDE IT COME FROM ONE DICT. `plot.py` builds a
  spec, writes it as `<name>.vl.json`, and renders THAT SAME OBJECT through
  `vl_convert` to the PNG a paper would use. So this component is not a second
  drawing of the figure and cannot disagree with the printed one; it is the same
  figure with an interaction layer and live text.

  WHICH FIGURES ARE SPECS IS THE SERVER'S ANSWER, not this component's. The
  manifest carries a `specs` list; nothing here parses a filename to decide how
  to render a file.

  Actions are off except zoom and the source link. `vega-embed`'s default menu
  offers PNG and SVG export, and a reader who took the export would get a
  screen-resolution image of a figure whose print version is already on disk at
  300 dpi -- two artifacts of the same figure at different quality, with the
  worse one easier to reach.
-->
<script lang="ts">
	import embed, { type VisualizationSpec, type Result } from 'vega-embed';

	let { url, name }: { url: string; name: string } = $props();

	let host = $state<HTMLDivElement | null>(null);
	let error = $state<string | null>(null);
	let view = $state<Result | null>(null);

	//: THE FETCH AND THE EMBED ARE ONE EFFECT because they share a lifetime: a
	//: `url` change has to abandon an in-flight response as well as tear down the
	//: previous view, and splitting them lets a slow first response paint over a
	//: fast second one.
	$effect(() => {
		const u = url;
		const el = host;
		if (!el) return;
		let dead = false;
		error = null;
		(async () => {
			try {
				const r = await fetch(u);
				if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
				const spec = (await r.json()) as VisualizationSpec;
				if (dead) return;
				const res = await embed(el, spec, {
					actions: { export: false, source: true, compiled: false, editor: false },
					renderer: 'canvas',
					//: The spec sets its own widths. Letting the container override
					//: them would rescale the two panels of a two-panel figure
					//: independently, and at least one figure here exists precisely
					//: because both panels share one x domain.
					width: undefined,
					height: undefined
				});
				if (dead) {
					res.finalize();
					return;
				}
				view = res;
			} catch (e) {
				if (!dead) error = e instanceof Error ? e.message : String(e);
			}
		})();
		return () => {
			dead = true;
			view?.finalize();
			view = null;
		};
	});
</script>

<figure class="vega">
	{#if error}
		<p class="err">
			could not render <code>{name}</code>: {error}
		</p>
	{/if}
	<div bind:this={host} class="host"></div>
	<figcaption>
		<code>{name}</code>
		<span class="muted">Vega-Lite spec, rendered live</span>
		<a href={url} target="_blank" rel="noreferrer">open the spec</a>
	</figcaption>
</figure>

<style>
	.vega {
		margin: 0;
	}
	.host {
		overflow-x: auto;
	}
	figcaption {
		display: flex;
		gap: 0.75rem;
		align-items: baseline;
		flex-wrap: wrap;
		margin-top: 0.5rem;
		font-size: 0.8rem;
	}
	.muted {
		opacity: 0.6;
	}
	.err {
		font-size: 0.85rem;
		color: #b03a2e;
	}
</style>
