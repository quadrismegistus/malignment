<!--
  Plots — pick a registered figure, give it parameters, look at the result.

  ── THE PRODUCERS DECLARE AND THIS READS THE DECLARATION ────────────────────

  Nothing here knows what a `prompt_slopes` is. `/plots` returns the spec each
  `experiments/**/plot.py` publishes as `PLOT`, and the form below is built from
  that spec. Adding a plot type is adding a `PLOT` dict and a `render()` to a
  producer; no change is needed in this file, and there is no second list of
  what the producers accept to drift from what they accept.

  ── WHY THE PROMPT IS A SEARCH AND NOT A TEXT BOX ───────────────────────────

  It looks like a UI nicety and it is a security boundary. A prompt reaches a
  ClickHouse query, and `serve.py`'s rule is that nothing a client sends does —
  so the server validates it by MEMBERSHIP in the set of prompts the store
  actually holds. The search hits `/plot/prompts`, which filters that cached set
  in Python rather than with a `LIKE`, because a substring filter in SQL is
  client text reaching SQL by a politer route.

  It is also better: a prompt with no cells can only ever draw an empty figure,
  and this makes that unreachable rather than disappointing.

  ── THE IMAGE IS THE 300 DPI ARTIFACT ───────────────────────────────────────

  Not a screen rendering that a "save" button would re-make at print quality.
  The panel shows the same PNG a paper would use, scaled by the browser, and
  "open full size" hands over that exact file. One artifact, two consumers —
  because a figure implemented twice is the divergence this repo keeps paying
  for, with a picture on it.
-->
<script lang="ts">
	import { api } from '$lib/api';
	import type { PlotSpec } from '$lib/api';

	let plots = $state<PlotSpec[]>([]);
	let chosen = $state('');
	let values = $state<Record<string, string>>({});
	let running = $state(false);
	let error = $state('');
	let result = $state<{
		url: string;
		figure: string;
		seconds: number;
		info: Record<string, unknown>;
	} | null>(null);

	//: Prompt search state, kept per-render rather than debounced into the
	//: form: the field is a filter over a list, not a value being typed.
	let promptQuery = $state('');
	let promptHits = $state<string[]>([]);
	let promptTotal = $state(0);
	let promptMatched = $state(0);
	let searching = $state(false);
	let promptOpen = $state(false);

	api
		.plots()
		.then((r) => {
			plots = r.plots;
			if (!chosen && plots.length) select(plots[0]);
		})
		.catch((e) => (error = e instanceof Error ? e.message : String(e)));

	let spec = $derived(plots.find((p) => p.id === chosen) ?? null);

	function select(p: PlotSpec) {
		chosen = p.id;
		result = null;
		error = '';
		//: Defaults come from the SPEC, so a producer that changes a default
		//: changes it here without anyone editing this file.
		const v: Record<string, string> = {};
		for (const f of p.params) v[f.name] = f.default != null ? String(f.default) : '';
		values = v;
	}

	let searchTimer: ReturnType<typeof setTimeout> | undefined;
	function searchPrompts(q: string) {
		promptQuery = q;
		promptOpen = true;
		clearTimeout(searchTimer);
		searchTimer = setTimeout(() => {
			searching = true;
			api
				.plotPrompts(q, 40)
				.then((r) => {
					promptHits = r.prompts;
					promptTotal = r.n_total;
					promptMatched = r.n_matched;
				})
				.catch(() => (promptHits = []))
				.finally(() => (searching = false));
		}, 200);
	}

	async function run() {
		if (!spec || running) return;
		running = true;
		error = '';
		try {
			result = await api.plotRender(spec.id, values);
		} catch (e) {
			//: The server's sentence, not a status code. Every refusal in
			//: `serve.py` names what it refused and what it would accept.
			error = e instanceof Error ? e.message : String(e);
			result = null;
		} finally {
			running = false;
		}
	}

	function label(f: PlotSpec['params'][number]) {
		return f.label || f.name;
	}
</script>

