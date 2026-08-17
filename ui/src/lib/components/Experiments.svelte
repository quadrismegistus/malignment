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
	import { api } from '$lib/api';
	import type { Experiments, QuestionDetail, ResultRows, ResultJson } from '$lib/api';
	import Markdown from './Markdown.svelte';
	import DataTable from './DataTable.svelte';

	let index: Experiments | null = $state(null);
	let selected: string | null = $state(null);
	let detail: QuestionDetail | null = $state(null);
	let pane: string = $state('readme');
	let rows: ResultRows | null = $state(null);
	let blob: ResultJson | null = $state(null);
	let error = $state('');
	let loading = $state(false);

	async function loadIndex() {
		try {
			index = await api.experiments();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	loadIndex();

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
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function openGrain(grain: string) {
		if (!selected) return;
		pane = grain;
		rows = blob = null;
		error = '';
		loading = true;
		try {
			const r = await api.result(selected, grain);
			if ('json' in r) blob = r as ResultJson;
			else rows = r as ResultRows;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	function backToRegister() {
		selected = null;
		detail = null;
		rows = blob = null;
		error = '';
	}

	//: FOUND BY READING THE RENDERED HEADINGS, not by matching a line in the
	//: markdown source. The rendered DOM is what the reader is looking at, so a
	//: heading the renderer did not produce is one the jump must not offer.
	let registerEl: HTMLElement | null = $state(null);
	let hasRegister = $derived(!!index?.register_md && /^#+\s.*HYPOTHESIS REGISTER/im.test(index.register_md));

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
	let grouped = $derived.by(() => {
		const flat: typeof index.questions = [];
		const subs = new Map<string, typeof index.questions>();
		for (const q of index?.questions ?? []) {
			if (q.subject) {
				if (!subs.has(q.subject)) subs.set(q.subject, []);
				subs.get(q.subject)!.push(q);
			} else flat.push(q);
		}
		return { flat, subs: [...subs.entries()].sort() };
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
					{#if !q.has['run.py']}<span class="tag noprod" title="registered, no producer yet">no run.py</span>{/if}
					{#if q.has['registration.md']}<span class="tag" title="a frozen registration exists">reg</span>{/if}
					{#if q.results.length}<span class="tag n">{q.results.length}</span>{/if}
				</span>
			</button>
		{/each}

		{#each grouped.subs as [subject, qs] (subject)}
			<div class="subject">{subject}</div>
			{#each qs as q (q.id)}
				<button class="q indent" class:on={selected === q.id} onclick={() => open(q.id)}>
					{q.name}
					<span class="tags">
						{#if !q.has['run.py']}<span class="tag noprod">no run.py</span>{/if}
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
					onclick={() => (pane = 'readme')}>README</button>
				<button class="ghost" class:on={pane === 'registration'} disabled={!detail.registration_md}
					onclick={() => (pane = 'registration')}>registration</button>
				<button class="ghost" class:on={pane === 'population'} disabled={!detail.population}
					onclick={() => (pane = 'population')}>population</button>
				{#each detail.results as r (r.grain)}
					<button class="ghost grain" class:on={pane === r.grain} onclick={() => openGrain(r.grain)}>
						{r.grain}<span class="bytes">{bytes(r.bytes)}</span>
					</button>
				{/each}
			</div>

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
							onclick={() => (pane = 'fig:' + f)}>{f}</button>
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
				<figure class="fig">
					<img src={api.figureUrl(selected, pane.slice(4))} alt={pane.slice(4)} />
					<figcaption>
						<code>{pane.slice(4)}</code>
						<a href={api.figureUrl(selected, pane.slice(4))} target="_blank" rel="noreferrer"
							>open full size</a
						>
					</figcaption>
				</figure>
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
	.subject {
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		color: var(--text-3);
		margin: 14px 0 4px 9px;
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
	/*
	  A QUESTION WITH NO PRODUCER IS MARKED, NOT HIDDEN. `register_shift` holds
	  four frozen hypotheses and no run.py; that is the state most worth seeing in
	  a list, and a list that showed only runnable questions would report this
	  repo as having three experiments when it has four.
	*/
	.tag.noprod {
		background: rgba(225, 87, 89, 0.16);
		color: var(--red-light);
	}

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
