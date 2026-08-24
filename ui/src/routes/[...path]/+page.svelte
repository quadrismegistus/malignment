<!--
  The shell.

  THREE SECTIONS, NOT SEVENTEEN TABS. The archive's app ended at a flat strip of
  17 equal-weight tabs, which is the same disease as 477 scripts in one directory
  expressed in chrome: a container with no hierarchy fills with whatever is
  nearby, and nothing in the interface can say that `Census` and `Sankey` were
  dead six weeks before anyone noticed.

  So the sections mirror the repo's own structure rather than an accumulation:

      Experiments   the hypothesis register and its questions   -- the argument
      Roster        which models am I comparing                 -- the populations
      Slot          what does the model want to say here        -- the instrument

  A fourth section is a claim that a fourth kind of thing exists. That is a
  higher bar than adding a tab, deliberately.

  THE STATUS BADGE NAMES THE DATABASE. The archive's said "connected", which is
  true of a server pointed at any store on this machine -- and this machine also
  runs `lltk` at 409 GiB. A badge that cannot be wrong is not telling you
  anything.
-->
<script lang="ts">
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import { api } from '$lib/api';
	import type { Health } from '$lib/api';
	import Experiments from '$lib/components/Experiments.svelte';
	import Roster from '$lib/components/Roster.svelte';
	import SlotExplorer from '$lib/components/SlotExplorer.svelte';
	import Plots from '$lib/components/Plots.svelte';
	import Prompts from '$lib/components/Prompts.svelte';

	const SECTIONS = [
		{ id: 'experiments', label: 'Experiments', sub: 'the register and its questions' },
		{ id: 'roster', label: 'Roster', sub: 'which models am I comparing' },
		{ id: 'prompts', label: 'Prompts', sub: 'the frames and how much each moves' },
		{ id: 'slot', label: 'Slot', sub: 'what the model wants to say' },
		{ id: 'plots', label: 'Plots', sub: 'registered figures, run on demand' }
	] as const;

	//: THE URL IS THE STATE, so a panel can be sent to someone (RH). Path
	//: segments replace query params, so the link reads as a hierarchy:
	//:
	//:     /experiments/displacement_taxonomy/displacement-categories-7.md
	//:
	//: Query-string form (`?s=experiments&q=...&p=...`) is still read on load so
	//: old bookmarks survive, but every navigation writes path segments.
	//:
	//: `replaceState` rather than `goto`: a click that opens a pane is not a
	//: navigation, and pushing history for each would make Back walk through
	//: every chip the reader touched instead of leaving the app.
	function urlState(): { s: string; q: string; p: string } {
		const segs = page.url.pathname.split('/').filter(Boolean);
		if (segs.length >= 1 && SECTIONS.some((x) => x.id === segs[0])) {
			return { s: segs[0], q: segs[1] ?? '', p: segs.slice(2).join('/') };
		}
		const sp = page.url.searchParams;
		return { s: sp.get('s') ?? '', q: sp.get('q') ?? '', p: sp.get('p') ?? '' };
	}

	function readSection() {
		const { s } = urlState();
		return SECTIONS.some((x) => x.id === s) ? s : 'experiments';
	}
	let section: string = $state(readSection());

	function setSection(id: string) {
		section = id;
		replaceState('/' + id, {});
	}
	let health: Health | null = $state(null);
	let down = $state('');

	async function check() {
		try {
			health = await api.health();
			down = '';
		} catch (e) {
			health = null;
			down = e instanceof Error ? e.message : String(e);
		}
	}
	check();

	//: **POLLED, BECAUSE THIS BADGE GOES STALE AND LOOKS FINE DOING IT.**
	//:
	//: It was called once on mount. RH asked "2 models resident — is that true?"
	//: on 2026-08-16 and it WAS: the two claimed models answered in 0.95s and
	//: 0.76s against 10.2s for a control that was not resident, a 13x gap which
	//: is the model load. But the control call made it three, and the open tab
	//: still said two.
	//:
	//: So the badge is not wrong when written and is wrong within one Slot run,
	//: with nothing on screen to distinguish the two states. A number that was
	//: true when it was rendered is exactly the kind this campaign keeps paying
	//: for.
	//:
	//: `/health` reads a dict and an env var -- no ClickHouse query, no
	//: filesystem walk -- so the poll is close to free and 15s is not a
	//: compromise with cost. **Polling rather than refreshing after a Slot run**,
	//: which would be the narrower fix, because `_SLOT_MODELS` is process state:
	//: a second tab, another seat's curl, or a server restart all change it
	//: without this page doing anything.
	$effect(() => {
		const t = setInterval(check, 15000);
		return () => clearInterval(t);
	});
</script>

<svelte:head><title>malignment</title></svelte:head>

