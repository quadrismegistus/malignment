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
	import { api, ApiError } from '$lib/api';
	import type { SlotResponse, AxisResponse, Health, Pair, DomainCensus } from '$lib/api';

	let prompt = $state('She slowly took off her');
	//: NO DEFAULT MODEL, matching the server. A default pool is a population
	//: choice; one baked into a client is one nobody reports. The archive shipped
	//: a client default that silently overrode the server's, so the app ran a
	//: population the server's own test never exercised.
	//: The declared pair's BASE id. Not a free model string: pooling base and
	//: endpoint is a property of the instrument, and a text field is how an
	//: author screens on one arm without noticing.
	let pairBase = $state('');
	let pairs = $state<Pair[]>([]);
	let pairsUnresolved = $state<Record<string, string[]>>({});
	api.slotPairs().then((r) => {
		pairs = r.pairs;
		pairsUnresolved = r.unresolved;
		if (!pairBase) pairBase = r.default;
	}).catch(() => (pairs = []));
	let topK = $state(50);

	let resp: SlotResponse | null = $state(null);
	let loading = $state(false);
	let phase = $state<'idle' | 'loading' | 'expanding'>('idle');
	//: Fetched once for the declared diagnostic pair, whose ids live on the
	//: server and are verified out-of-population there. Not polled — the pair
	//: changes only when the roster does, and the server re-checks at boot.
	let health = $state<Health | null>(null);
	api.health().then((h) => (health = h)).catch(() => (health = null));
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

	//: ── THE AXIS.
	//:
	//: `Record<word, number>` and **scoped to this response, deliberately**. It is
	//: a function of the POLES, not of the words: malign's [6365] measured the
	//: same frame under two legitimate pole readings and got `dress +0.1175` on
	//: one and `-0.0097` on the other, a sign flip, at purity 1.000 on BOTH.
	//: Persisting this map anywhere keyed on the word alone would be wrong and
	//: wrong silently. It dies with the tags that made it.
	let axis = $state<Record<string, number> | null>(null);
	let axisInfo = $state<AxisResponse | null>(null);
	let axisLoading = $state(false);
	let axisNote = $state('');
	let hover = $state<{ word: string; p: number; s: number | null } | null>(null);
	//: The full point, so the raised copy can be drawn at the same coordinates.
	let hovered = $state<{ word: string; cx: number; cy: number } | null>(null);

	//: ── THE GENERIC AXIS (RH: "show the x/y plot even before words are tagged
	//: ... from a bge axis of literally 'naughty' - 'nice'").
	//:
	//: Before the author has tagged anything the panel had no x at all, so the
	//: scatter was hidden and the first look at a frame was a bare list. The
	//: single words `naughty` and `nice` give a real semantic direction with no
	//: tagging, which is strictly better than an alphabetical x — alphabetical
	//: would imply an ordering that carries nothing.
	//:
	//: **IT IS LABELLED GENERIC AND ITS STATISTICS ARE NOT SHOWN.** Leverage, N
	//: and purity are properties of THE AUTHOR'S poles; computed against a
	//: generic axis they are a different quantity wearing the same names, and
	//: `screening_base` is this session's lesson in what that costs. The generic
	//: axis gives positions to look at and nothing to gate on.
	const GENERIC_POLES = { naughty: ['naughty'], nice: ['nice'] };
	let axisGeneric = $state(false);

	async function runAxis() {
		if (!resp) {
			axis = null;
			axisInfo = null;
			return;
		}
		const generic = !naughty.size || !nice.size;
		axisGeneric = generic;
		axisLoading = true;
		axisNote = '';
		try {
			//: The probabilities go too, so leverage and N come back with the
			//: scores. `stats()` is the companion call to any reading of the axis,
			//: not an optional extra — see `split`'s docstring on dN cancelling
			//: while something large happens.
			const probs = Object.fromEntries(words.map((w) => [w.word, w.p]));
			const r = await api.slotAxis(
				resp.prompt,
				generic ? GENERIC_POLES.naughty : [...naughty],
				generic ? GENERIC_POLES.nice : [...nice],
				words.map((w) => w.word),
				probs
			);
			axisInfo = r;
			if (!r.ok) {
				axis = null;
				axisNote = r.note ?? 'no axis';
			} else {
				axis = Object.fromEntries(r.scores.map((x) => [x.word, x.s]));
			}
		} catch (e) {
			axis = null;
			axisInfo = null;
			axisNote = e instanceof Error ? e.message : String(e);
		} finally {
			axisLoading = false;
		}
	}

	//: AUTO-REPOLE, DEBOUNCED. The axis is a function of the tags, so it should
	//: not need a button to stay true to them — a stale axis drawn beside fresh
	//: tags is a plot saying something the data no longer says. Debounced because
	//: tagging is a burst and each run embeds every candidate on CPU.
	//:
	//: KEYED ON THE POLE SETS AND THE WORD LIST, not on `resp`: re-running the
	//: same prompt with the same tags should re-project, changing a tag should
	//: re-project, and neither should fire while only a view toggles.
	let poleKey = $derived(
		[...naughty].sort().join(',') + '|' + [...nice].sort().join(',') +
			'|' + words.map((w) => w.word).join(',')
	);
	$effect(() => {
		const k = poleKey;
		if (!words.length) {
			axis = null;
			axisInfo = null;
			return;
		}
		//: Fires with NO tags as well, so the scatter exists from the first
		//: expansion. Still debounced: tagging is a burst and each run embeds
		//: every candidate on CPU.
		const t = setTimeout(runAxis, 450);
		return () => clearTimeout(t);
	});

	async function run() {
		if (!prompt.trim()) return;
		if (!pairBase) {
			error = 'no declared pair selected';
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
		//: **"Loading models…" IS A DIFFERENT STATE FROM "running…".** A cold call
		//: is ~6s on a 360M and ~10s on a 1B; a warm one is under a second. Under
		//: one spinner those are indistinguishable, and the long one is exactly
		//: where a user starts wondering whether it has hung and clicks again.
		//:
		//: Asked fresh rather than read off the polled badge: the poll is on a 15s
		//: interval and the models may have been released by the idle reaper since
		//: it last ran. A stale "resident" here would promise a fast call and
		//: deliver a slow one, which is the failure this message exists to prevent.
		try {
			const p = pairs.find((x) => x.base === pairBase);
			const want = p ? [p.base, p.endpoint] : [pairBase];
			const h = await api.health();
			phase = want.every((m) => h.slot_loaded.includes(m)) ? 'expanding' : 'loading';
		} catch {
			phase = 'expanding';
		}
		try {
			resp = await api.slot(prompt, pairBase, topK);
			taggedFor = prompt;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			resp = null;
		} finally {
			elapsed = Math.round(performance.now() - t0);
			loading = false;
			phase = 'idle';
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
		//: ── EVERY WORD IS LABELLED (RH: "show all words, even if they overlap,
		//: as long as they highlight on hover I can see what's underneath").
		//:
		//: This previously labelled the top 24 by probability and drew the rest as
		//: marks, because the log-scale tail overprints. That traded legibility for
		//: completeness and RH wants the other trade: overlap is acceptable when
		//: hover raises the word out of the pile, and a mark you cannot identify is
		//: worse than a label you have to hover to read.
		//:
		//: The hovered word is re-drawn ON TOP after the loop, because SVG has no
		//: z-index and paints in document order — CSS alone cannot raise it.
		return words.map((w, i) => ({
			word: w.word,
			p: w.p,
			s: xs[i],
			cx: 6 + ((xs[i] - xlo) / span) * 88,
			cy: 92 - ((ly[i] - ylo) / yspan) * 84
		}));
	});
	//: Measured by looking, not chosen: at 50 the tail overprints, at 24 it does
	//: not on a 1560px panel. It is a legibility budget, so it has no better
	//: justification than the rendered image and should be re-checked if the
	//: panel geometry changes.


	//: The scatter's own pixel size, so the viewBox matches its aspect ratio.
	//: With `preserveAspectRatio="none"` a mismatched viewBox scales x and y
	//: independently: this was `0 0 100 100` in a ~1900x420 box, a 4.5x
	//: HORIZONTAL SCALE ON EVERY GLYPH, and the words came out looking
	//: letter-spaced -- a rendering artifact, not a property of anything measured.
	//:
	//: **BOTH DIMENSIONS ARE MEASURED NOW.** The height used to be the literal
	//: 420 from the stylesheet, with a comment saying to change it here too if
	//: the CSS changed. That is a footgun with a note taped to it, and the note
	//: does not fire: the panel is now sized in `vh` and the constant would have
	//: been silently wrong at every viewport but one.
	let scatterW = $state(0);
	let scatterH = $state(0);

	//: ── THE PLOT FILLS WHAT IS LEFT OF THE VIEWPORT (RH, 2026-08-17: "can we
	//: make sure height stays in page without need for scroll?").
	//:
	//: **MEASURED, NOT `calc(100vh - 300px)`.** The content above this plot is not
	//: a fixed height: the pair line, the axis badges, the cleared-tags note, the
	//: save row and any error each appear and disappear, and the badges rewrap at
	//: narrow widths. A subtracted constant is right at exactly one viewport and
	//: one panel state, and wrong silently everywhere else — the same footgun as
	//: the literal 420 this file just lost.
	//:
	//: No feedback loop: `top` is the distance to the plot's own top edge, which
	//: depends on the content ABOVE it and not on its own height.
	let wrapEl = $state<HTMLElement | null>(null);
	let plotH = $state(420);
	//: **MEASURED AGAINST THE SCROLL CONTAINER, NOT THE VIEWPORT.** A viewport
	//: measurement is only correct at `scrollTop === 0`: scroll down, tag a word,
	//: and the re-fit sees a smaller `top` and grows the plot to fill space that
	//: is already above the fold. Adding `scrollTop` back makes the offset a
	//: distance from the CONTENT top, which is what it needs to be.
	function fitPlot() {
		if (!wrapEl) return;
		const box = wrapEl.getBoundingClientRect();
		const main = wrapEl.closest('main');
		if (main) {
			const offset = box.top - main.getBoundingClientRect().top + main.scrollTop;
			plotH = Math.max(280, Math.round(main.clientHeight - offset - 14));
		} else {
			plotH = Math.max(280, Math.round(window.innerHeight - box.top - 14));
		}
	}
	$effect(() => {
		//: Re-fit when anything above can have changed height. Reading them here is
		//: what subscribes the effect to them.
		void [resp, axisInfo, axisNote, error, clearedNote, saved, saveError, naughty.size, nice.size];
		if (!wrapEl) return;
		//: After paint, so the row above has its final height.
		const id = requestAnimationFrame(fitPlot);
		window.addEventListener('resize', fitPlot);
		return () => {
			cancelAnimationFrame(id);
			window.removeEventListener('resize', fitPlot);
		};
	});
	let vbW = $derived(
		scatterW > 0 && scatterH > 0 ? Math.max(100, (scatterW / scatterH) * 100) : 100
	);

	let shown = $derived.by(() => {
		if (!axis) return words;
		return [...words].sort((a, b) => (axis![b.word] ?? -9) - (axis![a.word] ?? -9));
	});

	//: ── THE SAVED ITEM CARRIES WHAT SCREENED IT (malign, [6361]).
	//:
	//: The first version emitted item_id, prompt, naughty, nice — and **no
	//: models at all**. So an item recorded which words an author tagged and not
	//: which checkpoints produced the distribution they were looking at. Two
	//: items authored against different pairs were indistinguishable afterwards,
	//: which is the provenance defect this campaign keeps paying for, and it is
	//: my own rule from [6358]: *a default pool is a population choice, and one
	//: made in a server is one nobody reports.*
	//:
	//: **READ FROM `resp.models`, NEVER FROM THE `model` INPUT.** The input is
	//: editable after an expansion, so an author who retypes it before copying
	//: would stamp the item with a pair that did not screen it. The response is
	//: the record of what actually ran. Same reason the rule_version and dict_sha
	//: come off the payload rather than being written as constants here.
	//:
	//: `displayed: probability` is stated rather than implied, because [6361]
	//: makes the screening ARM part of the item: an item screened on summed
	//: probabilities with movement never shown is a different instrument from one
	//: screened while looking at movement, and two provenances in one column is
	//: exactly the thing being guarded against.
	//: ── THE DERIVED ID (RH, 2026-08-16).
	//:
	//: This emitted `item_id: CHANGEME`, faithfully, because the archive's
	//: copy-yaml button did too — there the real id was computed in
	//: `_slot_save`, server-side, and v3 has no save route yet. So the port was
	//: right and the gap was one level up: nothing in v3 produced the id at all.
	//:
	//: `nn_<last3words>_<nice0>-<naughty0>`, and it is not a new convention: 86
	//: items in the archive's `round3_slots.yaml` already carry ids from this
	//: function, so changing it orphans them. `malignment/slots.py` is the ported
	//: rule and reproduces all 86.
	//:
	//: FETCHED, NOT COMPUTED HERE. It is three regexes and the temptation to
	//: inline them is the whole point: Python's `\w` is Unicode-aware and
	//: JavaScript's is ASCII-only, so a port silently strips accented and CJK
	//: characters the original keeps, yielding ids that look right and do not
	//: match what is already written.
	let itemId = $state('');
	//: A FUNCTION OF THE PROMPT ALONE (RH, 2026-08-17). It used to depend on the
	//: highest-mass word of each pole, which made it a property of the RUN rather
	//: than of the item: re-screening the same tagged frame on a different pair
	//: renamed it, and two frames differing only in gender could SWAP ids —
	//: `nn_andstartedto_search-beat` and `..._search-choke`, where each item's
	//: runner-up is the other's top word. See `slots.item_id`.
	//:
	//: So the id no longer waits for tags: it exists as soon as a prompt has been
	//: expanded, and tagging does not move it. Still fetched rather than computed
	//: here — a JavaScript port would need matching Unicode classes AND a matching
	//: sha256 over the same byte encoding, two ways to diverge silently.
	$effect(() => {
		const p = resp?.prompt;
		if (!p) {
			itemId = '';
			return;
		}
		api.slotItemId(p)
			.then((r) => (itemId = r.item_id))
			//: A FAILURE FALLS BACK TO THE PLACEHOLDER, never to a guess. An id
			//: computed here on the error path is the divergence this route exists
			//: to prevent, arriving exactly when nobody is watching.
			.catch(() => (itemId = 'CHANGEME'));
	});

	//: ── ONE PROVENANCE OBJECT, RENDERED TWICE.
	//:
	//: The yaml block below and the `/slot/save` payload describe the same run,
	//: and two hand-built copies of one description is the drift this file
	//: documents at every other level. Built once here; the yaml reads its
	//: fields and the save posts it whole.
	//:
	//: **IT CARRIES THREE FIELDS THE YAML BLOCK DOES NOT**, because the saved
	//: JSON is a new artifact and none of them belongs in a format 86 items
	//: already use. `pair` is the DECLARED (base, endpoint) and its path —
	//: `models` is the arms that ran, which is a different claim once a path is
	//: multi-step, and 17 of the 50 are. `n_answered` is the pool's real
	//: denominator: it differs from `n_models` when a tokenizer refuses the
	//: prompt, and dividing by the wrong one is the pooling bug this panel has
	//: already shipped once.
	let screenedBy = $derived.by(() => {
		if (!resp) return null;
		return {
			role: 'screening',
			models: resp.models,
			pooled: resp.n_models > 1,
			displayed: 'probability',
			rule_version: resp.rule_version,
			dict_sha: resp.dict_sha,
			theta: resp.theta,
			n_words: resp.n_words,
			top_k: resp.shown,
			n_models: resp.n_models,
			n_answered: resp.n_answered,
			pair: resp.pair
		};
	});

	let yaml = $derived.by(() => {
		if (!resp || (!naughty.size && !nice.size)) return '';
		const sb = screenedBy!;
		//: **MASS-ORDERED, AND NEVER ALPHABETISED.** Two reasons, and the second
		//: is the one that would get lost:
		//:
		//: 1. the id takes the head of each list, so it must be a property of the
		//:    distribution and not of the order the author happened to click
		//: 2. **the order is recoverable provenance.** The masses identify the
		//:    screening pair only because the lists they were summed over are
		//:    stored verbatim in mass order; sorting them for tidiness on any
		//:    later migration destroys a check that has already corrected a wrong
		//:    memory about 86 items ([6365]).
		//:
		//: A cosmetic sort here is unrecoverable and looks like housekeeping.
		const byMass = (set: Set<string>) =>
			words.filter((w) => set.has(w.word)).sort((a, b) => b.p - a.p).map((w) => w.word);
		const list = (xs: string[]) => `[${xs.join(', ')}]`;
		return (
			`- item_id: ${itemId || 'CHANGEME'}\n` +
			`  prompt: ${JSON.stringify(resp.prompt)}\n` +
			`  naughty: ${list(byMass(naughty))}\n` +
			`  nice: ${list(byMass(nice))}\n` +
			//: ── THE BRANCH MASSES ARE THE CHECK ON `screened_by`, NOT A DISPLAY
			//: FIELD. **Do not delete them as redundant once the stamp exists.**
			//:
			//: The reason first written here was that they separate *nothing to
			//: move* from *nothing to choose*, since a ratio calls 0/0 and 0.3/0.3
			//: both "balanced". True, and far too weak: it justifies showing them
			//: on screen, not storing them, so anyone holding `screened_by` would
			//: reasonably cut them.
			//:
			//: The real reason, measured (malign, [6365]). Two floats over an
			//: author-chosen word set IDENTIFY the checkpoint pair. On
			//: `nn_tookoffher_coat-dress` the recorded 0.1218 / 0.2635 reproduces
			//: under Llama-3.1-8B + Tulu-3-8B-SFT pooled as a mean at err 0.0004,
			//: against 0.0174 for the DPO arm and 0.0918 for Meta's instruct — and
			//: the best single model out of all 402 with cells is 0.0032. A second
			//: frame resolved to the same pair independently.
			//:
			//: **So the artifact can check its own label.** A stamp declares and
			//: does not apply; an item whose recorded masses do not reproduce under
			//: its declared pair is a mislabelled item, detectable with no memory
			//: and no trust. That is what recovered the provenance of 86 archive
			//: items whose author remembered the wrong arm.
			`  naughty_mass: ${naughtyMass.toFixed(4)}\n` +
			`  nice_mass: ${niceMass.toFixed(4)}\n` +
			`  share: ${Number.isNaN(share) ? 'null' : share.toFixed(4)}\n` +
			`  writer: slot-explorer\n` +
			//: ── `role: screening`, NAMED (malign, [6363]).
			//:
			//: There are TWO roles and this panel only fills one:
			//:
			//:   SCREENING BASE   one distribution, no contrast. leverage, purity,
			//:                    pole_gap, pole mass. "can this frame move at all"
			//:   DIAGNOSTIC PAIR  base + aligned. dN, suppression, substitution.
			//:                    "what does the instrument do here"
			//:
			//: An item screened on one and diagnosed on another is two facts, and
			//: one field cannot hold them. So the role is written rather than
			//: implied, and a later diagnostic pass appends `diagnosed_by`
			//: alongside instead of overwriting this.
			//:
			//: **AND `models` IS A LIST BECAUSE THE PRACTICE POOLS, WHICH THE ROLE
			//: DESCRIPTION DOES NOT.** [6363] calls screening "one distribution, no
			//: contrast", and the 86 archive items were nonetheless screened on a
			//: POOL -- Llama-3.1-8B + Tulu-3-8B-SFT as a mean, recovered from their
			//: own recorded masses at [6365]. Both readings are defensible: pooling
			//: buys coverage of arrival-side vocabulary the base never offers. That
			//: tension is not mine to resolve, so the stamp records what actually
			//: ran and stays true under either ruling.
			`  screened_by:\n` +
			`    role: ${sb.role}\n` +
			`    models: ${list(sb.models)}\n` +
			`    pooled: ${sb.pooled}${sb.pooled ? '   # summed then divided by the models that ANSWERED' : ''}\n` +
			`    displayed: ${sb.displayed}          # movement NEVER shown at authoring time\n` +
			`    rule_version: ${sb.rule_version}\n` +
			`    dict_sha: ${sb.dict_sha}\n` +
			`    theta: ${sb.theta}\n` +
			`    n_words: ${sb.n_words}\n` +
			`    top_k: ${sb.top_k}\n`
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

	//: ── SAVING (RH, 2026-08-17).
	//:
	//: Writes to `$MALIGNMENT_DATA/slots/`, outside the repo, because a saved
	//: item carries its prompt verbatim from the transgressive battery.
	//:
	//: **THE PAYLOAD IS TAGS AND A DISTRIBUTION. NOTHING DERIVED IS SENT.**
	//: `item_id`, the mass ordering and `share` are all computed in `slots.py`
	//: from the words posted here, for the same reason `item_id` is fetched
	//: rather than built in JavaScript: a client-supplied mass that disagreed
	//: with the tags beside it would be undetectable and permanent.
	let saving = $state(false);
	let saved = $state<{ item_id: string; action: string } | null>(null);
	let saveError = $state('');
	let conflict = $state(false);
	let saveNote = $state('');
	//: **FREE TEXT WITH SUGGESTIONS, NOT A SELECT** (RH, 2026-08-17: "we also want
	//: a domain: tag ... for me to later categorise by sexual/violent/etc"). The
	//: ten values below are what `round3_slots.yaml` actually used; a closed
	//: dropdown would silently discourage the eleventh category, and the field
	//: exists to make a later sort possible rather than to settle the taxonomy
	//: now. The server does not validate it either.
	//: **THE LIST IS NOW THE SERVER'S** (`/slot/domains`), with this literal only
	//: as the pre-fetch fallback. Two hand-maintained copies of the same ten
	//: strings drift silently: the author picks from this datalist while the
	//: census groups by `slots.DOMAINS`, so a name added in one place makes an
	//: item that files itself under a domain the other never shows.
	const DOMAINS_FALLBACK = ['sexual', 'violence', 'power', 'substance', 'property',
		'identity_matched_frame', 'self_harm', 'poverty', 'medical', 'institutional'];
	let census = $state<DomainCensus | null>(null);
	let DOMAINS = $derived(census?.domains ?? DOMAINS_FALLBACK);
	//: Suggestions first, then any domain already in use that is NOT on the list,
	//: so an eleventh category typed once is offered the second time instead of
	//: being retyped from memory and misspelled -- which is what makes the
	//: `collisions` row below appear.
	let domainOptions = $derived([
		...DOMAINS,
		...(census?.rows ?? [])
			.filter((r) => !r.suggested && !r.untagged && r.total > 0)
			.map((r) => r.domain)
	]);
	let censusOpen = $state(false);
	let saveDomain = $state('');
	let savedCount = $state<number | null>(null);
	//: The id can CHANGE under retagging rather than collide: it is built from
	//: the top-mass word of each branch, so promoting a different word to the
	//: head of a pole yields a NEW item instead of replacing one. The panel says
	//: which ids are already on disk, because a save that quietly creates a
	//: second item looks exactly like one that updated the first.
	let savedIds = $state<string[]>([]);

	function refreshSaved() {
		//: Re-read on every save, because the census is the reason to save into a
		//: thin domain and a stale one advises the opposite.
		api.slotDomains()
			.then((r) => (census = r))
			.catch(() => (census = null));
		api.slotSaved()
			.then((r) => {
				savedCount = r.n;
				savedIds = r.items.map((i) => i.item_id);
			})
			.catch(() => {
				savedCount = null;
				savedIds = [];
			});
	}
	$effect(refreshSaved);

	async function save(overwrite = false) {
		if (!resp || !naughty.size || !nice.size || saving) return;
		saving = true;
		saveError = '';
		saved = null;
		try {
			//: Only the tagged words' probabilities. Sending the whole candidate
			//: list would post kilobytes the server discards, and `build_item`
			//: refuses a tag that is absent from what it receives — so the map
			//: has to cover the tags exactly.
			const wordP: Record<string, number> = {};
			for (const w of words) if (naughty.has(w.word) || nice.has(w.word)) wordP[w.word] = w.p;
			const r = await api.slotSave({
				prompt: resp.prompt,
				naughty: [...naughty],
				nice: [...nice],
				words: wordP,
				provenance: screenedBy ?? {},
				domain: saveDomain.trim(),
				note: saveNote.trim(),
				overwrite
			});
			saved = { item_id: r.item_id, action: r.action };
			refreshSaved();
			setTimeout(() => (saved = null), 4000);
		} catch (e) {
			//: **A 409 IS A QUESTION, NOT A FAILURE.** The id already exists with
			//: different tags, which means this prompt was authored before and the
			//: earlier tagging would be lost. Surfaced as an explicit choice with
			//: the overwrite button beside it, never retried automatically.
			const err = e as ApiError;
			saveError = err.message || 'save failed';
			conflict = !!err.conflict;
		} finally {
			saving = false;
		}
	}

	let alreadySaved = $derived(!!itemId && savedIds.includes(itemId));
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
	<!--
	  RH, 2026-08-17: these declarations cost vertical space the graph wants.
	  THEY ARE COMPRESSED, NOT DELETED. The distinction they carry is real — a
	  reader who cannot tell a live instrument from a committed result will quote
	  one as the other — so each survives as a `title` on a badge that sits in a
	  row the panel already draws. Zero extra lines, one hover to recover.
	-->
	<div class="controls">
		<span
			class="badge"
			title="This panel MEASURES: it runs twp against a resident checkpoint and writes nothing. Every other panel in this app reads a committed result."
			>measures</span
		>
		<input
			class="prompt"
			bind:value={prompt}
			placeholder="She slowly took off her"
			onkeydown={(e) => { if (e.key === 'Enter') run(); }}
		/>
		<button class="ghost go" onclick={run} disabled={loading}>
			{#if phase === 'loading'}Loading models…{:else if phase === 'expanding'}running…{:else}Expand{/if}
		</button>
	</div>
	{#if phase === 'loading'}
		<!--
		  NAMED, AND WITH THE REASON. "Loading models..." on its own reads as an
		  app being slow; saying which weights and roughly how long makes it a
		  cost the user can decide about. The panel is the only place that knows
		  this is a one-off per model rather than the normal speed.
		-->
		<p class="declare">
			loading weights for the first call — ~6s at 360M, ~10s at 1B. Held for
			the session and released after idle, so the next expansion is under a second.
		</p>
	{/if}
	<div class="controls small">
		<!--
		  LABELLED FOR ITS ROLE, AND LEFT EMPTY (malign, [6363]). This is the
		  SCREENING base, not the diagnostic pair, and the two take different
		  answers: screening wants a REPRESENTATIVE model, because selection on
		  P_base is a pre-treatment covariate and cannot bias a base->aligned
		  contrast measured after it.

		  Empty on purpose. A default is a population choice hiding in a server
		  *when there are several defensible answers*, and for the screening base
		  there are many — so the choice gets made, named and stamped every time.
		  The diagnostic pair is the opposite case (one declared answer, its
		  correctness a property of the roster) and WILL be prefilled, on the
		  movement route, when that route exists. It is not offered here, because
		  a control that appears to affect a measurement and drives nothing is
		  worse than an absent one.
		-->
		<label>pair
			<select class="pairsel" bind:value={pairBase}>
				{#each pairs as p (p.base)}
					<option value={p.base}>{p.label}{p.n_steps && p.n_steps > 1 ? `  (${p.n_steps} steps)` : ''}</option>
				{/each}
			</select></label>
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
		<!--
		  THE SCREENING PAIR IS NAMED ON THE PANEL, ALWAYS (malign, [6361]: "the
		  pair must be named in the UI and written onto the saved item, never
		  implied").

		  It reads `resp.models`, not the input above it, so what is shown is what
		  RAN. An author who edits the model field without re-expanding will see
		  the field and this line disagree, which is correct: the field is an
		  intention, this is a record.

		  NO LONGER GATED ON `n_models > 1`. The single-model case is exactly where
		  a reader is most likely to assume they already know which checkpoint it
		  was, so it is the case that most needs saying.
		-->
		<!--
		  THE PAIR AND ITS PATH LENGTH, both stamped. "Aligned" means the far end
		  of `n_steps` operations -- three for the default -- and a panel that
		  printed two ids would let a reader take it for one hop. Only the two ENDS
		  are loaded; the intermediate rungs are named, not measured.
		-->
		<div class="branches">
			<!--
			  The pair is already chosen in the dropdown above, so repeating it in
			  prose was the redundant half. What is NOT redundant is that the pool is
			  blind to source and that the path may be multi-step — both live here as
			  a title on a cell the row already had space for.
			-->
			<div
				class="branch dim"
				title="Pooled over {resp.pair.base} + {resp.pair.endpoint}, BLIND TO SOURCE — a word's origin is not returned, so poles are declared on the pooled vocabulary and not on the base.{resp.pair.n_steps && resp.pair.n_steps > 1 ? ` ${resp.pair.n_steps} operations apart (${resp.pair.ops.join(' → ')}); only the two ENDS are loaded and the intermediate rungs are named, not measured.` : ''}"
			>
				<span class="lbl">pooled</span>
				<span class="val num"
					>2 ends{#if resp.pair.n_steps && resp.pair.n_steps > 1} · {resp.pair.n_steps} ops{/if}</span
				>
			</div>
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
			{#if axisInfo?.ok && !axisGeneric}
				<!--
				  LEVERAGE IS THE SPREAD OF MASS ALONG THE AXIS, and it is the
				  quantity branch mass is not. dN = sum dP(w)s(w), so an item can
				  only register movement if its mass sits at DIFFERENT POSITIONS —
				  if every word offered has the same s, no redistribution among
				  them changes N, whatever the branch totals say.
				-->
				<div class="branch" title="Spread of probability mass along the axis. An item can only register movement if its mass sits at different positions — branch totals cannot tell you this.">
					<span class="lbl">leverage</span>
					<span class="val num">{axisInfo.leverage?.toFixed(4) ?? '—'}</span>
				</div>
				<div class="branch" title="Expected position of the model's mass on this axis: N = sum P(w)·s(w). The LEVEL, which carries your pole choice — dN, the movement from base, is the comparable quantity across items and is NOT shown here.">
					<span class="lbl">N</span>
					<span class="val num">{axisInfo.N != null ? (axisInfo.N >= 0 ? '+' : '') + axisInfo.N.toFixed(4) : '—'}</span>
				</div>
				<div class="branch" title={axisInfo.defectors?.length
					? `MISTAGGED: ${axisInfo.defectors.join(', ')} — declared on one side of the axis, scoring on the other. Usually a tagging error, and visible with no model run.`
					: 'Every declared pole word lands on its own side. Only the CENTROIDS are guaranteed to; individual words are not.'}>
					<span class="lbl">purity</span>
					<span class="val num" class:good={(axisInfo.purity ?? 0) >= 1}
						class:bad={(axisInfo.purity ?? 1) < 1}>{axisInfo.purity?.toFixed(2) ?? '—'}</span>
				</div>
				<div class="branch dim" title="Distance between the two pole centroids along the axis they define.">
					<span class="lbl">pole gap</span>
					<span class="val num">{axisInfo.pole_gap?.toFixed(3) ?? '—'}</span>
				</div>
				<div class="branch dim" title="Words tagged on each side. A centroid from ONE embedding rests the whole direction on a single word's neighbourhood.">
					<span class="lbl">poles</span>
					<span class="val num">{naughty.size}/{nice.size}</span>
				</div>
				{#each axisInfo.flags ?? [] as f (f)}
					<div class="verdict bad">{f}</div>
				{/each}
			{:else if axisLoading}
				<span class="cnt">building axis…</span>
			{/if}
			{#if naughty.size || nice.size}
				<button class="ghost" onclick={clearTags}>clear</button>
				<button class="ghost" onclick={copyYaml}>{copied ? 'copied ✓' : 'copy yaml'}</button>
				<!--
				  SAVE. Disabled until BOTH poles carry a tag, because `item_id`
				  takes the top word of each and an item with one pole has no axis.
				  The server refuses the same case; the button says so first rather
				  than letting the author find out by error.
				-->
				<button
					class="ghost save"
					onclick={() => save(false)}
					disabled={saving || !naughty.size || !nice.size}
					title={!naughty.size || !nice.size
						? 'both poles need a tag — the id takes the top word of each'
						: `write ${itemId || 'this item'} to the slots directory`}
				>
					{saving ? 'saving…' : alreadySaved ? 'save (update)' : 'save'}
				</button>
			{/if}
		</div>

		{#if naughty.size && nice.size}
			<div class="saverow">
				<input
					class="domainin"
					list="slot-domains"
					bind:value={saveDomain}
					placeholder="domain"
					title="free text — sexual, violence, power … used to sort later. Nothing enforces the list."
				/>
				<datalist id="slot-domains">
					{#each domainOptions as d (d)}<option value={d}></option>{/each}
				</datalist>
				<input
					class="notein"
					bind:value={saveNote}
					placeholder="note (optional) — why this frame, what to watch"
				/>
				{#if savedCount !== null}
					<span class="cnt dim" title="items already written to $MALIGNMENT_DATA/slots/">
						{savedCount} saved
					</span>
				{/if}
				{#if census}
					<button
						class="censustog"
						class:on={censusOpen}
						onclick={() => (censusOpen = !censusOpen)}
						title="items per domain across both slot corpora — for building a balanced set"
					>
						{censusOpen ? 'hide' : 'domains'} · {census.n_total}
					</button>
				{/if}
				{#if saved}
					<!--
					  THE ACTION IS SHOWN VERBATIM, not flattened to "saved ✓".
					  `created`, `overwritten` and `unchanged` are three different
					  events and only the author can say whether the second was
					  intended.
					-->
					<span class="ok">{saved.action}: {saved.item_id}</span>
				{/if}
				{#if saveError}
					<span class="bad">{saveError}</span>
					{#if conflict}
						<!--
						  A 409 IS A QUESTION. The id exists with different tags, so
						  the earlier tagging would be lost. Never retried
						  automatically; the previous version stays in journal.jsonl
						  either way, which is what makes this recoverable rather
						  than merely confirmed.
						-->
						<button
							class="ghost danger"
							onclick={() => {
								conflict = false;
								save(true);
							}}>overwrite it</button
						>
					{/if}
				{/if}
			</div>
		{/if}

		{#if censusOpen && census}
			<!--
			  ── ITEMS PER DOMAIN, FOR BUILDING A BALANCED SET.

			  TWO COLUMNS, NEVER ONE. `round3` is the 86 committed items migrated
			  from the archive; `now` is what is being authored into
			  $MALIGNMENT_DATA. A single pooled count cannot answer either question
			  an author has -- "is the set I am adding balanced" and "is the whole
			  corpus balanced" -- and pooling makes a thin domain look served by
			  inherited items the author did not choose.

			  A DOMAIN AT ZERO IS A ROW. That is why this is not a GROUP BY: the
			  rows worth acting on are the ones with nothing in them, and those are
			  exactly the rows a group-by cannot produce.

			  THE BAR IS THE COMPARISON AND `need` IS ARITHMETIC ON THE COUNTS.
			  `need` is distance to the LARGEST domain, not to a target -- what a
			  balanced set should hold is RH's decision, and a column called
			  `target` would be this panel inventing one.
			-->
			<div class="census">
				<div class="censushead">
					<span
						>items per domain · {census.n_total} total, largest {census.max_total}</span
					>
					<span class="dim"
						>round3 {census.files.round3?.n ?? 0} committed · now {census.files
							.authoring?.n ?? 0} authored · domain is free text and nothing enforces
						the list</span
					>
				</div>
				<table class="censustab">
					<thead>
						<tr>
							<th>domain</th>
							<th class="n">round3</th>
							<th class="n">now</th>
							<th class="n">total</th>
							<th class="bar"></th>
							<th class="n" title="how many more to level with the largest domain">need</th>
						</tr>
					</thead>
					<tbody>
						{#each census.rows as r (r.domain)}
							<tr class:zero={r.total === 0} class:untag={r.untagged}>
								<td class="dom">
									{r.domain}{#if !r.suggested && !r.untagged}<span
											class="offlist"
											title="not in the suggestion list — free text, which is allowed">*</span
										>{/if}
								</td>
								<td class="n dim">{r.round3 || ''}</td>
								<td class="n" class:mine={r.authoring > 0}>{r.authoring || ''}</td>
								<td class="n tot">{r.total}</td>
								<td class="bar">
									<!--
									  Two stacked segments so the author can see at a glance
									  which part of a domain's height they authored and which
									  part was inherited. Width is against `max_total`, so a
									  full bar means "this is the largest", not "this is done".
									-->
									<span
										class="seg r3"
										style="width:{census.max_total
											? (r.round3 / census.max_total) * 100
											: 0}%"
									></span><span
										class="seg au"
										style="width:{census.max_total
											? (r.authoring / census.max_total) * 100
											: 0}%"
									></span>
								</td>
								<td class="n need">{r.deficit_to_max ?? ''}</td>
							</tr>
						{/each}
					</tbody>
				</table>
				{#if census.collisions.length}
					<!--
					  NEAR-MISSES ARE FLAGGED AND NOT MERGED. Two raw strings that
					  differ only by case or separator are almost always one domain
					  typed twice, but folding them here would report a balance the
					  files do not have and hide the slip. Merging is the author's
					  call; this only says where.
					-->
					<div class="collide">
						same domain typed two ways — merge by hand, nothing folds these:
						{#each census.collisions as g (g.join('|'))}
							<code>{g.join(' / ')}</code>
						{/each}
					</div>
				{/if}
			</div>
		{/if}

		{#if axisInfo?.ok && !axisGeneric}
			<!--
			  ── THE THRESHOLDS ARE PRINTED AND DRAW NO VERDICT, and this line is
			  the whole reason that is safe to show at all.

			  LEV_MOVER 0.1027 / LEV_DEAD 0.0694 were measured in the archive on a
			  specific instrument, population and k. v3's populations have already
			  moved under exactly this kind of change — endpoints() went 48 to 50
			  on 2026-08-16. Rendering a red/green gate from them would assert a
			  calibration nobody has re-derived, which is the "asserting against a
			  booked value that is not a measurement" failure with an image on it.

			  So: the numbers, their provenance, and no colour. A reader can
			  compare and decide; the panel does not decide for them.
			-->
			<!--
			  RH, 2026-08-17: removed from the panel. The thresholds are still
			  RETURNED by `/slot/axis` and `leverage_verdict` is still null, so
			  nothing here draws a verdict from them and no fence was load-bearing on
			  this line — it was telling the reader about a gate the panel does not
			  apply. `slot_axis.LEV_SOURCE` carries the same statement at the place
			  the numbers actually live.
			-->
		{/if}
		{#if axisNote}<p class="declare warn">axis: {axisNote}</p>{/if}

		{#if clearedNote}<p class="clearednote">{clearedNote}</p>{/if}

		{#if axisGeneric && axis}
			<!--
			  ── THE GENERIC AXIS, CHARACTERISED OVER 14 AUTHORED ITEMS.
			
			  The previous version of this line quoted 6.2x and 67% from ONE frame
			  while rendering for every frame -- the same defect as the hardcoded
			  0.0714 movement figure two commits earlier: a number from one
			  measurement captioning all cases. Measured properly against the declared
			  pole sets in `round3_slots.yaml`:
			
			      span vs authored axis        3.9x narrower  (median)
			      pairwise order agreement     68%            (median)
			      separates the two branches   80%            (median)
			
			  **So it usually works, and that is not the risk.** The risk is the tail:
			
			      nn_feltherselfget_weak-wet    order 19%   separation  8%
			      nn_felthimselfget_weak-hard   order 13%   separation 11%
			
			  Those are not flat, they are INVERTED -- the generic axis puts the
			  author's naughty branch on the nice side almost perfectly. Both are
			  frames whose loaded word is an ordinary adjective (`wet`, `hard`) that
			  the bare word "naughty" does not reach.
			
			  **An inverted axis is worse than a flat one.** A flat axis is visibly
			  useless; an inverted one looks like a result. And nothing on the panel
			  distinguishes them, because the check requires the poles this axis exists
			  to precede. That is why the warning is unconditional rather than
			  triggered.
			-->
			<!--
			  THE WARNING IS UNCONDITIONAL AND STAYS UNCONDITIONAL, but it is a badge
			  now. The tail is what it is for: two of 14 authored frames come out
			  INVERTED rather than flat, and an inverted axis looks like a result
			  where a flat one is visibly useless. Nothing on the panel can tell them
			  apart, because the check needs the poles this axis stands in for.
			-->
			<span
				class="badge warn"
				title="GENERIC AXIS — positions come from the bare words `naughty` and `nice`, not from your poles. Over 14 authored items it spans 3.9x less than a real axis and agrees on 68% of orderings (medians). Usually it separates the two branches; on some frames it INVERTS them entirely — nn_feltherselfget_weak-wet agrees on 19%, nn_felthimselfget_weak-hard on 13% — and nothing here tells you which, because that check needs the poles this axis stands in for. A rough layout to click on, not a reading. Leverage, N and purity are withheld until the poles are yours."
				>generic axis</span
			>
		{:else if !axis}
			<p class="declare warn">
				NO AXIS &mdash; the projection could not be built. {axisNote || 'The two poles may be identical in embedding space.'}
			</p>
		{/if}
		<p class="hint">
			left-click = nice · right-click = naughty · on the scatter, Enter = nice and Shift+Enter =
			naughty
		</p>

		{#if axis && pts.length}
			<div class="scatterwrap" bind:this={wrapEl}>
				<!--
				  MEASURED ON THE SVG, NOT ON THE WRAPPER. The wrapper carries 6px of
				  padding and the readout row beneath, so its height is not the plot's
				  height and the aspect ratio would come out skewed — which shows up as
				  the horizontal glyph stretch this viewBox exists to prevent.
				-->
				<svg
					viewBox="0 0 {vbW} 100"
					preserveAspectRatio="none"
					class="scatter"
					style="height: {plotH}px"
					bind:clientWidth={scatterW}
					bind:clientHeight={scatterH}
				>
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
							onmouseenter={() => { hover = { word: pt.word, p: pt.p, s: pt.s }; hovered = pt; }}
							onmouseleave={() => { hover = null; hovered = null; }}
							onfocus={() => { hover = { word: pt.word, p: pt.p, s: pt.s }; hovered = pt; }}
							onblur={() => { hover = null; hovered = null; }}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									tag(pt.word, e.shiftKey ? 'naughty' : 'nice');
								}
							}}
							onclick={() => tag(pt.word, 'nice')}
							oncontextmenu={(e) => tag(pt.word, 'naughty', e)}>{pt.word}</text>
					{/each}
					<!--
					  THE HOVERED WORD, PAINTED AGAIN AND LAST. SVG has no z-index and
					  paints in document order, so CSS cannot raise a <text> out of the
					  pile it is buried in. Re-drawing it after the loop is what makes
					  "overlap is fine if hover shows what is underneath" true rather
					  than merely intended. The halo is a stroke UNDER the fill, so the
					  glyph itself is not thickened.
					-->
					{#if hovered}
						<text class="raised" x={(hovered.cx * vbW) / 100} y={hovered.cy}
							class:tn={naughty.has(hovered.word)} class:tc={nice.has(hovered.word)}
						>{hovered.word}</text>
					{/if}
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
					<span class="ylab">
						y = probability, placed on log10
						<!--
						  THE LABEL WINDOW, DECLARED. All {pts.length} points are
						  plotted; only the highest-probability ones carry text,
						  because the log floor overprints. A reader must not have to
						  infer that the words they can read are all the words there
						  are — same rule as the row cap on a result table.
						-->
						&middot; all {pts.length} labelled, overlapping
						&mdash; hover raises one out of the pile
					</span>
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
	/* RH, 2026-08-17: "still not using full width of page". The 1100px measure
	   was a reading width, and it was capping the PLOT as well as the prose. Gone
	   from the panel; the only thing that still wants a measure is the yaml
	   preview, which is read rather than looked at. */
	.slot { max-width: none; }
	header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px; }
	h2 { font-size: 17px; margin: 0; letter-spacing: -0.2px; }
	.sub { font-size: 12px; color: var(--text-3); }

	.controls { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
	.controls.small { font-size: 11px; color: var(--text-3); gap: 14px; margin-bottom: 14px; flex-wrap: wrap; }
	.controls.small label { display: flex; gap: 5px; align-items: center; }
	/* The declared pair: offered, and visibly a different kind of thing from the
	   free-text field beside it. */
	.pair { display: flex; gap: 7px; align-items: baseline; white-space: nowrap; }
	.pairids { font-family: var(--mono); font-size: 9.5px; color: var(--text-3); }
	.prompt { flex: 1; font-size: 13px; }
	.pairsel { max-width: 340px; font-size: 11px; }
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
	/* Movement is a different KIND of quantity from the screening statistics
	   beside it — a contrast, not a level — so it is tinted rather than left to
	   read as one more scalar in the row. */
	.branch.mv .lbl { color: var(--red-light); }
	.branch.mv .val { color: var(--red-light); }
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
	/* RH, 2026-08-17: the graph should take the page. `vh` rather than a flex
	   fill because `main` scrolls now — a flex-grown child of a scrolling
	   container collapses to its content. The word list below is still reachable
	   by scrolling, which is the same fix as the scroll complaint. */
	/* Height is set inline from the measured fit; this is the pre-hydration fallback. */
	.scatter { width: 100%; height: 420px; display: block; overflow: visible; }
	/* 2.8 user units of a 100-unit viewBox: 2.4 was too small at this size and
	   3.2 too large (RH, both by looking). The budget is legibility against
	   overprinting and it has no better justification than the rendered image,
	   so re-check it the same way if the geometry changes. */
	.scatter text {
		font-family: var(--mono); font-size: 2.8px; fill: var(--text-2);
		cursor: pointer; text-anchor: middle;
	}
	.scatter text:hover { fill: #fff; }
	/* THE CLICK ARTIFACT (RH, 2026-08-17: "this big post-click thing"). Clicking
	   an SVG <text role="button" tabindex="0"> leaves it focused, and the browser
	   paints its default focus indicator over the plot until something else is
	   clicked. `:focus-visible` fires for KEYBOARD focus only, so the indicator
	   survives where it is the only way to see where you are and disappears where
	   the pointer already told you. Removing `:focus` outright would have taken
	   the keyboard affordance the tabindex exists for. */
	.scatter text:focus { outline: none; }
	.scatter text:focus-visible {
		outline: none;
		fill: #fff;
		paint-order: stroke;
		stroke: var(--blue-light);
		stroke-width: 0.6px;
		stroke-linejoin: round;
	}
	/* The raised copy: a halo stroke painted UNDER the fill so the glyph is not
	   thickened, and pointer-events off so it cannot steal the hover from the
	   text beneath it and flicker. */
	.scatter text.raised {
		fill: #fff;
		paint-order: stroke;
		stroke: var(--ground);
		stroke-width: 1.1px;
		stroke-linejoin: round;
		font-weight: 700;
		pointer-events: none;
	}
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
		max-width: 1100px;
		margin-top: 14px; padding: 10px; background: var(--panel);
		border: 1px solid var(--rule); border-radius: 4px; color: var(--text-2);
		font-family: var(--mono); font-size: 11px; white-space: pre-wrap; user-select: all;
	}

	.badge {
		font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase;
		padding: 3px 7px; border: 1px solid var(--rule); border-radius: 3px;
		color: var(--text-2); background: var(--panel); cursor: help; white-space: nowrap;
	}
	.badge.warn { border-color: var(--amber, #b8860b); color: var(--amber, #b8860b); }

	/* ── saving ─────────────────────────────────────────────────────────── */
	.saverow {
		display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
		margin-top: 8px;
	}
	.censustog {
		font: inherit;
		font-size: 0.72rem;
		background: transparent;
		border: 1px solid var(--line, #d8d8d4);
		border-radius: 3px;
		padding: 0.1rem 0.4rem;
		cursor: pointer;
		color: var(--dim, #6b6b66);
	}
	.censustog.on,
	.censustog:hover {
		background: var(--soft, #f0f0ec);
		color: inherit;
	}
	.census {
		margin: 0.35rem 0 0.15rem;
		padding: 0.4rem 0.5rem;
		border: 1px solid var(--line, #d8d8d4);
		border-radius: 3px;
		background: var(--soft, #fafaf7);
	}
	.censushead {
		display: flex;
		flex-wrap: wrap;
		gap: 0.15rem 0.8rem;
		font-size: 0.72rem;
		margin-bottom: 0.3rem;
	}
	.censustab {
		border-collapse: collapse;
		font-size: 0.72rem;
		width: 100%;
		max-width: 34rem;
	}
	.censustab th {
		text-align: left;
		font-weight: 500;
		color: var(--dim, #6b6b66);
		border-bottom: 1px solid var(--line, #d8d8d4);
		padding: 0 0.4rem 0.12rem 0;
	}
	.censustab td {
		padding: 0.06rem 0.4rem 0.06rem 0;
		white-space: nowrap;
	}
	.censustab th.n,
	.censustab td.n {
		text-align: right;
		font-variant-numeric: tabular-nums;
		width: 3.1rem;
	}
	.censustab .tot {
		font-weight: 600;
	}
	.censustab .mine {
		color: #1a6b3a;
		font-weight: 600;
	}
	.censustab .need {
		color: var(--dim, #6b6b66);
	}
	/* A zero row is CONTENT -- it is the domain worth authoring next -- so it is
	   dimmed only enough to read as empty, never hidden. */
	.censustab tr.zero .dom {
		color: var(--dim, #8b8b86);
	}
	.censustab tr.untag .dom {
		font-style: italic;
		color: #8a6d3b;
	}
	.censustab .dom {
		width: 12rem;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.offlist {
		color: #8a6d3b;
		padding-left: 0.1rem;
	}
	.censustab td.bar,
	.censustab th.bar {
		width: auto;
		min-width: 6rem;
		padding-right: 0.5rem;
	}
	.seg {
		display: inline-block;
		height: 0.5rem;
		vertical-align: middle;
	}
	.seg.r3 {
		background: #b9c6d6;
	}
	.seg.au {
		background: #2f7a4d;
	}
	.collide {
		font-size: 0.7rem;
		margin-top: 0.3rem;
		color: #8a6d3b;
	}
	.collide code {
		margin-left: 0.3rem;
	}
	.domainin {
		flex: 0 0 150px; padding: 5px 8px;
		background: var(--panel); border: 1px solid var(--rule); border-radius: 4px;
		color: var(--text); font-family: inherit; font-size: 12px;
	}
	.notein {
		flex: 1 1 200px; min-width: 150px; padding: 5px 8px;
		background: var(--panel); border: 1px solid var(--rule); border-radius: 4px;
		color: var(--text); font-family: inherit; font-size: 12px;
	}
	.saverow .ok { color: var(--ok, #2f9e44); font-size: 12px; font-family: var(--mono); }
	.saverow .bad { color: var(--bad, #c92a2a); font-size: 12px; }
	/* The overwrite button is the only destructive control on this panel, so it
	   does not look like the others. It appears ONLY after a refusal — there is
	   no way to reach it without first having been told what it would replace. */
	button.danger { border-color: var(--bad, #c92a2a); color: var(--bad, #c92a2a); }
</style>
