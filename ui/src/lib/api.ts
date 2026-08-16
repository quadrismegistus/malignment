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

export interface Health {
	status: string;
	db: string;
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
	//: Per-rung distributions, so a movement split needs no second expansion.
	per_arm: Record<string, Record<string, number>>;
	//: **THE LICENCE TO READ MOVEMENT.** Non-null only when the two models named
	//: are a declared ALIGNING edge. Any two models can be pooled; only a
	//: declared edge makes the difference between them a treatment effect.
	edge: { base: string; aligned: string; op: string } | null;
	rule_version: number;
	dict_sha: string;
	theta: number;
	skipped: string | null;
}

export interface Split {
	dN: number;
	suppression: number;
	substitution: number;
	movers: [string, number][];
}

export interface AxisResponse {
	ok: boolean;
	//: Present only when both arms were sent. **Never read dN without `leverage`
	//: from the same response** — the axis scores substitutions near-neutral, so
	//: ΔN cancels while something large happens.
	split: Split | null;
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

async function post<T>(path: string, body: unknown): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	const j = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
	if (!res.ok) throw new Error((j as { error?: string }).error || `HTTP ${res.status}`);
	return j as T;
}

export const api = {
	//: POST for PAYLOAD SIZE, not side effects — it writes nothing. At k=500 the
	//: candidate list is kilobytes, past what a URL carries reliably.
	slotAxis: (
		prompt: string,
		naughty: string[],
		nice: string[],
		words: string[],
		probs?: Record<string, number>,
		//: BOTH OR NEITHER — the server refuses one alone, because a single arm
		//: diffs against an empty distribution and yields a finite number about
		//: nothing.
		base_probs?: Record<string, number>,
		aligned_probs?: Record<string, number>
	) =>
		post<AxisResponse>('/slot/axis', {
			prompt, naughty, nice, words, probs, base_probs, aligned_probs
		}),
	health: () => get<Health>('/health'),
	inventory: () => get<{ db: string; tables: Table[] }>('/store/inventory'),
	roster: () => get<RosterSummary>('/roster'),
	population: (kind: string) =>
		get<{ kind: string; n: number; members: string[] }>(
			`/roster/population?kind=${encodeURIComponent(kind)}`
		),
	experiments: () => get<Experiments>('/experiments'),
	experiment: (id: string) => get<QuestionDetail>(`/experiment?id=${encodeURIComponent(id)}`),
	result: (id: string, grain: string, limit?: number) =>
		get<ResultRows | ResultJson>(
			`/experiment/result?id=${encodeURIComponent(id)}&grain=${encodeURIComponent(grain)}` +
				(limit ? `&limit=${limit}` : '')
		),
	//: DERIVED SERVER-SIDE. `nice` and `naughty` must be the HIGHEST-MASS word of
	//: each branch, not the first tagged — the id is a property of the
	//: distribution, not of the order someone clicked.
	slotItemId: (prompt: string, nice: string, naughty: string) =>
		get<{ item_id: string }>(
			`/slot/item_id?prompt=${encodeURIComponent(prompt)}` +
				`&nice=${encodeURIComponent(nice)}&naughty=${encodeURIComponent(naughty)}`
		),
	slot: (prompt: string, model: string, k: number) =>
		get<SlotResponse>(
			`/slot?prompt=${encodeURIComponent(prompt)}&model=${encodeURIComponent(model)}&k=${k}`
		)
};