<div class="app">
	<header>
		<div class="left">
			<h1>malignment</h1>
			<span class="tag">On the Psychopathology of Everyday AI</span>
		</div>
		<div class="right">
			{#if health}
				<!--
				  THE SERVER IS RUNNING CODE THAT NO LONGER EXISTS ON DISK.
				  A Python server does not hot-reload, and the failure is invisible:
				  a route added and committed answers "no POST route" until someone
				  notices the process is hours old — which reads as a missing feature
				  rather than a stale process. `stale` is checked explicitly rather
				  than truthily, so an OLDER server that cannot answer (field absent)
				  shows nothing instead of showing "fresh", because "cannot tell you"
				  is not the same claim as "not stale".
				-->
				{#if health.source?.stale === true}
					<span
						class="badge bad num"
						title="This process loaded a different version of: {health.source.changed.join(
							', '
						)}. Started {health.source.booted_at ?? 'unknown'}, pid {health.source
							.pid}. Restart it — the server cannot reload itself without dropping resident models."
						>server stale · restart</span
					>
				{/if}
				<span class="badge ok num">{health.db}</span>
				{#if health.slot_loaded.length}
					<span class="badge blue num" title={health.slot_loaded.join('\n')}>
						{health.slot_loaded.length} model{health.slot_loaded.length > 1 ? 's' : ''} resident
					</span>
				{:else if !health.slot_enabled}
					<span class="badge num" title="started with --no-slot">no slot</span>
				{/if}
			{:else}
				<span class="badge bad num">no server</span>
				<button class="ghost" onclick={check}>retry</button>
			{/if}
		</div>
	</header>

	<nav>
		{#each SECTIONS as s (s.id)}
			<button class:on={section === s.id} onclick={() => setSection(s.id)}>
				{s.label}<span class="sub">{s.sub}</span>
			</button>
		{/each}
	</nav>

	<main>
		{#if down}
			<p class="declare warn">
				{down} &mdash; start it with <code>python -m malignment.serve</code>
			</p>
		{/if}
		{#if section === 'experiments'}
			<Experiments />
		{:else if section === 'roster'}
			<Roster />
		{:else if section === 'slot'}
			<SlotExplorer />
		{:else if section === 'plots'}
			<Plots />
		{:else if section === 'prompts'}
			<Prompts />
		{/if}
	</main>
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}
	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 11px 22px;
		border-bottom: 1px solid var(--rule);
		flex-shrink: 0;
	}
	.left {
		display: flex;
		align-items: baseline;
		gap: 12px;
	}
	h1 {
		margin: 0;
		font-size: 17px;
		font-weight: 600;
		letter-spacing: -0.4px;
	}
	.tag {
		font-size: 11.5px;
		color: var(--text-3);
	}
	.right {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.badge {
		font-size: 10.5px;
		padding: 2px 9px;
		border-radius: 10px;
		background: var(--panel-2);
		color: var(--text-3);
		border: 1px solid var(--rule);
	}
	.badge.ok {
		background: rgba(89, 161, 79, 0.13);
		color: var(--ok);
		border-color: rgba(89, 161, 79, 0.3);
	}
	.badge.bad {
		background: rgba(225, 87, 89, 0.13);
		color: var(--bad);
		border-color: rgba(225, 87, 89, 0.3);
	}
	.badge.blue {
		background: rgba(78, 121, 167, 0.14);
		color: var(--blue-light);
		border-color: rgba(78, 121, 167, 0.3);
	}

	nav {
		display: flex;
		gap: 2px;
		padding: 0 18px;
		border-bottom: 1px solid var(--rule);
		flex-shrink: 0;
	}
	nav button {
		background: none;
		border: 0;
		border-bottom: 2px solid transparent;
		padding: 9px 14px 8px;
		cursor: pointer;
		color: var(--text-3);
		font-size: 13px;
		text-align: left;
	}
	nav button:hover {
		color: var(--text);
	}
	nav button.on {
		color: #fff;
		border-bottom-color: var(--blue);
	}
	/*
	  THE SUBTITLE IS PART OF THE TAB, not a tooltip. Three sections can each
	  afford a line saying what question they answer, and a tab bar whose labels
	  need explaining is how "Census" and "Correlation" sat side by side for
	  weeks with nobody able to say what either did.
	*/
	nav .sub {
		display: block;
		font-size: 10px;
		color: var(--text-3);
		opacity: 0.75;
	}
	nav button.on .sub {
		color: var(--blue-light);
		opacity: 1;
	}

	main {
		flex: 1;
		/* RH, 2026-08-17: "I can't scroll down". `overflow: hidden` here clipped
		   every panel taller than the viewport — the slot word list, long result
		   tables, the markdown pages. The app shell stays 100vh and non-scrolling
		   so the header and nav are fixed; the CONTENT pane is what scrolls. */
		overflow-y: auto;
		padding: 18px 22px 0;
	}
	code {
		background: var(--panel);
		padding: 1px 5px;
		border-radius: 3px;
		font-size: 11px;
	}
</style>
