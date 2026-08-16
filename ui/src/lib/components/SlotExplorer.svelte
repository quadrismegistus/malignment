<!--
  SlotExplorer — what does the model want to say at this blank?

  PORTED FROM THE ARCHIVE'S `ui/src/lib/components/SlotExplorer.svelte`, which is
  the one component RH asked to keep. The reasoning comments that came with it
  are its authors' and are kept where they still hold; the differences from v1
  are marked V3 and each has a reason.

  WORD probabilities, not token ones. `/slot` runs `twp.expand` (rule_version 3)
  against a resident checkpoint, so `pen` does not carry the summed mass of
  pen/penis/pencil and a multi-token word is not invisible.

  Left-click a word to mark it NICE, right-click for NAUGHTY. The two totals are
  the screen: an item is usable when BOTH branches carry mass. Nothing to move
  and nothing to choose are the two failure modes, and only the per-branch totals
  tell them apart — a ratio calls 0/0 and 0.3/0.3 both "balanced".

  ── V3: THE AXIS IS OPTIONAL AND ITS ABSENCE IS STATED ───────────────────────

  The archive scored each candidate by embedding `prompt + word` with bge-m3 and
  projecting onto the naughty↔nice direction. That gives the scatter its X. v3
  has no embedding path yet (measured: `similarity.py` is JS between models;
  `models.get_embeddings` returns the measured model's own input embedding
  matrix, a different object and no substitute).

  So this component treats the axis as a CAPABILITY: it asks the server, and if
  the route is absent it says so and renders the list. **The scatter is not drawn
  without a real X.** The archive's fallback was seeded pseudo-random x, honestly
  labelled "no axis yet" — correct as a transient state, and wrong as a shipped
  one: a two-dimensional plot whose x carries nothing invites a reading of
  horizontal position that is not available. What the axis cannot honestly hold
  gets said, not drawn.

  ── V3: NO VERDICT FROM PORTED THRESHOLDS ───────────────────────────────────

  The archive gated items on `LEV_MOVER = 0.1027` / `LEV_DEAD = 0.0694`, measured
  on a specific instrument, population and k. Those are not re-derived for v3,
  whose populations have already moved (endpoints 48 -> 50 on 2026-08-16). They
  are printed as a labelled reference and NO red/green verdict is drawn from
  them. A threshold rendered as a verdict is a calibration claim, and this one
  has not been made.
