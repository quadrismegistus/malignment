<!--
  Generate — sample continuations from a resident model.

  Uses the same `_SLOT_MODELS` residency as /slot, so a model loaded here is
  reused by Slot and vice versa. Generation blocks while the model runs
  (HF `model.generate` is synchronous); the UI shows a spinner.

  **MPS CONSTRAINTS ENFORCED SERVER-SIDE.** `top_p` is pinned to 1.0 and
  `top_k` to 0. The controls are shown disabled with an explanation.
-->
<script lang="ts">
	import { api } from '$lib/api';
	import type { GenerateResult } from '$lib/api';

	let models = $state<string[]>([]);
	let modelsLoading = $state(true);
	api.roster().then((r) => {
		const all = new Set<string>();
		for (const ep of r.endpoints) {
			all.add(ep.base);
			all.add(ep.endpoint);
		}
		models = [...all].sort();
		modelsLoading = false;
	}).catch(() => { modelsLoading = false; });

	let model = $state('');
	let prompt = $state('She slowly took off her');
	let frame = $state<'raw' | 'chat' | 'continue' | 'system'>('raw');
	let systemPrompt = $state('');
	let prefill = $state(false);
	let userMsg = $state('Hi.');
	let temperature = $state(1.0);
	let maxTokens = $state(256);
	let nSamples = $state(1);
	let seed = $state<string>('');

	let results = $state<GenerateResult[]>([]);
	let generating = $state(false);
	let error = $state('');
	let elapsed = $state(0);
	let slotLoaded = $state<string[]>([]);

	api.health().then((h) => {
		slotLoaded = h.slot_loaded;
		if (!model && h.slot_loaded.length > 0) {
			model = h.slot_loaded[h.slot_loaded.length - 1];
		}
	}).catch(() => {});

	function modelShort(m: string) {
		return m.split('/').pop() || m;
	}

	async function generate() {
		if (!model || !prompt.trim()) return;
		generating = true;
		error = '';
		results = [];
		const t0 = performance.now();
		try {
			const body: Record<string, unknown> = {
				model,
				prompt: prompt.trim(),
				frame,
				n: nSamples,
				decoder: { temperature, max_new_tokens: maxTokens },
			};
			if (frame === 'system' && systemPrompt.trim()) {
				body.system = systemPrompt.trim();
			}
			if (prefill) {
				body.prefill = true;
				body.user_msg = userMsg;
			}
			if (seed.trim()) {
				body.seed = parseInt(seed.trim(), 10);
			}
			const resp = await api.generate(body as any);
			results = resp.results;
			elapsed = Math.round(performance.now() - t0);
			api.health().then((h) => { slotLoaded = h.slot_loaded; }).catch(() => {});
		} catch (e: any) {
			error = e.message || String(e);
		} finally {
			generating = false;
		}
	}

	function finishLabel(f: string) {
		if (f === 'length') return 'max tokens';
		if (f === 'eos') return 'end of sequence';
		return f;
	}
</script>

