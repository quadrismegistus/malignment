//: The whole client surface. One function per SERVER ROUTE, no query building.
//:
//: `malignment/serve.py` refuses to accept SQL from a client, so there is
//: nothing here that assembles one. If a view needs data this file cannot ask
//: for, the answer is a route in `serve.py` reading a producer's output -- never
//: a more expressive endpoint. The archive's app grew a `/api/data/csv` that
//: took a path, and what it actually grew was a second way to define a
//: population.

const BASE = import.meta.env.DEV ? '/api' : '';

async function get<T>(path: string): Promise<T> {
	const res = await fetch(`${BASE}${path}`);
	const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
	//: THE SERVER'S REASON, NOT A STATUS CODE. Every refusal in `serve.py` names
	//: what it refused and lists what it would have accepted; throwing away that
	//: sentence in favour of "404" is how a typo in a grain name becomes twenty
	//: minutes of looking at the wrong thing.
	if (!res.ok) throw new Error((body as { error?: string }).error || `HTTP ${res.status}`);
	return body as T;
}

export interface SourceStatus {
	//: True when a `.py` in the package differs from what this PROCESS loaded.
	//: The server cannot reload itself — `_SLOT_MODELS` lives in `serve`'s
	//: globals, so reloading it drops the resident weights — so the most it can
	//: do is refuse to look current when it is not.
	stale: boolean;
	changed: string[];
	n_files: number;
	pid: number;
	booted_at: string | null;
}

export interface Health {
	status: string;
	db: string;
	//: Present since 2026-08-17. Optional so an older server does not render as
	//: broken — absent means "this server cannot tell you", which is not the
	//: same claim as "not stale".
	source?: SourceStatus;
	slot_enabled: boolean;
	//: In LRU order, least-recently-used first — so the head is what the next
	//: load will evict. Not sorted; the order is information.
	slot_loaded: string[];
	slot_max: number;
	slot_ttl: number;
	//: The declared diagnostic pair, verified out-of-population at server boot.
	//: Empty if that check failed — so an unverified pair is never offered.
	diagnostic_pair: string[];
	//: {model_id: seconds since last use}. Lets a caller distinguish a model that
	//: is resident from one about to be released by the idle reaper.
	slot_idle: Record<string, number>;
}

export interface PlotParam {
	name: string;
	type: 'text' | 'int' | 'choice' | 'prompt';
	label?: string;
	help?: string;
	required?: boolean;
	default?: string | number;
	choices?: string[];
	min?: number;
	max?: number;
}

export interface PlotSpec {
	id: string;
	name: string;
	blurb?: string;
	experiment?: string;
	has_render?: boolean;
	//: Set when the producer would not import. Shown rather than skipped: a plot
	//: missing from the list is indistinguishable from one never written.
	error?: string | null;
	params: PlotParam[];
}

export interface Table {
	name: string;
	engine: string;
	rows: number | null;
	bytes: number | null;
	size: string;
	sorting_key: string;
}

export interface RosterSummary {
	populations: Record<string, number | { error: string }>;
	endpoints: { base: string; endpoint: string }[];
	unresolved: Record<string, string[]>;
	chains: { base: string; sft: string; pref: string; pref_op: string }[];
	paths: { base: string; endpoint: string; nodes: string[]; ops: string[]; n_steps: number }[];
	path_steps: Record<string, number>;
}

export interface ResultFile {
	grain: string;
	bytes: number;
	kind: string;
}

export interface Question {
	id: string;
	name: string;
	subject: string | null;
	has: Record<string, boolean>;
	results: ResultFile[];
	figures: string[];
}

export interface Experiments {
	register_md: string | null;
	questions: Question[];
}

export interface QuestionDetail extends Question {
	readme_md: string | null;
	registration_md: string | null;
	population: Record<string, unknown> | null;
}

//: `n_rows_total` AND `n_rows_returned` ARE BOTH REQUIRED, not optional, so a
//: component cannot render a table without having been handed the number that
//: says whether it is the whole table. A caption is a claim about what was
//: DRAWN; the type makes the other number impossible to forget.
export interface ResultRows {
	id: string;
	grain: string;
	columns: string[];
	rows: string[][];
	n_rows_total: number;
	n_rows_returned: number;
	capped: boolean;
	cap: number;
}

