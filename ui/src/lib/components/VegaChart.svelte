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
					//: SVG, NOT CANVAS, SO THE FIGURE CAN BE SCALED TO FIT.
					//: Vega-Lite's responsive `width: "container"` does not apply to
					//: FACETED specs, and these are faceted, so the spec keeps its
					//: own size and the CSS below fits it to the panel. A canvas
					//: scales to mush; an SVG scales losslessly and keeps its text
					//: selectable, which also makes the caption searchable.
					renderer: 'svg',
					//: The spec sets its own widths and the container must not
					//: override them: at least one figure here exists precisely
					//: because two panels share one x domain, and independent
					//: rescaling would destroy it. Scaling the whole rendered SVG
					//: uniformly, as the stylesheet does, preserves every ratio.
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
	/*
	  FIT THE RENDERED SVG TO THE PANEL, PRESERVING ASPECT. The slopegraph is
	  2,754 x 3,254 at 300 dpi and renders around 1,100 CSS px wide, against a
	  panel of roughly 770 -- so it overflowed on the right and ran far past the
	  fold. Scaling the whole SVG uniformly keeps every panel's y-units-per-pixel
	  identical to every other's, which is the property the figure is built on.
	*/
	.host {
		overflow-x: auto;
	}
	.host :global(svg) {
		max-width: 100%;
		height: auto;
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