<div class="gen-wrap">
	<div class="controls">
		<div class="row">
			<label>
				<span class="lbl">Model</span>
				<select bind:value={model} disabled={modelsLoading}>
					{#if modelsLoading}
						<option value="">Loading roster...</option>
					{:else if models.length === 0}
						<option value="">No models available</option>
					{:else}
						<option value="">Select a model</option>
						{#each models as m (m)}
							<option value={m}>
								{modelShort(m)}{slotLoaded.includes(m) ? ' (resident)' : ''}
							</option>
						{/each}
					{/if}
				</select>
			</label>
		</div>

		{#if slotLoaded.length > 0}
			<div class="resident">
				Resident: {slotLoaded.map(modelShort).join(', ')}
			</div>
		{/if}

		<div class="row">
			<label class="full">
				<span class="lbl">Prompt</span>
				<textarea bind:value={prompt} rows={3} placeholder="The text to continue or frame"></textarea>
			</label>
		</div>

		<div class="row three">
			<label>
				<span class="lbl">Frame</span>
				<select bind:value={frame}>
					<option value="raw">raw (bare stem)</option>
					<option value="chat">chat (template default)</option>
					<option value="continue">continue (user turn)</option>
					<option value="system">system (system + user)</option>
				</select>
			</label>
			<label>
				<span class="lbl">Temperature</span>
				<input type="number" bind:value={temperature} min={0.01} max={2} step={0.05} />
			</label>
			<label>
				<span class="lbl">Max tokens</span>
				<input type="number" bind:value={maxTokens} min={1} max={2048} step={16} />
			</label>
		</div>

		{#if frame === 'system'}
			<div class="row">
				<label class="full">
					<span class="lbl">System prompt</span>
					<textarea bind:value={systemPrompt} rows={2} placeholder="System message (leave empty for vendor default)"></textarea>
				</label>
			</div>
		{/if}

		<div class="row three">
			<label class="checkbox-row">
				<input type="checkbox" bind:checked={prefill} />
				<span class="lbl">Prefill (stem in assistant turn)</span>
			</label>
			{#if prefill}
				<label>
					<span class="lbl">User message</span>
					<input type="text" bind:value={userMsg} placeholder="Hi." />
				</label>
			{/if}
			<label>
				<span class="lbl">Samples</span>
				<input type="number" bind:value={nSamples} min={1} max={8} />
			</label>
			<label>
				<span class="lbl">Seed (optional)</span>
				<input type="text" bind:value={seed} placeholder="none" />
			</label>
		</div>

		<div class="row mps-note">
			<code>top_p</code> pinned to 1.0, <code>top_k</code> disabled — MPS sampling defect
		</div>

		<div class="row">
			<button class="ghost" onclick={generate} disabled={generating || !model || !prompt.trim()}>
				{#if generating}
					Generating...
				{:else}
					Generate{model && slotLoaded.includes(model) ? '' : ' (will load model)'}
				{/if}
			</button>
		</div>
	</div>

	{#if generating}
		<div class="spinner-wrap">
			<div class="spinner"></div>
			<span>{model && slotLoaded.includes(model) ? 'Generating' : 'Loading model and generating'} ({nSamples} sample{nSamples > 1 ? 's' : ''}, up to {maxTokens} tokens each)...</span>
		</div>
	{/if}

	{#if error}
		<div class="declare warn">{error}</div>
	{/if}

	{#if results.length > 0}
		<div class="meta">
			{results.length} result{results.length > 1 ? 's' : ''} in {(elapsed / 1000).toFixed(1)}s
			— {modelShort(results[0].model)}, frame={results[0].frame}, temp={results[0].decoder?.temperature}
		</div>
		{#each results as r, i (i)}
			<div class="result">
				{#if results.length > 1}
					<div class="result-head">Sample {i + 1}</div>
				{/if}
				<pre class="result-body"><span class="prompt-echo">{r.prompt}</span><span class="completion">{r.text}</span></pre>
				<div class="result-foot">
					{r.n_new_tokens} tokens, {finishLabel(r.finish)}{r.seed != null ? `, seed ${r.seed}` : ''}
				</div>
			</div>
		{/each}
	{/if}
</div>

<style>
	.gen-wrap {
		max-width: 900px;
	}
	.controls {
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-bottom: 16px;
	}
	.row {
		display: flex;
		gap: 12px;
		align-items: flex-end;
	}
	.row.three {
		flex-wrap: wrap;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 3px;
		min-width: 120px;
	}
	.lbl {
		font-size: 11px;
		color: var(--text-3);
	}
	label.full {
		flex: 1;
		min-width: 100%;
	}
	.checkbox-row {
		flex-direction: row;
		align-items: center;
		gap: 6px;
		padding-top: 16px;
	}
	select {
		max-width: 400px;
	}
	textarea {
		font-family: var(--mono);
		font-size: 13px;
		resize: vertical;
	}
	input[type="number"] {
		width: 90px;
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
	}
	.resident {
		font-size: 11px;
		color: var(--text-3);
	}
	.mps-note {
		font-size: 11px;
		color: var(--text-3);
	}
	.mps-note code {
		font-family: var(--mono);
		color: var(--text-2);
	}
	.spinner-wrap {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 16px 0;
		color: var(--text-3);
		font-size: 13px;
	}
	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid var(--rule);
		border-top-color: var(--blue);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	.meta {
		font-size: 12px;
		color: var(--text-3);
		margin-bottom: 8px;
		font-family: var(--mono);
	}
	.result {
		border: 1px solid var(--rule);
		border-radius: 4px;
		margin-bottom: 8px;
		overflow: hidden;
	}
	.result-head {
		background: var(--panel-2);
		padding: 4px 10px;
		font-size: 11px;
		color: var(--text-3);
		border-bottom: 1px solid var(--rule-soft);
	}
	.result-body {
		padding: 10px 12px;
		font-family: var(--mono);
		font-size: 13px;
		line-height: 1.6;
		white-space: pre-wrap;
		word-break: break-word;
		margin: 0;
		background: var(--panel);
		color: var(--text);
	}
	.prompt-echo {
		color: var(--text-3);
	}
	.completion {
		color: var(--text);
		border-left: 2px solid var(--blue);
		padding-left: 0;
		margin-left: 1px;
	}
	.result-foot {
		background: var(--panel-2);
		padding: 4px 10px;
		font-size: 11px;
		color: var(--text-3);
		border-top: 1px solid var(--rule-soft);
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
	}
</style>
