<!--
  National stories: table of generated stories with click-through detail view
  showing color-coded annotation spans.
-->
<script lang="ts">
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import StoryRates from './StoryRates.svelte';
	import StoryPanel from './StoryPanel.svelte';
	import StoryLadder from './StoryLadder.svelte';

	let storyTab = $state<'rates' | 'ladder' | 'panel' | 'table'>('rates');
	let rows = $state<any[]>([]);
	let loading = $state(true);
	let error = $state('');
	let selected = $state<string | null>(null);
	let detail = $state<any>(null);
	let detailLoading = $state(false);

	let armFilter = $state('');
	let frameFilter = $state('');
	let sortKey = $state('n_words');
	let sortDesc = $state(true);

	const BASE = '/api';

	async function load() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (armFilter) params.set('arm', armFilter);
			if (frameFilter) params.set('frame', frameFilter);
			const r = await fetch(`${BASE}/stories?${params}`);
			const d = await r.json();
			rows = d.rows;
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}
	load();

	$effect(() => { armFilter; frameFilter; load(); });

	function sortBy(k: string) {
		if (sortKey === k) sortDesc = !sortDesc;
		else { sortKey = k; sortDesc = true; }
	}

	let sorted = $derived.by(() => {
		const s = [...rows].sort((a, b) => {
			const av = a[sortKey], bv = b[sortKey];
			if (av == null && bv == null) return 0;
			if (av == null) return 1;
			if (bv == null) return -1;
			const c = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
			return sortDesc ? -c : c;
		});
		return s;
	});

	async function openStory(id: string) {
		selected = id;
		detailLoading = true;
		replaceState('/stories/' + id, {});
		try {
			const r = await fetch(`${BASE}/story?id=${id}`);
			detail = await r.json();
		} catch (e: any) {
			error = e.message;
		} finally {
			detailLoading = false;
		}
	}

	function back() {
		selected = null;
		detail = null;
		replaceState('/stories', {});
	}

	{
		const segs = page.url.pathname.split('/').filter(Boolean);
		if (segs[0] === 'stories' && segs[1]) {
			openStory(segs[1]);
		}
	}

	const SPAN_COLORS: Record<string, string> = {
		opponent: '#e15759',
		opponent_fate: '#f28e2b',
		conflict_mode: '#4e79a7',
		ending: '#76b7b2',
		resolution_scale: '#b07aa1',
		resolution_means: '#59a14f',
		community_role: '#edc949',
		mood: '#af7aa1',
		genre: '#ff9da7',
		setting: '#9c755f',
		homecoming: '#bab0ab',
		threat: '#e15759',
		romance: '#ff9da7',
		protagonist_change: '#4e79a7',
		temporality: '#76b7b2',
	};

	function spanColor(annotation: string): string {
		return SPAN_COLORS[annotation] ?? '#888888';
	}

	let TABLE_COLS = ['model', 'arm', 'frame', 'demonym', 'n_words', 'opponent', 'opponent_fate', 'mood', 'genre', 'setting', 'conflict_mode', 'ending'];
</script>