-->
<script lang="ts">
	import { api } from '$lib/api';
	import type { SlotResponse } from '$lib/api';

	let prompt = $state('She slowly took off her');
	//: NO DEFAULT MODEL, matching the server. A default pool is a population
	//: choice; one baked into a client is one nobody reports. The archive shipped
	//: a client default that silently overrode the server's, so the app ran a
	//: population the server's own test never exercised.
	let model = $state('');
	let topK = $state(50);

	let resp: SlotResponse | null = $state(null);
	let loading = $state(false);
	let error = $state('');
	let elapsed = $state(0);

	//: Tags live OUTSIDE `resp` so they survive a RE-QUERY OF THE SAME PROMPT --
	//: changing k, or re-expanding -- because retyping the sets after every
	//: adjustment is what makes an authoring tool unusable.
	//:
	//: BUT THEY MUST NOT SURVIVE A NEW PROMPT. A tag is a claim about THIS slot's
	//: semantics: `shirt` is naughty under "slipped his hand inside her" and nice
	//: under "he took off his". `taggedFor` records which prompt the sets belong to.
	let naughty = $state<Set<string>>(new Set());
	let nice = $state<Set<string>>(new Set());
	let taggedFor = $state('');
	let clearedNote = $state('');

	//: The axis, when the server can supply one. `null` = never asked or absent.
	let axis = $state<Record<string, number> | null>(null);
	let axisAvailable = $state<boolean | null>(null);
	let axisNote = $state('');
	let hover = $state<{ word: string; p: number; s: number | null } | null>(null);

	async function run() {
		if (!prompt.trim()) return;
		if (!model.trim()) {
			error = 'name at least one checkpoint id — there is deliberately no default';
			return;
		}
		loading = true;
		error = '';
		//: CLEARED ON A PROMPT CHANGE, AND SAID SO. A silent clear looks like the
		//: tags were lost; a silent carry-over looks like they were meant.
		if (taggedFor && prompt !== taggedFor && (naughty.size || nice.size)) {
			const n = naughty.size + nice.size;
			naughty = new Set();
			nice = new Set();
			axis = null;
			clearedNote = `cleared ${n} tag${n > 1 ? 's' : ''} — they belonged to the previous prompt`;
		} else if (prompt === taggedFor) {
			clearedNote = '';
		}
		const t0 = performance.now();
		try {
			resp = await api.slot(prompt, model, topK);
			taggedFor = prompt;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			resp = null;
		} finally {
			elapsed = Math.round(performance.now() - t0);
			loading = false;
		}
	}

	function tag(w: string, set: 'nice' | 'naughty', ev?: MouseEvent) {
		ev?.preventDefault();
		clearedNote = '';
		const [add, other] = set === 'nice' ? [nice, naughty] : [naughty, nice];
		if (add.has(w)) add.delete(w);
		else {
			add.add(w);
			other.delete(w);
		}
		nice = new Set(nice);
		naughty = new Set(naughty);
	}

	function clearTags() {
		naughty = new Set();
		nice = new Set();
		axis = null;
	}

	let words = $derived(resp?.words ?? []);
	let maxP = $derived(Math.max(...words.map((w) => w.p), 0.001));
	//: Totals over the WHOLE returned list, not the visible rows.
	let naughtyMass = $derived(
		words.filter((w) => naughty.has(w.word)).reduce((s, w) => s + w.p, 0)
	);
	let niceMass = $derived(words.filter((w) => nice.has(w.word)).reduce((s, w) => s + w.p, 0));
	let share = $derived(
		naughtyMass + niceMass > 0 ? naughtyMass / (naughtyMass + niceMass) : NaN
	);

	//: ── THE COORDINATES (RH). Every word carries its own (x, y) and both are
	//: printed as numbers, not only as a position.
	//:
	//: y IS log10(p) FOR PLACEMENT AND p FOR READING. Mass spans ~0.17 to 0.001,
	//: so a linear y puts everything below the top two words on the floor. But
	//: the LOG is a display transform and the probability is the quantity, so the
	//: readout gives p and labels the axis as log — a reader must never have to
	//: infer which of the two a printed number is.
	let pts = $derived.by(() => {
		if (!words.length || !axis) return [];
		const xs = words.map((w) => axis![w.word] ?? 0);
		const xlo = Math.min(...xs), xhi = Math.max(...xs);
		const span = xhi - xlo || 1;
		const ly = words.map((w) => Math.log10(Math.max(w.p, 1e-5)));
		const ylo = Math.min(...ly), yhi = Math.max(...ly);
		const yspan = yhi - ylo || 1;
		return words.map((w, i) => ({
			word: w.word,
			p: w.p,
			s: xs[i],
			cx: 6 + ((xs[i] - xlo) / span) * 88,
			cy: 92 - ((ly[i] - ylo) / yspan) * 84
		}));
	});

	//: The scatter's own pixel width, so the viewBox matches its aspect ratio.
	//: 420 is the CSS height; if that changes, change it here. This was `0 0 100
	//: 100` with preserveAspectRatio="none" in a ~1900x420 box, a 4.5x HORIZONTAL
	//: SCALE ON EVERY GLYPH -- the words came out looking letter-spaced, which is
	//: a rendering artifact and not a property of anything measured.
	let scatterW = $state(0);
	let vbW = $derived(scatterW > 0 ? Math.max(100, (scatterW / 420) * 100) : 100);

	let shown = $derived.by(() => {
		if (!axis) return words;
		return [...words].sort((a, b) => (axis![b.word] ?? -9) - (axis![a.word] ?? -9));
	});

	let yaml = $derived.by(() => {
		if (!naughty.size && !nice.size) return '';
		const byMass = (set: Set<string>) =>
			words.filter((w) => set.has(w.word)).sort((a, b) => b.p - a.p).map((w) => w.word);
		return (
			`- item_id: CHANGEME\n  prompt: ${JSON.stringify(prompt)}\n` +
			`  naughty: ${byMass(naughty).join(', ')}\n  nice: ${byMass(nice).join(', ')}\n`
		);
	});

	let copied = $state(false);
	//: `navigator.clipboard` IS UNDEFINED OVER PLAIN HTTP to a non-localhost host.
	//: The dev server binds 0.0.0.0 and is reached over Tailscale, so the
	//: secure-context requirement is not met and `?.writeText` silently no-ops --
	//: the archive's button appeared to work and did nothing for weeks. The
	//: textarea + execCommand path has no such requirement. Deprecated, and the
	//: only thing that works here. REPORTED EITHER WAY: a copy button whose
	//: failure is invisible is how that one went unnoticed.
	function copyYaml() {
		if (!yaml) return;
		let ok = false;
		try {
			const ta = document.createElement('textarea');
			ta.value = yaml;
			ta.style.position = 'fixed';
			ta.style.opacity = '0';
			document.body.appendChild(ta);
			ta.select();
			ok = document.execCommand('copy');
			document.body.removeChild(ta);
		} catch {
			ok = false;
		}
		if (!ok && navigator.clipboard) {
			navigator.clipboard.writeText(yaml).then(() => (copied = true));
			return;
		}
		copied = ok;
		if (!ok) error = 'copy blocked by the browser — select the yaml below manually';
		setTimeout(() => (copied = false), 1600);
	}