<div class="plots">
	<h2>Plots <span class="muted">registered figures, run on demand</span></h2>

	{#if error && !plots.length}
		<p class="bad">{error}</p>
	{/if}

	<!-- Sub-tabs: one per registered plot type. -->
	<div class="tabs">
		{#each plots as p (p.id)}
			<button class="ghost" class:on={chosen === p.id} onclick={() => select(p)} title={p.blurb}>
				{p.name}
				{#if p.error}<span class="tag bad">broken</span>{/if}
			</button>
		{/each}
		{#if !plots.length}
			<span class="muted">no producer declares a PLOT spec yet</span>
		{/if}
	</div>

	{#if spec}
		{#if spec.error}
			<!--
			  A PRODUCER THAT WILL NOT IMPORT IS SHOWN, NOT SKIPPED. A plot missing
			  from the list is indistinguishable from one never written.
			-->
			<p class="bad">this producer failed to import: {spec.error}</p>
		{:else}
			<p class="blurb">{spec.blurb}</p>
			<div class="form">
				{#each spec.params as f (f.name)}
					<div class="field" class:wide={f.type === 'prompt'}>
						<label for="f-{f.name}">{label(f)}{#if f.required}<span class="req">*</span>{/if}</label>
						{#if f.type === 'choice'}
							<select id="f-{f.name}" bind:value={values[f.name]}>
								{#each f.choices ?? [] as c (c)}<option value={c}>{c}</option>{/each}
							</select>
						{:else if f.type === 'int'}
							<input
								id="f-{f.name}"
								type="number"
								min={f.min}
								max={f.max}
								bind:value={values[f.name]}
							/>
						{:else if f.type === 'prompt'}
							<div class="combo">
								<input
									id="f-{f.name}"
									placeholder="type to search the prompts the store holds"
									value={values[f.name] || promptQuery}
									oninput={(e) => searchPrompts((e.currentTarget as HTMLInputElement).value)}
									onfocus={() => (promptOpen = true)}
								/>
								{#if promptOpen && (promptHits.length || searching)}
									<div class="hits">
										{#if searching}<div class="muted hit">searching…</div>{/if}
										{#each promptHits as h (h)}
											<button
												class="hit"
												onclick={() => {
													values[f.name] = h;
													promptQuery = h;
													promptOpen = false;
												}}>{h}</button
											>
										{/each}
										{#if promptMatched > promptHits.length}
											<!--
											  A COUNT OF WHAT WAS DRAWN, NOT OF WHAT MATCHED. The list
											  is capped and says so, because a capped list that does
											  not is read as the whole answer.
											-->
											<div class="muted hit">
												showing {promptHits.length} of {promptMatched} matches ({promptTotal} prompts
												in the store)
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{:else}
							<input id="f-{f.name}" bind:value={values[f.name]} placeholder={f.help ?? ''} />
						{/if}
						{#if f.help}<span class="help">{f.help}</span>{/if}
					</div>
				{/each}
			</div>

			<div class="actions">
				<button class="ghost go" onclick={run} disabled={running}>
					{running ? 'drawing…' : 'draw'}
				</button>
				{#if result}
					<span class="muted">{result.seconds}s · {result.figure}</span>
				{/if}
			</div>

			{#if error}<p class="bad">{error}</p>{/if}

			{#if result}
				<!--
				  THE RUN'S OWN NUMBERS, beside the picture rather than only inside
				  it. `n_units` against `n_units_requested` is the one a reader most
				  needs: a lineage missing a rung is dropped, and a figure drawn over
				  40 of 50 units looks exactly like one drawn over 50.
				-->
				<div class="info">
					{#each Object.entries(result.info) as [k, v] (k)}
						{#if v != null && typeof v !== 'object'}
							<span class="kv"><b>{k}</b> {v}</span>
						{/if}
					{/each}
				</div>
				<figure class="fig">
					<img src={result.url} alt={result.figure} />
					<figcaption>
						<code>{result.figure}</code>
						<a href={result.url} target="_blank" rel="noreferrer">open full size (300 dpi)</a>
						<span class="muted">saved to the producer's figures/ folder</span>
					</figcaption>
				</figure>
			{/if}
		{/if}
	{/if}
</div>

<style>
	.plots { max-width: none; }
	h2 { font-size: 15px; margin: 0 0 4px; font-weight: 600; }
	h2 .muted { font-weight: 400; font-size: 12px; }
	.muted { color: var(--text-2); }
	.bad { color: var(--bad, #c92a2a); font-size: 12px; }
	.blurb { color: var(--text-2); font-size: 12px; margin: 6px 0 10px; max-width: 90ch; }
	.tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0 2px; }
	.form { display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-start; margin: 8px 0; }
	.field { display: flex; flex-direction: column; gap: 3px; min-width: 130px; }
	.field.wide { flex: 1 1 420px; }
	.field label { font-size: 11px; color: var(--text-2); }
	.req { color: var(--bad, #c92a2a); margin-left: 2px; }
	.field input, .field select {
		padding: 5px 8px; background: var(--panel); border: 1px solid var(--rule);
		border-radius: 4px; color: var(--text); font-family: inherit; font-size: 12px;
	}
	.help { font-size: 10px; color: var(--text-2); max-width: 46ch; line-height: 1.35; }
	.combo { position: relative; }
	.combo input { width: 100%; }
	.hits {
		position: absolute; z-index: 20; top: 100%; left: 0; right: 0; max-height: 260px;
		overflow-y: auto; background: var(--panel); border: 1px solid var(--rule);
		border-radius: 4px; margin-top: 2px;
	}
	.hit {
		display: block; width: 100%; text-align: left; padding: 5px 8px; border: 0;
		background: none; color: var(--text); font-family: var(--mono); font-size: 11px;
		cursor: pointer;
	}
	.hit:hover { background: var(--rule); }
	.actions { display: flex; align-items: center; gap: 12px; margin: 6px 0 2px; }
	.info { display: flex; gap: 14px; flex-wrap: wrap; margin: 10px 0 4px; font-size: 11px; }
	.kv b { color: var(--text-2); font-weight: 500; margin-right: 4px; }
	.fig { margin: 6px 0 24px; }
	.fig img {
		width: 100%; height: auto; display: block; background: #fff;
		border: 1px solid var(--rule); border-radius: 4px;
	}
	.fig figcaption {
		display: flex; gap: 14px; align-items: center; margin-top: 6px;
		font-size: 11px; color: var(--text-2);
	}
</style>