<style>
	.filters { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; font-size: 12px; }
	.filters select { background: var(--panel); border: 1px solid var(--rule); color: var(--text); padding: 3px 8px; border-radius: 4px; font-size: 11px; }
	.tablewrap { overflow-x: auto; }
	table { border-collapse: collapse; font-size: 11px; width: 100%; }
	th { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--rule); cursor: pointer; white-space: nowrap; }
	th:hover { color: #fff; }
	th.on { color: var(--blue-light); }
	td { padding: 3px 8px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
	td.num { text-align: right; font-variant-numeric: tabular-nums; }
	tr { cursor: pointer; }
	tr:hover { background: rgba(78, 121, 167, 0.08); }
	.dir { font-size: 9px; margin-left: 2px; }
	.back { margin-bottom: 12px; }
	.story-text { font-size: 13px; line-height: 1.7; max-width: 700px; margin: 12px 0; }
	.story-text :global(.para) { margin-bottom: 0.8em; }
	.meta { font-size: 11px; color: var(--text-3); margin: 4px 0; }
	.span-hl { border-bottom: 2px solid; padding-bottom: 1px; cursor: help; }
	.legend { display: flex; flex-wrap: wrap; gap: 8px; font-size: 10px; margin: 8px 0; }
	.legend span { padding: 1px 6px; border-radius: 3px; border: 1px solid; }
	.ann-table { font-size: 11px; margin: 8px 0; }
	.ann-table td { padding: 2px 8px; }
	.ann-table .label { color: var(--text-3); text-align: right; }
</style>

{#if selected && detail}
	<button class="ghost back" onclick={back}>← all stories</button>

	<p class="meta">
		<b>{detail.story.model}</b> · {detail.story.arm} · {detail.story.frame} · {detail.story.demonym} · {detail.story.n_words} words
	</p>

	<table class="ann-table">
		{#each ['opponent', 'opponent_fate', 'conflict_mode', 'mood', 'genre', 'setting', 'ending', 'resolution_scale', 'resolution_means', 'protagonist_change', 'homecoming', 'threat', 'temporality', 'romance', 'community_role'] as col}
			{#if detail.story[col]}
				<tr>
					<td class="label">{col.replace(/_/g, ' ')}</td>
					<td><span style="color:{spanColor(col)}">{detail.story[col]}</span></td>
				</tr>
			{/if}
		{/each}
		{#if detail.story.stakes}
			<tr><td class="label">stakes</td><td>{detail.story.stakes}</td></tr>
		{/if}
	</table>

	<div class="legend">
		{#each Object.entries(SPAN_COLORS) as [ann, col]}
			{#if detail.spans.some((s) => s.annotation === ann)}
				<span style="border-color:{col};color:{col}">{ann.replace(/_/g, ' ')}</span>
			{/if}
		{/each}
	</div>

	{@const paragraphs = (() => {
		const text = detail.story.text;
		const spans = detail.spans.filter((s: any) => s.located);
		const cuts = new Set([0, text.length]);
		for (const s of spans) { cuts.add(s.start); cuts.add(s.end); }
		const sorted = [...cuts].sort((a, b) => a - b);
		const segs = [];
		for (let i = 0; i < sorted.length - 1; i++) {
			const start = sorted[i], end = sorted[i + 1];
			const active = spans
				.filter((s: any) => s.start <= start && s.end >= end)
				.map((s: any) => ({ ann: s.annotation, val: s.value }));
			segs.push({ text: text.slice(start, end), anns: active });
		}
		const paras: typeof segs[] = [[]];
		for (const seg of segs) {
			const parts = seg.text.split(/\n\n+/);
			for (let i = 0; i < parts.length; i++) {
				if (i > 0) paras.push([]);
				const t = parts[i].replace(/\n/g, ' ');
				if (t) paras[paras.length - 1].push({ text: t, anns: seg.anns });
			}
		}
		return paras.filter((p) => p.some((s) => s.text.trim()));
	})()}
	<div class="story-text">
		{#each paragraphs as para, pi}
			<p class="para">
				{#each para as seg}
					{#if seg.anns.length}
						<span class="span-hl"
							style="border-color:{spanColor(seg.anns[0].ann)};{seg.anns.length > 1 ? `text-decoration:underline;text-decoration-color:${spanColor(seg.anns[1].ann)}` : ''}"
							title={seg.anns.map((a) => a.ann.replace(/_/g, ' ') + ': ' + a.val).join('\n')}>{seg.text}</span>
					{:else}{seg.text}{/if}
				{/each}
			</p>
		{/each}
	</div>

{:else if selected && detailLoading}
	<p class="muted">loading story...</p>
{:else}
	<div class="chart-tabs" style="margin-bottom:12px">
		<button class:active={storyTab === 'rates'} onclick={() => storyTab = 'rates'}>annotation rates</button>
		<button class:active={storyTab === 'ladder'} onclick={() => storyTab = 'ladder'}>training ladder</button>
		<button class:active={storyTab === 'panel'} onclick={() => storyTab = 'panel'}>semantic fields</button>
		<button class:active={storyTab === 'table'} onclick={() => storyTab = 'table'}>stories table</button>
	</div>

	{#if storyTab === 'rates'}
		<StoryRates />
	{:else if storyTab === 'ladder'}
		<StoryLadder />
	{:else if storyTab === 'panel'}
		<StoryPanel />
	{:else}
	<div class="filters">
		<label>arm <select bind:value={armFilter}>
			<option value="">all</option><option value="base">base</option><option value="aligned">aligned</option>
		</select></label>
		<label>frame <select bind:value={frameFilter}>
			<option value="">all</option><option value="raw">raw</option><option value="prefill">prefill</option>
		</select></label>
		<span class="muted">{rows.length} stories</span>
	</div>

	{#if loading}
		<p class="muted">loading...</p>
	{:else if error}
		<p class="err">{error}</p>
	{:else}
		<div class="tablewrap">
			<table>
				<thead>
					<tr>
						{#each TABLE_COLS as col}
							<th class:on={sortKey === col} onclick={() => sortBy(col)}>
								{col.replace(/_/g, ' ')}{#if sortKey === col}<span class="dir">{sortDesc ? '▾' : '▴'}</span>{/if}
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each sorted.slice(0, 500) as r (r.id)}
						<tr onclick={() => openStory(r.id)}>
							{#each TABLE_COLS as col}
								<td class:num={typeof r[col] === 'number'}>{r[col] ?? ''}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
	{/if}
{/if}
