<!--
  Renders a repo markdown file: a question's README, a registration, the
  hypothesis register.

  THE FILE IS SHOWN, NOT SUMMARISED, and that is the component's whole reason.
  `experiments/README.md` holds THE hypothesis register, and the repo's rule is
  that a claim lives in one place -- *"a number in two files is a number that
  will disagree with itself"*. An app that parsed those READMEs into cards would
  be the second place, and it would be the one on screen.

  `marked` rather than a hand-rolled renderer: the tables here are load-bearing
  (every result table in every README is a pipe table), and a parser I wrote
  this afternoon would be a second markdown implementation whose failures show
  up as a silently missing row.

  NOT SANITISED, and that is a bounded claim rather than an oversight: the only
  strings reaching this component come from `serve.py` reading files inside this
  checkout. There is no user-authored input anywhere in the app. If a route ever
  serves markdown from outside the repo, this needs a sanitiser first.
-->
<script lang="ts">
	import { marked } from 'marked';

	let { src, compact = false }: { src: string | null; compact?: boolean } = $props();

	marked.setOptions({ gfm: true, breaks: false });

	let html = $derived(src ? (marked.parse(src) as string) : '');
</script>

{#if src}
	<div class="md" class:compact>{@html html}</div>
{:else}
	<p class="muted">no file</p>
{/if}

<style>
	.md {
		font-size: 13.5px;
		line-height: 1.6;
		color: var(--text);
		max-width: 78ch; /* prose measure; the tables below opt out */
	}
	.md.compact {
		font-size: 12.5px;
	}

	.md :global(h1) {
		font-size: 19px;
		margin: 0 0 14px;
		letter-spacing: -0.3px;
	}
	.md :global(h2) {
		font-size: 15px;
		margin: 26px 0 10px;
		padding-bottom: 5px;
		border-bottom: 1px solid var(--rule);
	}
	.md :global(h3) {
		font-size: 13px;
		margin: 20px 0 8px;
		color: var(--text-2);
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}
	.md :global(p) {
		margin: 0 0 11px;
	}
	.md :global(strong) {
		color: #fff;
		font-weight: 600;
	}
	.md :global(em) {
		color: var(--text-2);
	}
	.md :global(code) {
		background: var(--panel);
		border: 1px solid var(--rule-soft);
		border-radius: 3px;
		padding: 1px 4px;
		font-size: 11.5px;
	}
	.md :global(pre) {
		background: var(--panel);
		border: 1px solid var(--rule);
		border-radius: 4px;
		padding: 10px 12px;
		overflow-x: auto;
		font-size: 11.5px;
		line-height: 1.5;
	}
	.md :global(pre code) {
		background: none;
		border: 0;
		padding: 0;
	}
	.md :global(blockquote) {
		margin: 0 0 11px;
		padding: 2px 0 2px 12px;
		border-left: 2px solid var(--rule);
		color: var(--text-2);
	}
	.md :global(ul),
	.md :global(ol) {
		margin: 0 0 11px;
		padding-left: 20px;
	}
	.md :global(li) {
		margin-bottom: 4px;
	}

	/*
	  A README's table is a RESULT TABLE -- means, CIs, sign p. It gets the
	  monospace tabular treatment for the same reason every other number in this
	  app does, and it is allowed to exceed the prose measure, because wrapping a
	  results table to 78 characters is how a column stops being comparable.
	*/
	.md :global(table) {
		border-collapse: collapse;
		margin: 0 0 14px;
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
		font-size: 11.5px;
		display: block;
		overflow-x: auto;
		max-width: 100%;
	}
	.md :global(th),
	.md :global(td) {
		border: 1px solid var(--rule);
		padding: 4px 9px;
		text-align: left;
		white-space: nowrap;
	}
	.md :global(th) {
		background: var(--panel);
		color: var(--text-2);
		font-weight: 600;
	}
	.md :global(hr) {
		border: 0;
		border-top: 1px solid var(--rule);
		margin: 22px 0;
	}
	.md :global(a) {
		color: var(--blue-light);
	}
</style>
