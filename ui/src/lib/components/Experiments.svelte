<!--
  The experiments view: the hypothesis register, and one page per question.

  THE REGISTER IS THE HOME SCREEN. `experiments/README.md` is the file the repo
  designates as the index of every registered hypothesis and its status, and it
  exists because separating instrument registrations from hypothesis ones made
  the hypotheses hard to FIND -- *"separation without an index is just
  scattering"*. Putting anything else first would rebuild the scattering in a
  new medium.

  A QUESTION PAGE SHOWS THREE THINGS IN THIS ORDER, and the order is the
  argument: the README (the claim and its result), the population receipt (what
  it was computed over), then the grains (the rows the summary is derived from).
  `RESULTS.md` §3 says a result is not quotable until you can answer, from the
  artifact alone: which models, which prompts, what was excluded, and can the
  summary be re-derived. That is exactly these three panels, in that sequence.
-->
<script lang="ts">
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import { api } from '$lib/api';
	//: ALIASED BECAUSE THE COMPONENT IS ALSO CALLED `Experiments`. Inside its own
	//: module the file's implicit component name shadows the imported type, and
	//: `index: Experiments | null` then narrowed to `never` -- so every field
	//: access on it was a type error, including the `register_md` test that
	//: decides whether the register link renders. The behaviour was correct at
	//: runtime; the checker was right that the annotation was not.
	import type {
		Experiments as ExperimentIndex,
		Question,
		QuestionDetail,
		ResultRows,
		ResultJson
	} from '$lib/api';
	import Markdown from './Markdown.svelte';
	import DataTable from './DataTable.svelte';
	import VegaChart from './VegaChart.svelte';

	let index: ExperimentIndex | null = $state(null);
	let selected: string | null = $state(null);
	let detail: QuestionDetail | null = $state(null);
	let pane: string = $state('readme');
	let rows: ResultRows | null = $state(null);
	let blob: ResultJson | null = $state(null);
	let doc: string | null = $state(null);
	let openGroups: Record<string, boolean> = $state({});
	let error = $state('');
	let loading = $state(false);

	//: URL-BACKED SELECTION (RH: "i can't send you a link"). `q` is the question
	//: and `p` the open pane, written on every click and read once on mount, so
	//: a link reopens the same document rather than the panel's default.
	function syncUrl() {
		const u = new URL(page.url);
		u.searchParams.set('s', 'experiments');
		if (selected) u.searchParams.set('q', selected);
		else u.searchParams.delete('q');
		if (selected && pane) u.searchParams.set('p', pane);
		else u.searchParams.delete('p');
		replaceState(u, {});
	}

	async function loadIndex() {
		try {
			index = await api.experiments();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	loadIndex().then(() => {
		//: RESTORE AFTER THE INDEX, not on mount: `open()` needs the question to
		//: exist, and a link naming one that has since been renamed should land on
		//: the register rather than on an error.
		const q = page.url.searchParams.get('q');
		if (q?.startsWith('subject:')) {
			openSubject(q.slice(8));
			return;
		}
		if (!q || !index?.questions.some((x) => x.id === q)) return;
		const p = page.url.searchParams.get('p');
		open(q).then(() => {
			if (!p) return;
			if (p.startsWith('fig:') || ['readme', 'registration', 'population'].includes(p)) pane = p;
			else if (detail?.results.some((r) => r.grain === p)) openGrain(p);
		});
	});

	//: A SUBJECT OPENS ITS README AND NOTHING ELSE. It is held in `detail` with a
	//: `subject:` prefix so the existing selection highlight and URL sync work
	//: unchanged, and with empty results/figures so the tiers below render as
	//: the honest empty -- a subject HAS no results, and showing borrowed ones
	//: from its children would be the second-status defect the register avoids.
	function openSubject(name: string) {
		const s = index?.subjects?.[name];
		if (!s) return;
		selected = 'subject:' + name;
		detail = {
			id: name, name, subject: null, has: {}, results: [], figures: [],
			readme_md: s.readme_md, registration_md: null, population: null
		} as unknown as QuestionDetail;
		pane = 'readme';
		rows = blob = null;
		doc = null;
		error = '';
		syncUrl();
	}

	async function open(id: string) {
		selected = id;
		pane = 'readme';
		rows = blob = null;
		detail = null;
		error = '';
		loading = true;
		try {
			detail = await api.experiment(id);
			//: A QUESTION WITH NO README OPENS ON ITS REGISTRATION. `register_shift`
			//: is registered and not run, so `readme` would be an empty panel for the
			//: one question whose state is most worth seeing. Falling through to the
			//: file that does exist is not a nicety: an empty default reads as "this
			//: experiment has nothing", which is the opposite of "frozen, awaiting a
			//: producer".
			if (!detail.readme_md && detail.registration_md) pane = 'registration';
			syncUrl();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	//: GROUPED, NOT LISTED. `displacement_taxonomy` has 82 results and the flat
	//: strip rendered 82 chips, which is a directory listing pretending to be
	//: navigation: the three documents that say what the experiment FOUND sat
	//: between `xling_he_kicked_the.json` and `xling_he_pinched_her.json`.
	//:
	//: Three tiers, and the order is the argument. DOCUMENTS first because a
	//: finding written in prose is what a reader wants and is the rarest thing
	//: in the folder; TABLES second because they are queryable; everything else
	//: folded into collapsed groups by filename prefix, since a family of 40
	//: per-prompt state files is ONE thing to the reader and forty to the
	//: filesystem.
	const DOC_EXT = ['.md', '.txt'];
	const TAB_EXT = ['.csv'];
	function ext(g: string) {
		const i = g.lastIndexOf('.');
		return i < 0 ? '' : g.slice(i);
	}
	//: A REAL DIRECTORY IS ITS OWN GROUP AND OUTRANKS A NAME PREFIX. The backend
	//: now walks one level into results/, so a grain may be `word_groups/x.txt`.
	//: Grouping that by its leading token would scatter 40 documents that the
	//: producer deliberately put in one place, and mix them with unrelated files
	//: sharing four letters.
	function prefix(g: string) {
		const slash = g.indexOf('/');
		if (slash > 0) return g.slice(0, slash) + '/';
		const stem = g.slice(0, g.length - ext(g).length);
		const m = stem.match(/^[A-Za-z0-9]+/);
		return m ? m[0] : stem;
	}
	let resultTree = $derived.by(() => {
		const rs = detail?.results ?? [];
		//: THE TOP TIERS ARE TOP-LEVEL ONLY. `word_groups/` holds 40 .txt files
		//: and `batches/` 91; promoting them to `documents` would bury the three
		//: findings the tier exists to surface under 131 machine-written inputs.
		//: A directory stays a directory.
		const top = rs.filter((r) => !r.grain.includes('/'));
		const nested = rs.filter((r) => r.grain.includes('/'));
		const docs = top.filter((r) => DOC_EXT.includes(ext(r.grain)));
		const tabs = top.filter((r) => TAB_EXT.includes(ext(r.grain)));
		const rest = [
			...top.filter(
				(r) => !DOC_EXT.includes(ext(r.grain)) && !TAB_EXT.includes(ext(r.grain))
			),
			...nested
		];
		const by = new Map<string, typeof rest>();
		for (const r of rest) {
			const k = prefix(r.grain);
			if (!by.has(k)) by.set(k, []);
			by.get(k)!.push(r);
		}
		//: A prefix shared by ONE file is not a group, it is a file with a long
		//: name. Those go to `loose` rather than each becoming a collapsed
		//: heading the reader has to open to find a single item.
		const groups: { key: string; items: typeof rest }[] = [];
		const loose: typeof rest = [];
		for (const [k, items] of [...by].sort((a, b) => b[1].length - a[1].length)) {
			if (items.length > 1) groups.push({ key: k, items });
			else loose.push(items[0]);
		}
		return { docs, tabs, groups, loose };
	});

	async function openGrain(grain: string) {
		if (!selected) return;
		pane = grain;
		rows = blob = null;
		doc = null;
		error = '';
		loading = true;
		try {
			syncUrl();
			const r = await api.result(selected, grain);
			if ('markdown' in r) doc = (r as { markdown: string }).markdown;
			else if ('json' in r) blob = r as ResultJson;
			else rows = r as ResultRows;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	function backToRegister() {
		selected = null;
		pane = 'readme';
		detail = null;
		rows = blob = null;
		doc = null;
		error = '';
		syncUrl();
	}

	//: FOUND BY READING THE RENDERED HEADINGS, not by matching a line in the
	//: markdown source. The rendered DOM is what the reader is looking at, so a
	//: heading the renderer did not produce is one the jump must not offer.
	let registerEl: HTMLElement | null = $state(null);
	//: BOUND ONCE, THEN TESTED. Written as `!!index?.register_md && test(index.register_md)`
	//: the second access re-reads a value the checker has narrowed to `never`
	//: inside `$derived`, and both accesses errored. Reading it into a local is
	//: the same logic with one access, and it is also the honest shape: the test
	//: is about the STRING, not about `index`.
	let hasRegister = $derived.by(() => {
		const md = index?.register_md;
		return !!md && /^#+\s.*HYPOTHESIS REGISTER/im.test(md);
	});

	function scrollToRegister() {
		const root = registerEl?.parentElement;
		if (!root) return;
		const h = [...root.querySelectorAll('h1, h2, h3')].find((el) =>
			/HYPOTHESIS REGISTER/i.test(el.textContent ?? '')
		);
		h?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	//: Grouped by SUBJECT, because `experiments/README.md` makes the subject level
	//: meaningful: a subject appears only by PROMOTION when a second question
	//: arrives, so a subject with children is a fact about the work rather than a
	//: filing choice. Flat questions are listed first and unheaded.
	//: A FOLDER CAN BE BOTH, AND slot_ratings IS. It carries `run.py`, `plot.py`
	//: and 1,266 result grains of its own AND holds three questions, so it
	//: qualified as a question (landing in `flat`) and as a subject (heading its
	//: children) and rendered TWICE, once at the top of the list and again as the
	//: heading below. Both entries opened the same `slot_ratings/README.md`.
	//:
	//: Resolved toward ONE row rather than by dropping either role: the heading
	//: becomes the question, so clicking `SLOT_RATINGS` gives the README, the
	//: figures and the 1,266 grains instead of the stripped subject view. Nothing
	//: is lost and the hierarchy stops claiming a folder is in two places.
	//: `division_of_labour` is unaffected -- it holds no code and no results, so
	//: it is a subject only, exactly as its own README declares.
	let grouped = $derived.by(() => {
		const flat: Question[] = [];
		const subs = new Map<string, Question[]>();
		for (const q of index?.questions ?? []) {
			if (q.subject) {
				if (!subs.has(q.subject)) subs.set(q.subject, []);
				subs.get(q.subject)!.push(q);
			} else flat.push(q);
		}
		//: Built AFTER the loop: a parent can be walked before or after its own
		//: children depending on the server's ordering, so deciding inside the
		//: loop would depend on which arrived first.
		const asSubject = new Map<string, Question>();
		for (const q of flat) if (subs.has(q.id)) asSubject.set(q.id, q);
		return {
			flat: flat.filter((q) => !asSubject.has(q.id)),
			subs: [...subs.entries()].sort(),
			asSubject
		};
	});

	//: **DIVIDE ONCE PER UNIT.** The first version was
	//:     n < 1048576 ? (n/1024).toFixed(0)+' KB' : (n/1024).toFixed(1)+' MB'
	//: which divides by 1024 ONCE and then calls the result MB, so `cells.csv`
	//: rendered as **36270.6 MB** -- a 37 MB file reported as 36 GB.
	//:
	//: Nothing could catch this but looking. It compiles, the type is right, the
	//: shape is a number beside a unit, and both branches are individually
	//: plausible; the KB branch is even correct. It was caught by rendering the
	//: panel and reading it, which is the check that finds what a review of the
	//: code does not, because the reviewer already believes the formula.
	//: DISPLAY ONLY. The subject key is a path and a single underscored token, so
	//: it has no break opportunity and CSS split it mid-word. Spaces give the
	//: wrapper somewhere to break. The id is never transformed -- `open()` and
	//: `openSubject()` still receive `subject`.
	const head = (subject: string) => subject.split('/').pop()!.replace(/_/g, ' ');

	const bytes = (n: number) => {
		if (n < 1024) return `${n} B`;
		if (n < 1048576) return `${Math.round(n / 1024)} KB`;
		if (n < 1073741824) return `${(n / 1048576).toFixed(1)} MB`;
		return `${(n / 1073741824).toFixed(2)} GB`;
	};
</script>

<div class="experiments">
	<nav>
		<button class="reg" class:on={!selected} onclick={backToRegister}>
			Hypothesis register
			<span class="sub">experiments/README.md</span>
		</button>

		{#each grouped.flat as q (q.id)}
			<button class="q" class:on={selected === q.id} onclick={() => open(q.id)}>
				{q.name}
				<span class="tags">
					{#if q.has['registration.md']}<span class="tag" title="a frozen registration exists">reg</span>{/if}
					{#if q.results.length}<span class="tag n">{q.results.length}</span>{/if}
				</span>
			</button>
		{/each}

		{#each grouped.subs as [subject, qs] (subject)}
			<!--
			  THE HEADING IS A BUTTON WHEN THE SUBJECT HAS A README (RH). A subject
			  folder is not an experiment and is deliberately not listed among its
			  own children -- `division_of_labour/README.md` says so in as many
			  words -- but it does carry the subject's QUESTION, and rendering it
			  as inert text made that unreadable from the panel. Subjects without
			  a README stay inert, because there is nothing to open.
			-->
			{#if grouped.asSubject.get(subject)}
				<!-- The subject folder is itself a question: open the question. -->
				<button class="subject link" class:on={selected === subject}
					onclick={() => open(subject)}
					>{head(subject)}<span class="tag n"
						>{grouped.asSubject.get(subject)!.results.length}</span
					></button
				>
			{:else if index?.subjects?.[subject]}
				<button class="subject link" class:on={selected === 'subject:' + subject}
					onclick={() => openSubject(subject)}
					>{head(subject)}<span class="tag n">readme</span></button
				>
			{:else}
				<div class="subject">{head(subject)}</div>
			{/if}
			{#each qs as q (q.id)}
				<button class="q indent" class:on={selected === q.id} onclick={() => open(q.id)}>
					{q.name}
					<span class="tags">
						{#if q.has['registration.md']}<span class="tag">reg</span>{/if}
						{#if q.results.length}<span class="tag n">{q.results.length}</span>{/if}
					</span>
				</button>
			{/each}
		{/each}
	</nav>

	<section>
		{#if error}
			<p class="err">{error}</p>
		{/if}

		{#if !selected}
			<!--
			  THE JUMP EXISTS BECAUSE THE FILE'S ORDER IS NOT THE READER'S ORDER.
			  `experiments/README.md` opens with the directory conventions and puts
			  THE HYPOTHESIS REGISTER two thirds of the way down. That is right for
			  the file -- a seat creating an experiment needs the rules first -- and
			  wrong for this panel, which is labelled "the register" and lands the
			  reader on `01_ encodes creation order`.

			  Fixed by moving the READER, not the file. Parsing the register into
			  cards would put the statuses in a second place; scrolling to the
			  heading leaves one copy and starts you at it. The control is rendered
			  only if the heading is actually found, so it cannot advertise a
			  destination that a rewritten README no longer has.
			-->
			<div class="jump" bind:this={registerEl}>
				{#if hasRegister}
					<button class="ghost" onclick={() => scrollToRegister()}>jump to the register ↓</button>
					<span class="muted">the file opens with the directory conventions</span>
				{/if}
			</div>
			<Markdown src={index?.register_md ?? null} />
		{:else if detail}
			<header>
				<h2>{detail.name}</h2>
				<span class="path num">experiments/{detail.id}</span>
			</header>

			<div class="panes">
				<button class="ghost" class:on={pane === 'readme'} disabled={!detail.readme_md}
					onclick={() => { pane = 'readme'; syncUrl(); }}>README</button>
				<button class="ghost" class:on={pane === 'registration'} disabled={!detail.registration_md}
					onclick={() => { pane = 'registration'; syncUrl(); }}>registration</button>
				<button class="ghost" class:on={pane === 'population'} disabled={!detail.population}
					onclick={() => { pane = 'population'; syncUrl(); }}>population</button>
			</div>

			{#if resultTree.docs.length}
				<div class="paneswitch figrow">
					<span class="rowlbl">documents</span>
					{#each resultTree.docs as r (r.grain)}
						<button class="ghost grain doc" class:on={pane === r.grain}
							onclick={() => openGrain(r.grain)}
							>{r.grain}<span class="bytes">{bytes(r.bytes)}</span></button>
					{/each}
				</div>
			{/if}

			{#if resultTree.tabs.length}
				<div class="paneswitch figrow">
					<span class="rowlbl">tables</span>
					{#each resultTree.tabs as r (r.grain)}
						<button class="ghost grain" class:on={pane === r.grain}
							onclick={() => openGrain(r.grain)}
							>{r.grain}<span class="bytes">{bytes(r.bytes)}</span></button>
					{/each}
				</div>
			{/if}

			{#if resultTree.groups.length || resultTree.loose.length}
				<div class="paneswitch figrow">
					<span class="rowlbl">data</span>
					{#each resultTree.groups as g (g.key)}
						<button class="ghost folder" class:open={openGroups[g.key]}
							onclick={() => (openGroups = { ...openGroups, [g.key]: !openGroups[g.key] })}
							>{openGroups[g.key] ? '▾' : '▸'} {g.key}<span class="tag n">{g.items.length}</span
							></button>
					{/each}
					{#each resultTree.loose as r (r.grain)}
						<button class="ghost grain" class:on={pane === r.grain}
							onclick={() => openGrain(r.grain)}
							>{r.grain}<span class="bytes">{bytes(r.bytes)}</span></button>
					{/each}
				</div>
				{#each resultTree.groups as g (g.key)}
					{#if openGroups[g.key]}
						<div class="paneswitch figrow nested">
							<span class="rowlbl">{g.key}</span>
							{#each g.items as r (r.grain)}
								<button class="ghost grain" class:on={pane === r.grain}
									onclick={() => openGrain(r.grain)}
									>{g.key.endsWith('/')
											? r.grain.slice(g.key.length)
											: r.grain.slice(g.key.length).replace(/^[_-]/, '')}<span class="bytes"
										>{bytes(r.bytes)}</span
									></button>
							{/each}
						</div>
					{/if}
				{/each}
			{/if}

			<!--
			  WHAT WAS NOT LISTED, AND WHY. A results subdirectory with no README
			  is skipped by the server (RH, 2026-08-21) -- `slot_ratings/results`
			  alone holds 1,213 per-prompt JSONs across three such directories,
			  which buried the eleven artifacts a reader wants. Skipping them
			  silently would make the grain count a claim about what was drawn
			  rather than about the folder, so the panel says what is missing and
			  how to get it back. One README, one command.
			-->
			{#if detail.undocumented?.length}
				<p class="hidden-dirs">
					not listed, no README:
					{#each detail.undocumented as u, i (u.dir)}<code>{u.dir}/</code>
						<span class="n">{u.files}</span>{i < detail.undocumented.length - 1 ? ', ' : ''}{/each}
					<span class="how">— add a <code>README.md</code> to list one</span>
				</p>
			{/if}

			<!--
			  FIGURES GET THEIR OWN ROW (RH, 2026-08-17), because a figure is not a
			  grain: a result is read as rows and a figure is looked at, and mixing
			  them in one strip makes the click ambiguous.

			  THE ROW IS SHOWN EVEN WHEN EMPTY, and that is deliberate. Exactly one
			  figure was committed repo-wide when this was written, so an absent row
			  would render "no figures" as "no figures ROW" — and the plot debt is
			  the thing most worth seeing at the place the results are already being
			  read. An empty row is a measurement.
			-->
			<div class="paneswitch figrow">
				<span class="rowlbl">figures</span>
				{#if detail.figures.length}
					{#each detail.figures as f (f)}
						<button class="ghost grain" class:on={pane === 'fig:' + f}
							onclick={() => { pane = 'fig:' + f; syncUrl(); }}>{f}</button>
					{/each}
				{:else}
					<span class="muted none">none — this experiment has produced no figure</span>
				{/if}
			</div>

			{#if pane.startsWith('fig:')}
				<!--
				  Full width, natural aspect, and a link to the file itself. These
				  are 300 dpi artifacts — the same PNG a paper would use — so the
				  panel shows it scaled and "open" hands over the original rather
				  than re-rendering anything.
				-->
				<!--
				  THREE KINDS OF FILE LIVE IN `figures/` AND ONLY ONE IS AN IMAGE.
				  The server lists every file in the folder, so before this branch
				  existed a Vega-Lite spec and this repo's `figures/README.md` were
				  both handed to an <img>, which renders a broken-image icon and
				  reads as a missing figure rather than as the wrong element.

				  A SPEC IS IDENTIFIED BY THE SERVER'S `specs` LIST, not by its
				  extension here. The manifest is where the directory was read.
				-->
				{#if detail.specs?.includes(pane.slice(4))}
					<VegaChart url={api.figureUrl(selected, pane.slice(4))} name={pane.slice(4)} />
				{:else if /\.(png|svg|jpe?g|webp)$/i.test(pane.slice(4))}
					<figure class="fig">
						<img src={api.figureUrl(selected, pane.slice(4))} alt={pane.slice(4)} />
						<figcaption>
							<code>{pane.slice(4)}</code>
							<a href={api.figureUrl(selected, pane.slice(4))} target="_blank" rel="noreferrer"
								>open full size</a
							>
						</figcaption>
					</figure>
				{:else}
					<p class="muted">
						<code>{pane.slice(4)}</code> is not an image or a spec —
						<a href={api.figureUrl(selected, pane.slice(4))} target="_blank" rel="noreferrer"
							>open it</a
						>
					</p>
				{/if}
			{:else if loading}
				<p class="muted">reading…</p>
			{:else if pane === 'readme'}
				<Markdown src={detail.readme_md} />
			{:else if pane === 'registration'}
				<!--
				  A REGISTRATION IS FROZEN AND THE PANEL SAYS SO. It is the one
				  document here that is worth less the moment it can be edited, and
				  a reader arriving at it from a result needs to know they are
				  looking at what was committed BEFORE the number, not a description
				  of the design written after.
				-->
				<p class="declare">frozen before the first run &mdash; amendments append with a date, never edit</p>
				<Markdown src={detail.registration_md} />
			{:else if pane === 'population'}
				<p class="declare">
					the MEMBERSHIP half of the population declaration, verbatim from
					population.json &mdash; the RULE lives in run.py
				</p>
				<pre class="json">{JSON.stringify(detail.population, null, 2)}</pre>
			{:else if rows}
				<DataTable data={rows} />
			{:else if doc !== null}
				<Markdown src={doc} />
			{:else if blob}
				<pre class="json">{JSON.stringify(blob.json, null, 2)}</pre>
			{/if}
		{/if}
	</section>
</div>

<style>
	.experiments {
		display: grid;
		grid-template-columns: 232px 1fr;
		gap: 22px;
		height: 100%;
		overflow: hidden;
	}
	nav {
		overflow-y: auto;
		padding-right: 4px;
		border-right: 1px solid var(--rule);
	}
	section {
		overflow-y: auto;
		padding-right: 14px;
		padding-bottom: 40px;
	}

	nav button {
		display: block;
		width: 100%;
		text-align: left;
		background: none;
		border: 0;
		border-radius: 4px;
		padding: 6px 9px;
		cursor: pointer;
		color: var(--text-2);
		font-size: 12.5px;
		margin-bottom: 1px;
	}
	nav button:hover {
		background: rgba(255, 255, 255, 0.04);
		color: var(--text);
	}
	nav button.on {
		background: rgba(78, 121, 167, 0.16);
		color: #fff;
	}
	.reg {
		margin-bottom: 12px;
		line-height: 1.35;
	}
	.reg .sub {
		display: block;
		font-family: var(--mono);
		font-size: 10px;
		color: var(--text-3);
	}
	.subject.link {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		background: none;
		border: 0;
		cursor: pointer;
		text-align: left;
		font: inherit;
	}
	.subject.link:hover,
	.subject.link.on {
		color: var(--fg, #e6e6e6);
	}
	/*
	  THE HEADING WRAPS RATHER THAN CLIPPING. `INSTRUMENT_CALIBRATIONS` and
	  `POSTTRAINING_CORPUS_ANALYSIS` ran off the right edge of the panel and the
	  `readme` badge on `DIVISION_OF_LABOUR` went with them -- uppercase plus
	  0.07em tracking makes these the widest strings in the sidebar, and nothing
	  was set to contain them. Caught by screenshotting the panel; the markup and
	  the strings are both correct, so only the render shows it.
	*/
	.subject {
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		color: var(--text-3);
		margin: 14px 0 4px 9px;
		padding-right: 9px;
		max-width: 100%;
		line-height: 1.35;
		text-align: left;
	}
	/* The count must not be dragged onto its own line by a wrapping heading. */
	.subject .tag {
		white-space: nowrap;
		flex: 0 0 auto;
	}
	.q.indent {
		padding-left: 18px;
	}
	.tags {
		float: right;
		display: flex;
		gap: 4px;
	}
	.tag {
		font-family: var(--mono);
		font-size: 9px;
		padding: 1px 4px;
		border-radius: 2px;
		background: var(--panel-2);
		color: var(--text-3);
	}
	.tag.n {
		background: rgba(78, 121, 167, 0.2);
		color: var(--blue-light);
	}
	.hidden-dirs {
		margin: 6px 0 0 9px;
		font-size: 11px;
		color: var(--text-3);
	}
	.hidden-dirs code {
		font-size: 11px;
		color: var(--text-2);
	}
	.hidden-dirs .n {
		color: var(--blue-light);
	}
	.hidden-dirs .how {
		opacity: 0.7;
	}
	/*
	  THE `no run.py` BADGE IS GONE (RH, 2026-08-21). It was added so a question
	  with no producer was marked rather than hidden, and it did that -- but the
	  repo's naming convention outgrew it: `analyse.py`, `run_f21.py`,
	  `run_m03.py`, `base_side_positions.py` are all producers, and a folder full
	  of them was flagged as having none. A red badge that is wrong most of the
	  time trains a reader to ignore the one time it is right.

	  The `has` map still carries `run.py` from the server, so a future check can
	  use it -- what was removed is the CLAIM, not the fact.
	*/

	header {
		display: flex;
		align-items: baseline;
		gap: 12px;
		margin-bottom: 12px;
	}
	h2 {
		font-size: 17px;
		margin: 0;
		letter-spacing: -0.2px;
	}
	.path {
		font-size: 11px;
		color: var(--text-3);
	}
	.panes {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		margin-bottom: 14px;
		padding-bottom: 12px;
		border-bottom: 1px solid var(--rule);
	}
	.figrow { margin-top: 6px; align-items: center; }
	.rowlbl {
		font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em;
		color: var(--text-2); margin-right: 4px;
	}
	.figrow .none { font-size: 11px; }
	.fig { margin: 12px 0 0; }
	.fig img {
		width: 100%; height: auto; display: block;
		border: 1px solid var(--rule); border-radius: 4px; background: #fff;
	}
	.fig figcaption {
		display: flex; gap: 12px; align-items: center;
		margin-top: 6px; font-size: 11px; color: var(--text-2);
	}
	.folder {
		font-weight: 600;
	}
	.folder.open {
		border-color: var(--accent, #8ab4f8);
	}
	.nested {
		padding-left: 14px;
		border-left: 2px solid var(--rule);
	}
	.doc {
		font-weight: 600;
	}
	.grain {
		font-family: var(--mono);
		font-size: 10.5px;
	}
	.bytes {
		color: var(--text-3);
		margin-left: 6px;
	}
	.jump {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 14px;
		font-size: 11px;
	}
	.json {
		background: var(--panel);
		border: 1px solid var(--rule);
		border-radius: 4px;
		padding: 12px;
		font-family: var(--mono);
		font-size: 11px;
		line-height: 1.5;
		color: var(--text-2);
		overflow-x: auto;
		max-height: 62vh;
	}
</style>
