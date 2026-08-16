<!--
  A result grain, with the size of what is NOT on screen stated above it.

  THE DECLARATION IS NOT OPTIONAL AND CANNOT BE SWITCHED OFF. `ResultRows` makes
  `n_rows_total` and `n_rows_returned` required fields, so there is no way to
  mount this component without having been handed the number that says whether
  the table is complete. That is deliberate: the defect it guards against is a
  windowed view read as a population, which produces no error, survives every
  check, and is caught by nothing except saying so on the panel.

  VALUES ARE PRINTED AS THE FILE STORES THEM. No rounding, no thousands
  separators, no NaN for a blank. `serve.py` reads the CSV with `csv.reader` and
  hands back strings for the same reason. A viewer that renders 0.00366555845 as
  0.0037 is showing something the result file does not say, and the reader has no
  way to tell which of the two they are looking at.

  ALIGNMENT IS INFERRED FROM THE DATA, NOT DECLARED. A column whose non-empty
  cells all parse as numbers is right-aligned; everything else is left. Model ids
  and prompt keys are strings and stay left, so the eye can run down a name; the
  measurements right-align and their decimal points line up, which is the only
  reason a column of floats is comparable at a glance.
-->
<script lang="ts">
	import type { ResultRows } from '$lib/api';

	let { data }: { data: ResultRows } = $props();

	//: A column is numeric only if EVERY non-blank cell parses. One stray label in
	//: a float column means the column is not a quantity, and right-aligning it
	//: would imply a comparison that is not available.
	let numeric = $derived(
		data.columns.map((_, i) => {
			let seen = 0;
			for (const r of data.rows) {
				const v = r[i];
				if (v === undefined || v === '') continue;
				seen++;
				if (!Number.isFinite(Number(v))) return false;
			}
			return seen > 0;
		})
	);

	const fmt = (n: number) => n.toLocaleString('en-US');
</script>

<p class="declare" class:warn={data.capped}>
	{#if data.capped}
		showing {fmt(data.n_rows_returned)} of {fmt(data.n_rows_total)} rows &mdash; this table is a
		WINDOW, and any pattern read off it is a pattern in the first {fmt(data.n_rows_returned)}
		rows of the file, not in {data.grain}
	{:else}
		{fmt(data.n_rows_total)}
		{data.n_rows_total === 1 ? 'row' : 'rows'} &mdash; the whole of {data.grain}
	{/if}
</p>

<div class="wrap">
	<table>
		<thead>
			<tr>
				{#each data.columns as c, i (c)}
					<th class:num={numeric[i]}>{c}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each data.rows as row, ri (ri)}
				<tr>
					{#each data.columns as _c, i (i)}
						<td class:num={numeric[i]} class:blank={!row[i]}>{row[i] ?? ''}</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.wrap {
		overflow: auto;
		max-height: 62vh;
		border: 1px solid var(--rule);
		border-radius: 4px;
		background: var(--panel);
	}
	table {
		border-collapse: collapse;
		width: 100%;
		font-size: 11.5px;
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
		color: var(--text-2);
		font-weight: 600;
		font-size: 10.5px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		z-index: 1;
		border-bottom: 1px solid var(--rule);
	}
	td.num,
	th.num {
		text-align: right;
		font-family: var(--mono);
		font-variant-numeric: tabular-nums;
	}
	tbody tr:hover {
		background: rgba(255, 255, 255, 0.035);
	}
	/*
	  AN EMPTY CELL IS SHOWN AS EMPTY. The archive's tables printed a dash, which
	  is a character the file does not contain -- and a dash is exactly what
	  several of these columns legitimately hold.
	*/
	td.blank {
		background: rgba(255, 255, 255, 0.02);
	}
</style>
