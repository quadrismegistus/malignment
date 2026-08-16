<!--
  Which models am I comparing?

  THE ONE DESIGN DECISION HERE: `endpoints`, `chains` and `paths` ARE SHOWN IN
  ONE TABLE, ONE ROW PER LINEAGE, rather than as three lists behind three tabs.

  Three tabs would render them as three views of one thing. `docs/HOWTO.md` says
  at length that they are not:

      Llama-3.1-8B     path  -> Llama-3.1-8B-Instruct          (Meta's, 1 step)
                       chain -> Tulu-3-8B-SFT -> Tulu-3-8B-DPO (AllenAI's)

  *"Both are correct and they are not the same measurement."* 17 lineages have a
  multi-step path and 16 have a chain, **and they are not the same lineages** --
  `stablelm-2-1_6b` and `RedPajama` have 2-step paths that `chains()` excludes
  because their last op is `instruct` rather than a named preference op.

  A reader flipping between two tabs cannot see that. Beside each other on one
  row, a lineage that has a path and no chain is a blank cell you cannot miss,
  and the count of blank cells IS the divergence the HOWTO spends a paragraph
  on. This is the same argument as the campaign's rule that decompositions print
  beside aggregates: the constituents have to share the panel or the comparison
  is left to memory.

  THE ENDPOINT AND THE CHAIN ARE COLOURED DIFFERENTLY ON PURPOSE. They are
  answers to different questions -- an endpoint asks *what does a user receive*,
  a chain rung asks *which stage did it* -- and a shared colour would say they
  are the same kind of object.
-->
<script lang="ts">
	import { api } from '$lib/api';
	import type { RosterSummary } from '$lib/api';

	let r: RosterSummary | null = $state(null);
	let error = $state('');
	let filter = $state('');
	let only = $state<'all' | 'chain' | 'multistep' | 'divergent'>('all');

	(async () => {
		try {
			r = await api.roster();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	})();

	const short = (m: string) => m.split('/').pop() ?? m;

	//: ONE ROW PER LINEAGE, joining the three populations on the BASE. The join
	//: key is the base because that is the only thing all three share -- an
	//: endpoint row and a chain row for one lineage can name entirely different
	//: aligned checkpoints, which is the point of showing them together.
	let lineages = $derived.by(() => {
		if (!r) return [];
		const byBase = new Map<string, { base: string; endpoint?: string; steps?: number; ops?: string[]; sft?: string; pref?: string; pref_op?: string }>();
		for (const e of r.endpoints) byBase.set(e.base, { base: e.base, endpoint: e.endpoint });
		for (const p of r.paths) {
			const row = byBase.get(p.base) ?? { base: p.base };
			row.steps = p.n_steps;
			row.ops = p.ops;
			byBase.set(p.base, row);
		}
		for (const c of r.chains) {
			const row = byBase.get(c.base) ?? { base: c.base };
			//: A BASE CAN CARRY TWO CHAINS -- 18 chains over 16 lineages. Keeping the
			//: first silently would under-report; the count is shown instead.
			row.sft = row.sft ? row.sft : c.sft;
			row.pref = row.pref ? row.pref : c.pref;
			row.pref_op = row.pref_op ? row.pref_op : c.pref_op;
			byBase.set(c.base, row);
		}
		return [...byBase.values()].sort((a, b) => a.base.localeCompare(b.base));
	});

	let shown = $derived.by(() => {
		const f = filter.trim().toLowerCase();
		return lineages.filter((l) => {
			if (f && !JSON.stringify(l).toLowerCase().includes(f)) return false;
			if (only === 'chain') return !!l.pref;
			if (only === 'multistep') return (l.steps ?? 1) > 1;
			//: THE DIVERGENT SET: a lineage where the path and the chain disagree
			//: about what "aligned" means -- because only one of them exists, or
			//: because both exist and name different checkpoints. This is the filter
			//: that answers "can I put these two experiments on a common basis".
			//: Same three predicates as the decomposition above, so the button and
			//: the counts cannot drift apart.
			if (only === 'divergent')
				return (
					((l.steps ?? 1) > 1 && !l.pref) ||
					(!!l.pref && (l.steps ?? 1) === 1) ||
					(!!l.pref && !!l.endpoint && l.endpoint !== l.pref)
				);
			return true;
		});
	});

	let nChain = $derived(lineages.filter((l) => l.pref).length);
	let nMulti = $derived(lineages.filter((l) => (l.steps ?? 1) > 1).length);

	//: ── THE DECOMPOSITION, NOT THE AGGREGATE.
	//:
	//: "17 have a multi-step path and 16 have a chain" is an aggregate, and on its
	//: own it invites the reading that 16 of the 17 are the same lineages and one
	//: is extra. They are three separate disagreements, and only the third is
	//: about lineages that HAVE both:
	//:
	//:     pathOnly   a multi-step path and no chain -- the last op is `instruct`
	//:                rather than a named preference op, so chains() excludes it
	//:     chainOnly  a chain whose path is ONE step -- the publisher shipped an
	//:                endpoint directly and a third party shipped the middle
	//:     disagree   both exist and name DIFFERENT aligned checkpoints
	//:
	//: Verified against the store 2026-08-16: pathOnly is MiniCPM5-1B-Base,
	//: RedPajama-INCITE-Base-7B-v0.1, stablelm-2-1_6b; chainOnly is Llama-3.1-8B
	//: and Mistral-7B-v0.1 -- which are precisely the two worked examples in
	//: `docs/HOWTO.md`, recovered here from the data rather than copied from it.
	//:
	//: This is the campaign's standing rule that decompositions print beside
	//: aggregates, and it is load-bearing rather than decorative: a reader
	//: choosing between two experiments needs to know WHICH KIND of disagreement
	//: they face, because they have different consequences.
	let pathOnly = $derived(lineages.filter((l) => (l.steps ?? 1) > 1 && !l.pref));
	let chainOnly = $derived(lineages.filter((l) => !!l.pref && (l.steps ?? 1) === 1));
	let disagree = $derived(
		lineages.filter((l) => !!l.pref && !!l.endpoint && l.endpoint !== l.pref)
	);
	let nDivergent = $derived(pathOnly.length + chainOnly.length + disagree.length);
</script>

{#if error}
	<p class="err">{error}</p>
{:else if !r}
	<p class="muted">reading the roster…</p>
{:else}
	<div class="pops">
		{#each Object.entries(r.populations) as [kind, n] (kind)}
			<div class="pop">
				<span class="n num">{typeof n === 'number' ? n : '!'}</span>
				<span class="k">{kind}</span>
			</div>
		{/each}
	</div>

	<!--
	  `unresolved` IS RENDERED WHETHER OR NOT IT IS EMPTY. `docs/HOWTO.md`: *"a
	  caller that ignores it is choosing by accident."* A panel that showed this
	  block only when non-empty would train its reader to stop looking for it,
	  and the day it matters is the day it appears for the first time.
	-->
	{#if Object.keys(r.unresolved).length}
		<p class="declare warn">
			{Object.keys(r.unresolved).length} lineage(s) UNRESOLVED &mdash; endpoints() refused to choose:
			{Object.keys(r.unresolved).join(', ')}
		</p>
	{:else}
		<p class="declare">unresolved: 0 &mdash; every lineage resolved to one endpoint by a stated rule</p>
	{/if}

	<div class="split">
		<div>
			<h3>path length</h3>
			<div class="steps">
				{#each Object.entries(r.path_steps) as [k, n] (k)}
					<div class="step">
						<span class="num big">{n}</span>
						<span class="lbl">{k} step{k === '1' ? '' : 's'}</span>
					</div>
				{/each}
			</div>
			<p class="note">
				A 1-step path means <strong>one released rung</strong>, never one training stage.
				Baichuan2-7B-Chat is 1 step here and its own paper describes SFT then RLHF &mdash; the
				SFT rung was never released.
			</p>
		</div>
		<div>
			<h3>the two populations do not coincide</h3>
			<p class="note">
				<span class="num">{nMulti}</span> lineages have a multi-step path and
				<span class="num">{nChain}</span> have a chain, and they are
				<strong>not the same lineages</strong>. That aggregate hides three different
				disagreements, and only the last is about lineages that have both:
			</p>
			<ul class="decomp">
				<li>
					<span class="num c">{pathOnly.length}</span> multi-step path, <em>no chain</em> &mdash;
					the last op is <code>instruct</code>, not a named preference op
					{#if pathOnly.length}<span class="who">{pathOnly.map((l) => short(l.base)).join(', ')}</span>{/if}
				</li>
				<li>
					<span class="num c">{chainOnly.length}</span> chain, <em>1-step path</em> &mdash; the
					publisher shipped an endpoint and a third party shipped the middle
					{#if chainOnly.length}<span class="who">{chainOnly.map((l) => short(l.base)).join(', ')}</span>{/if}
				</li>
				<li>
					<span class="num c">{disagree.length}</span> both exist and
					<em>name different aligned checkpoints</em>
				</li>
			</ul>
			<p class="note">
				So <code>chains()</code> measures Llama through <strong>Tulu</strong> and Mistral
				through <strong>zephyr</strong>, where <code>endpoints()</code> measures both through
				the publisher's own instruct. Both are correct and they are not the same measurement.
			</p>
		</div>
	</div>

	<div class="controls">
		<input placeholder="filter lineages…" bind:value={filter} />
		<button class="ghost" class:on={only === 'all'} onclick={() => (only = 'all')}>all {lineages.length}</button>
		<button class="ghost" class:on={only === 'chain'} onclick={() => (only = 'chain')}>has a chain {nChain}</button>
		<button class="ghost" class:on={only === 'multistep'} onclick={() => (only = 'multistep')}>multi-step path {nMulti}</button>
		<button class="ghost" class:on={only === 'divergent'} onclick={() => (only = 'divergent')}>path ≠ chain {nDivergent}</button>
	</div>

	<p class="declare">
		showing {shown.length} of {lineages.length} lineages
		{#if only !== 'all' || filter}&mdash; filtered{/if}
	</p>

	<div class="wrap">
		<table>
			<thead>
				<tr>
					<th>base</th>
					<th class="ep">endpoint</th>
					<th class="num">steps</th>
					<th>ops</th>
					<th class="ch">sft rung</th>
					<th class="ch">preference rung</th>
					<th class="ch">op</th>
				</tr>
			</thead>
			<tbody>
				{#each shown as l (l.base)}
					<tr>
						<td title={l.base}>{short(l.base)}</td>
						<td class="ep" title={l.endpoint}>{l.endpoint ? short(l.endpoint) : ''}</td>
						<td class="num">{l.steps ?? ''}</td>
						<td class="ops">{l.ops?.join(' → ') ?? ''}</td>
						<td class="ch" title={l.sft}>{l.sft ? short(l.sft) : ''}</td>
						<td class="ch" title={l.pref}>{l.pref ? short(l.pref) : ''}</td>
						<td class="ch">{l.pref_op ?? ''}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}

<style>
	.pops {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		background: var(--rule);
		border: 1px solid var(--rule);
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 14px;
	}
	.pop {
		background: var(--panel);
		padding: 8px 16px;
		flex: 1 1 auto;
		min-width: 108px;
	}
	.pop .n {
		display: block;
		font-size: 20px;
		font-weight: 600;
		color: var(--text);
	}
	.pop .k {
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--text-3);
	}

	.split {
		display: grid;
		grid-template-columns: 1fr 1.6fr;
		gap: 24px;
		margin-bottom: 18px;
	}
	h3 {
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		color: var(--text-3);
		margin: 0 0 8px;
	}
	.steps {
		display: flex;
		gap: 18px;
		margin-bottom: 8px;
	}
	.step .big {
		font-size: 22px;
		font-weight: 600;
	}
	.step .lbl {
		display: block;
		font-size: 10px;
		color: var(--text-3);
	}
	.note {
		font-size: 12px;
		line-height: 1.55;
		color: var(--text-2);
		margin: 0;
		max-width: 66ch;
	}
	.note code {
		font-size: 11px;
		background: var(--panel);
		padding: 1px 4px;
		border-radius: 3px;
	}
	.note strong {
		color: var(--text);
	}
	.decomp {
		list-style: none;
		margin: 8px 0;
		padding: 0;
		font-size: 12px;
		color: var(--text-2);
		max-width: 66ch;
	}
	.decomp li {
		padding: 3px 0 3px 10px;
		border-left: 2px solid var(--rule);
		margin-bottom: 4px;
		line-height: 1.45;
	}
	.decomp .c {
		display: inline-block;
		min-width: 1.4em;
		font-weight: 600;
		color: var(--red-light);
	}
	.decomp em {
		color: var(--text);
		font-style: normal;
		font-weight: 600;
	}
	.decomp code {
		font-size: 11px;
		background: var(--panel);
		padding: 1px 4px;
		border-radius: 3px;
	}
	/* The members, named. A count with no membership cannot be audited. */
	.decomp .who {
		display: block;
		font-family: var(--mono);
		font-size: 10px;
		color: var(--text-3);
		margin-top: 2px;
	}

	.controls {
		display: flex;
		gap: 6px;
		align-items: center;
		margin-bottom: 10px;
		flex-wrap: wrap;
	}
	.controls input {
		width: 220px;
	}

	.wrap {
		overflow: auto;
		max-height: 52vh;
		border: 1px solid var(--rule);
		border-radius: 4px;
		background: var(--panel);
	}
	table {
		border-collapse: collapse;
		width: 100%;
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
		font-size: 11px;
	}
	th,
	td {
		padding: 3px 10px;
		border-bottom: 1px solid var(--rule-soft);
		text-align: left;
		white-space: nowrap;
	}
	th {
		position: sticky;
		top: 0;
		background: var(--panel-2);
		color: var(--text-3);
		font-weight: 600;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid var(--rule);
	}
	td.num,
	th.num {
		text-align: right;
	}
	/* endpoint blue, chain red: different questions, different colours. */
	.ep {
		color: var(--blue-light);
	}
	.ch {
		color: var(--red-light);
	}
	th.ep {
		color: var(--blue);
	}
	th.ch {
		color: var(--red);
	}
	.ops {
		color: var(--text-3);
	}
	tbody tr:hover {
		background: rgba(255, 255, 255, 0.035);
	}
</style>