export interface ResultJson {
	id: string;
	grain: string;
	json: unknown;
}

export interface Pair {
	base: string;
	endpoint: string;
	n_steps: number | null;
	ops: string[];
	label: string;
}

export interface SlotWord {
	word: string;
	p: number;
}

export interface SlotResponse {
	prompt: string;
	models: string[];
	n_models: number;
	//: Models that actually produced a cell. Differs from `n_models` when a
	//: checkpoint's tokenizer refused the prompt, and it is the denominator the
	//: pool was divided by — so a panel reporting one while the arithmetic used
	//: the other is the pooling bug restated.
	n_answered: number;
	n_words: number;
	shown: number;
	words: SlotWord[];
	residual: Record<string, number | null> | null;
	//: sum(words) + residual.total. The instrument's own accounting identity,
	//: returned so the panel can show that the books close rather than assert it.
	conservation: number | null;
	//: The declared pair and the PATH between its ends. `n_steps` matters:
	//: 17 of the 50 are multi-step, and the default is three ops — so "aligned"
	//: means the far end of a path, not one operation.
	pair: { base: string; endpoint: string; n_steps: number | null; ops: string[] };
	rule_version: number;
	dict_sha: string;
	theta: number;
	skipped: string | null;
}

export interface AxisResponse {
	ok: boolean;
	norm: number;
	note?: string;
	scores: { word: string; s: number }[];
	pole_gap?: number;
	purity?: number;
	defectors?: string[];
	n_poles?: [number, number];
	//: Present only when a distribution was sent.
	N?: number;
	leverage?: number;
	flags?: string[];
	//: **null BY DESIGN.** The archive's thresholds were calibrated on a
	//: population that has since moved; they are reported for orientation and
	//: draw no verdict. See `malignment/slot_axis.py`.
	leverage_verdict?: null;
	lev_mover?: number;
	lev_dead?: number;
	lev_source?: string;
}

//: An error that survives the throw with its status attached. `/slot/save`
//: answers 409 to REFUSE A CLOBBER, which is a question for the author rather
//: than a failure — and a plain `Error(message)` flattens it into the same red
//: text as a 400, leaving the caller to pattern-match on prose.
export class ApiError extends Error {
	status: number;
	conflict: boolean;
	constructor(message: string, status: number, conflict = false) {
		super(message);
		this.status = status;
		this.conflict = conflict;
	}
}

async function post<T>(path: string, body: unknown): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	const j = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
	if (!res.ok) {
		const e = j as { error?: string; conflict?: boolean };
		throw new ApiError(e.error || `HTTP ${res.status}`, res.status, !!e.conflict);
	}
	return j as T;
}

export interface SavedItem {
	item_id: string;
	prompt: string;
	domain: string;
	naughty: string[];
	nice: string[];
	naughty_mass: number;
	nice_mass: number;
	share: number | null;
	writer: string;
	note: string;
	saved_at?: string;
	action?: string;
}

export interface SaveResponse {
	item_id: string;
	//: `created` | `updated` | `unchanged`. Shown VERBATIM, because saving over an
	//: unchanged item and replacing a different tagging are different events and
	//: the author is the only one who can say whether the second was intended.
	//: (`overwritten` was the value when each item was its own JSON file; the
	//: running yaml replaces an entry in place, so it is `updated`.)
	action: string;
	path: string;
	item: SavedItem;
}

export interface SaveRequest {
	prompt: string;
	naughty: string[];
	nice: string[];
	//: `{word: p}` from the run on screen. The masses, their ordering and
	//: `item_id` are all derived from this SERVER-SIDE — a client-supplied mass
	//: that disagreed with the tags beside it would be undetectable.
	words: Record<string, number>;
	provenance?: Record<string, unknown>;
	domain?: string;
	note?: string;
	overwrite?: boolean;
}