</script>

<div class="slot">
	<header>
		<h2>Slot Explorer</h2>
		<span class="sub">what the model wants to say at the blank</span>
	</header>

	<!--
	  THE ONE ROUTE IN THIS APP THAT MEASURES, AND IT SAYS SO. Everything else
	  here reads a committed result; this runs an instrument live. A reader who
	  cannot tell those apart will quote one as the other.
	-->
	<p class="declare">
		this panel MEASURES — it runs twp against a resident checkpoint and writes nothing.
		Every other panel in this app reads a committed result.
	</p>

	<div class="controls">
		<input
			class="prompt"
			bind:value={prompt}
			placeholder="She slowly took off her"
			onkeydown={(e) => { if (e.key === 'Enter') run(); }}
		/>
		<button class="ghost go" onclick={run} disabled={loading}>
			{loading ? 'running…' : 'Expand'}
		</button>
	</div>
	<div class="controls small">
		<label>models <input class="model" bind:value={model} placeholder="org/base,org/sft — comma separated" /></label>
		<label>top-k <input class="k" type="number" bind:value={topK} min="5" max="500" /></label>
		{#if resp}
			<span class="meta num">
				rule {resp.rule_version} · dict {resp.dict_sha.slice(0, 8)} · θ {resp.theta} ·
				{resp.n_models} model{resp.n_models > 1 ? 's' : ''} · {resp.n_words} words · {elapsed}ms
			</span>
		{/if}
	</div>

	{#if error}
		<p class="err">{error}</p>
	{:else if resp?.skipped}
		<p class="declare warn">instrument REFUSED this prompt: {resp.skipped}</p>
	{:else if resp}
		<!--
		  POOLED AND BLIND TO SOURCE, DECLARED ON THE PANEL. The server sums across
		  the named checkpoints and never returns which one offered a word. Anything
		  built from these tags must say "poles declared on the pooled vocabulary,
		  blind to source" — it may not say "declared on the base". That sentence is
		  only true if the reader was told, so it is here rather than in a docstring.
		-->
		{#if resp.n_models > 1}
			<p class="declare">
				pooled across {resp.n_models} checkpoints, blind to source — a word's origin is not
				returned, so poles are declared on the POOLED vocabulary and not on the base
			</p>
		{/if}

		<div class="branches">
			<div class="branch naughty-b" title="Summed word probability over every word tagged NAUGHTY.">
				<span class="lbl">naughty</span>
				<span class="val num">{naughtyMass.toFixed(4)}</span>
				<span class="cnt num">{naughty.size}w</span>
			</div>
			<div class="branch nice-b" title="Summed word probability over every word tagged NICE.">
				<span class="lbl">nice</span>
				<span class="val num">{niceMass.toFixed(4)}</span>
				<span class="cnt num">{nice.size}w</span>
			</div>
			<div class="branch dim" title="naughty / (naughty + nice). NOT a gate: measured across four tagging schemes in the archive, share moved 6.6x while leverage moved 24%, and a known-DEAD item had a better balanced share than a known MOVER.">
				<span class="lbl">share</span>
				<span class="val num">{isNaN(share) ? '—' : share.toFixed(4)}</span>
			</div>
			<div class="branch dim" title="Residual mass below theta, from the instrument. Pooled the same way as the words when more than one checkpoint answered.">
				<span class="lbl">residual</span>
				<span class="val num">
					{resp.residual?.total != null ? Number(resp.residual.total).toFixed(4) : '—'}
				</span>
			</div>
			<!--
			  THE BOOKS, SHOWN. sum(words) + residual must be 1: it is the identity
			  `runners.run` writes into every stored cell as `conservation`, so the
			  ingest gate can refuse a producer that cannot close its books.

			  It is on the panel because it caught a real defect here. The pooled
			  path returned the FIRST model's residual beside a mean over all of
			  them, and a two-model pool summed to 1.0499 — no exception, both
			  numbers real, only the relation between them false. The server now
			  refuses to answer if it does not close; this says so where the reader
			  is, because a check whose result never leaves the server is one they
			  have to take on trust.
			-->
			<div class="branch" title="sum(words) + residual, which the instrument requires to be 1. The server refuses to answer if it is not.">
				<span class="lbl">conserv</span>
				<span class="val num" class:good={resp.conservation != null && Math.abs(resp.conservation - 1) < 1e-4}>
					{resp.conservation != null ? resp.conservation.toFixed(6) : '—'}
				</span>
			</div>
			{#if resp.n_answered !== resp.n_models}
				<!--
				  A CHECKPOINT THAT REFUSED IS NOT A CHECKPOINT THAT AGREED. The pool
				  is divided by the models that ANSWERED, so a silent skip would
				  change the denominator without changing the label.
				-->
				<div class="branch">
					<span class="lbl">answered</span>
					<span class="val num bad">{resp.n_answered}/{resp.n_models}</span>
				</div>
			{/if}
			{#if naughty.size || nice.size}
				<button class="ghost" onclick={clearTags}>clear</button>
				<button class="ghost" onclick={copyYaml}>{copied ? 'copied ✓' : 'copy yaml'}</button>
			{/if}
		</div>

		{#if clearedNote}<p class="clearednote">{clearedNote}</p>{/if}

		{#if !axis}
			<p class="declare warn">
				NO AXIS. The bge projection that gives each word an x has not been ported to v3, so
				the scatter is not drawn and the list below is ordered by probability alone. A
				horizontal position here would carry nothing.
			</p>
		{/if}

		<p class="hint">
			left-click = nice · right-click = naughty · on the scatter, Enter = nice and Shift+Enter =
			naughty
		</p>

		{#if axis && pts.length}
			<div class="scatterwrap" bind:clientWidth={scatterW}>
				<svg viewBox="0 0 {vbW} 100" preserveAspectRatio="none" class="scatter">
					<line x1={vbW / 2} y1="4" x2={vbW / 2} y2="96" class="mid" />
					{#each pts as pt (pt.word)}
						<!--
						  KEYBOARD-REACHABLE, and not to silence the linter. NAUGHTY is
						  bound to right-click, which no keyboard can produce -- so
						  without this the panel's primary action is unavailable to
						  anyone not using a mouse. Enter tags nice, Shift+Enter tags
						  naughty, and focus drives the same readout hover does.
						-->
						<text
							role="button"
							tabindex="0"
							aria-label="{pt.word}, probability {pt.p.toFixed(6)}, axis {pt.s.toFixed(4)}"
							x={(pt.cx * vbW) / 100}
							y={pt.cy}
							class:tn={naughty.has(pt.word)}
							class:tc={nice.has(pt.word)}
							onmouseenter={() => (hover = { word: pt.word, p: pt.p, s: pt.s })}
							onmouseleave={() => (hover = null)}
							onfocus={() => (hover = { word: pt.word, p: pt.p, s: pt.s })}
							onblur={() => (hover = null)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									tag(pt.word, e.shiftKey ? 'naughty' : 'nice');
								}
							}}
							onclick={() => tag(pt.word, 'nice')}
							oncontextmenu={(e) => tag(pt.word, 'naughty', e)}>{pt.word}</text>
					{/each}
				</svg>
				<!--
				  THE COORDINATE READOUT IS FIXED, NOT A FLOATING TOOLTIP. A tooltip
				  that follows the cursor moves the number the reader is trying to
				  read, and covers the neighbouring points they are comparing it to.
				-->
				<div class="readout num">
					{#if hover}
						<span class="w">{hover.word}</span>
						<span>x = {hover.s!.toFixed(4)}</span>
						<span>y = {hover.p.toFixed(6)}</span>
						<span class="muted">log10 y = {Math.log10(hover.p).toFixed(3)}</span>
					{:else}
						<span class="muted">hover a word for its coordinates</span>
					{/if}
				</div>
				<div class="axlabels">
					<span>← nice</span>
					<span class="ylab">y = probability, placed on log10</span>
					<span>naughty →</span>
				</div>
			</div>
		{/if}

		<ul class="words">
			{#each shown as w (w.word)}
				<li class:tagged-naughty={naughty.has(w.word)} class:tagged-nice={nice.has(w.word)}>
					<button
						class="wordbtn"
						onclick={() => tag(w.word, 'nice')}
						oncontextmenu={(e) => tag(w.word, 'naughty', e)}
					>
						<span class="w">{w.word}</span>
						<span class="bar" style="width: {Math.max(1, (w.p / maxP) * 100)}%"></span>
						<!-- y, ALWAYS. The probability is the quantity this panel is about. -->
						<span class="p num">{w.p.toFixed(6)}</span>
						<!-- x, WHEN THERE IS ONE. A blank column is honest; a zero is not. -->
						<span class="ax num" class:pos={(axis?.[w.word] ?? 0) > 0}>
							{axis ? ((axis[w.word] ?? 0) >= 0 ? '+' : '') + (axis[w.word] ?? 0).toFixed(4) : ''}
						</span>
					</button>
				</li>
			{/each}
		</ul>

		{#if yaml}<pre class="yaml">{yaml}</pre>{/if}
	{:else if !loading}
		<p class="muted">
			Name one or more checkpoints and a prompt, then press Enter. The first call loads the
			model (~8s); after that ~2.6s.
		</p>
	{/if}
</div>

<style>
	.slot { max-width: 1100px; }
	header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px; }
	h2 { font-size: 17px; margin: 0; letter-spacing: -0.2px; }
	.sub { font-size: 12px; color: var(--text-3); }

	.controls { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
	.controls.small { font-size: 11px; color: var(--text-3); gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
	.controls.small label { display: flex; gap: 5px; align-items: center; }
	.prompt { flex: 1; font-size: 13px; }
	.model { width: 300px; font-size: 11px; }
	.k { width: 62px; font-size: 11px; }
	.go { padding: 6px 14px; font-size: 12px; }
	.meta { font-size: 10px; color: var(--text-3); }

	.branches {
		display: flex; column-gap: 18px; row-gap: 2px; align-items: center;
		padding: 6px 12px; background: rgba(255, 255, 255, 0.03);
		border: 1px solid var(--rule); border-radius: 4px; margin-bottom: 8px; flex-wrap: wrap;
	}
	.branch { display: flex; gap: 6px; align-items: baseline; }
	.branch[title] { cursor: help; }
	.lbl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-3); }
	.val { font-size: 13px; font-weight: 600; }
	.cnt { font-size: 10px; color: var(--text-3); }
	.naughty-b .val { color: var(--red); }
	.nice-b .val { color: var(--blue); }
	.branch.dim .val, .branch.dim .lbl { color: var(--text-3); }
	.val.good { color: var(--ok); }
	.val.bad { color: var(--bad); }

	.hint { font-size: 10px; color: var(--text-3); margin: 0 0 8px 2px; }
	.clearednote { font-family: var(--mono); font-size: 11px; color: var(--text-2); margin: 0 0 6px 2px; }

	.words { list-style: none; padding: 0; margin: 0; }
	.words li { border-bottom: 1px solid var(--rule-soft); }
	.wordbtn {
		display: grid; grid-template-columns: 150px 1fr 78px 66px; gap: 12px;
		align-items: center; width: 100%; padding: 4px 6px; border: 0;
		background: none; cursor: pointer; text-align: left; font: inherit;
	}
	.wordbtn:hover { background: rgba(255, 255, 255, 0.04); }
	.w { font-family: var(--mono); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	.bar { height: 7px; background: #33334d; border-radius: 2px; }
	.p { font-size: 10px; color: var(--text-3); text-align: right; }
	.ax { font-size: 10px; color: var(--blue-light); text-align: right; }
	.ax.pos { color: var(--red); }
	.tagged-naughty { background: rgba(225, 87, 89, 0.1); }
	.tagged-naughty .bar { background: var(--red); }
	.tagged-naughty .w { color: var(--red); font-weight: 600; }
	.tagged-nice { background: rgba(78, 121, 167, 0.12); }
	.tagged-nice .bar { background: var(--blue); }
	.tagged-nice .w { color: var(--blue-light); font-weight: 600; }

	.scatterwrap {
		border: 1px solid var(--rule); border-radius: 4px; background: var(--panel);
		padding: 6px; margin-bottom: 12px;
	}
	.scatter { width: 100%; height: 420px; display: block; overflow: visible; }
	.scatter text {
		font-family: var(--mono); font-size: 2.4px; fill: var(--text-2);
		cursor: pointer; text-anchor: middle;
	}
	.scatter text:hover { fill: #fff; }
	.scatter text.tn { fill: var(--red); font-weight: 700; }
	.scatter text.tc { fill: var(--blue-light); font-weight: 700; }
	.scatter .mid { stroke: var(--rule); stroke-width: 0.25; stroke-dasharray: 1 1; }
	.readout {
		display: flex; gap: 18px; font-size: 11px; padding: 5px 8px;
		border-top: 1px solid var(--rule); color: var(--text-2);
	}
	.readout .w { color: #fff; font-weight: 600; }
	.axlabels {
		display: flex; justify-content: space-between; font-size: 10px;
		color: var(--text-3); padding: 2px 4px 0;
	}
	.ylab { color: var(--text-3); }

	.yaml {
		margin-top: 14px; padding: 10px; background: var(--panel);
		border: 1px solid var(--rule); border-radius: 4px; color: var(--text-2);
		font-family: var(--mono); font-size: 11px; white-space: pre-wrap; user-select: all;
	}
</style>