export const api = {
	//: POST for PAYLOAD SIZE, not side effects — it writes nothing. At k=500 the
	//: candidate list is kilobytes, past what a URL carries reliably.
	slotAxis: (
		prompt: string,
		naughty: string[],
		nice: string[],
		words: string[],
		probs?: Record<string, number>
	) => post<AxisResponse>('/slot/axis', { prompt, naughty, nice, words, probs }),
	//: **THE ONLY CALL IN THIS CLIENT WITH SIDE EFFECTS.** Writes an authored
	//: item to `$MALIGNMENT_DATA/slots/`, outside the repo, because a saved item
	//: carries its prompt verbatim from the transgressive battery.
	slotSave: (body: SaveRequest) => post<SaveResponse>('/slot/save', body),
	slotSaved: () => get<{ dir: string; n: number; items: SavedItem[] }>('/slot/saved'),
	health: () => get<Health>('/health'),
	inventory: () => get<{ db: string; tables: Table[] }>('/store/inventory'),
	roster: () => get<RosterSummary>('/roster'),
	population: (kind: string) =>
		get<{ kind: string; n: number; members: string[] }>(
			`/roster/population?kind=${encodeURIComponent(kind)}`
		),
	experiments: () => get<Experiments>('/experiments'),
	//: The producers' own declarations. Nothing in the client knows what a plot
	//: type is; adding one is adding a PLOT dict to a producer.
	plots: () => get<{ plots: PlotSpec[] }>('/plots'),
	//: Filtered SERVER-SIDE over a cached set, in Python, never with a LIKE —
	//: see `serve._plot_prompt_set`. The prompt is validated by membership at
	//: render time because it reaches a ClickHouse query.
	plotPrompts: (q: string, limit = 40) =>
		get<{ n_total: number; n_matched: number; limit: number; prompts: string[] }>(
			`/plot/prompts?q=${encodeURIComponent(q)}&limit=${limit}`
		),
	plotRender: (plot: string, params: Record<string, string>) => {
		const qs = Object.entries(params)
			.filter(([, v]) => v !== '' && v != null)
			.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
			.join('&');
		return get<{
			plot: string;
			experiment: string;
			params: Record<string, unknown>;
			seconds: number;
			figure: string;
			url: string;
			info: Record<string, unknown>;
		}>(`/plot/render?plot=${encodeURIComponent(plot)}&${qs}`);
	},
	//: A URL, not a fetch. The <img> does the request, so the browser caches and
	//: decodes it — pulling a 300 dpi PNG through `fetch` into a blob would buy
	//: nothing and lose the cache.
	figureUrl: (id: string, name: string) =>
		`${BASE}/experiment/figure?id=${encodeURIComponent(id)}&name=${encodeURIComponent(name)}`,
	experiment: (id: string) => get<QuestionDetail>(`/experiment?id=${encodeURIComponent(id)}`),
	result: (id: string, grain: string, limit?: number) =>
		get<ResultRows | ResultJson>(
			`/experiment/result?id=${encodeURIComponent(id)}&grain=${encodeURIComponent(grain)}` +
				(limit ? `&limit=${limit}` : '')
		),
	//: DERIVED SERVER-SIDE, AND A FUNCTION OF THE PROMPT ALONE since 2026-08-17.
	//: The pole words used to be in it and made it unstable — the top-mass word
	//: is a property of the RUN, so re-screening renamed items, and two frames
	//: differing only in gender could swap ids. See `slots.item_id`.
	slotItemId: (prompt: string, variant?: string) =>
		get<{ item_id: string; note?: string }>(
			`/slot/item_id?prompt=${encodeURIComponent(prompt)}` +
				(variant ? `&variant=${encodeURIComponent(variant)}` : '')
		),
	//: Takes a declared PAIR, never loose model ids — pooling base+endpoint is a
	//: property of the instrument, not a per-query choice.
	slotPairs: () =>
		get<{ pairs: Pair[]; unresolved: Record<string, string[]>; default: string }>('/slot/pairs'),
	slot: (prompt: string, pairBase: string, k: number) =>
		get<SlotResponse>(
			`/slot?prompt=${encodeURIComponent(prompt)}&pair=${encodeURIComponent(pairBase)}&k=${k}`
		)
};
