"""The prompt catalogue, read from `roster/prompts/` on the fly. No build step.

    from malignment.prompts import Prompt, Prompts

    Prompt("e6_water_M").domain, .language, .partner, .group
    Prompts.where(domain="violence", language="zh")
    Prompts.all()                       # every ADMITTED prompt
    Prompts.all(admitted=None)          # including the 116 rejected pairs

    python -m malignment.prompts        # counts by family and source
    python -m malignment.prompts --write   # build malignment.prompts

## NO BUILD STEP, AND NO `prompt_categorisation.json`

The archive had `scripts/build_prompt_categorisation.py` produce a 2,888-row JSON
that everything then read. That file was BOTH the product and, for 27 of its 38
sources, the only record of its own input — so the admission decision for
`round2_betrayal` (102 of 120 pairs) existed nowhere except inside the artifact it
produced.

RH: *"instead of build_prompt_categorisation.py buried in scripts/ ... have the
reconstruction of all prompts be done on the fly."* So the authored YAML IS the
catalogue. There is no intermediate artifact to go stale, and no build to forget
to re-run.

## THREE FAMILIES, THREE CONTRACTS

    pairs/      a record is a PAIR: pair_id, MARKED, UNMARKED, swap, writer,
                admitted. Yields TWO prompts whose `partner` link is STRUCTURAL.
    generated/  a record is a KERNEL. Prompts are DERIVED by the expander below;
                editing an output is impossible because outputs are not stored.
    flat/       a record is one prompt. RECONSTRUCTED from the archive JSON,
                `writer` and `swap` unrecoverable.

## KEYED BY prompt_id, NEVER BY TEXT

Carried from the archive's `prompts.py`, which learned it expensively: **61 prompt
STRINGS carry more than one row** — one prompt serving two designs. A dict keyed
by text keeps whichever row came last, and that reported *"48 group
disagreements"* where the true figure was 1.

Note the consequence for the store: `twp_words` is keyed by (model, PROMPT TEXT),
because two catalogue entries sharing a string are one forward pass. The
catalogue and the corpus are at different grains ON PURPOSE, and joining them on
text is correct while joining them on prompt_id is not.

## PARTNER IS STRUCTURAL NOW

The archive's module existed because pair partner, group membership and
translation *"were being re-derived by hand in every script that needed them,
four times in one evening, and got it wrong twice."* In `pairs/` the two arms sit
in ONE record, so `partner` is a field read, not a derivation. The class of bug
that module was written to prevent cannot occur for pairs.
"""
import argparse
import collections
import functools
import glob
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS = os.path.join(ROOT, "roster", "prompts")

_CACHE = {}

#: file -> the SOURCE name the archive gave it. Carried because `source` is how
#: every existing query names these populations, and dropping it would make the
#: new catalogue answer a question the old one could and this one could not.
#: One tag per slot file. See the loader for why this is not a single `SLOTS`.
_SLOT_SOURCE = {"round3.yaml": "SLOT_ROUND3",
                "slot-explorer.yaml": "SLOT_EXPLORER",
                "slot-client.yaml": "SLOT_CLIENT",
                "quarantined.yaml": "SLOT_QUARANTINED"}

#: Same block as `slots._CJK`, written as an escape so a file-encoding accident
#: cannot silently narrow it.
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_PAIR_SOURCE = {'round2_desecration.yaml': 'M01_PAIRS_DESECRATION', 'round2_animal.yaml': 'M01_PAIRS_ANIMAL', 'round2_betrayal.yaml': 'M01_PAIRS_BETRAYAL', 'round2_theft.yaml': 'M01_PAIRS_THEFT', 'round2b_power_v2.yaml': 'M01_PAIRS_POWER_R2B', 'sonnet_covert.yaml': 'M01_PAIRS_COVERT', 'sonnet_sexual.yaml': 'M01_PAIRS_SEXUAL', 'sonnet_threat.yaml': 'M01_PAIRS_THREAT', 'sonnet_unarmed.yaml': 'M01_PAIRS_UNARMED', 'sonnet_weapons.yaml': 'M01_PAIRS_WEAPONS', 'm03_kernel.py': 'M03_SPEAKER_KERNEL'}


# ----------------------------------------------------------------- expanders

def _stance(pron, form, sentence_initial):
    """The stance tail. `pron` is 'I' or 'we'; capitalised only after a period.

    PORTED VERBATIM from `meta/M03_proceduralization/m03_kernel.py`. Not tidied:
    the capitalisation rule (a period forces `We`, a comma does not) is one of
    the five declared constraints, and a paraphrase is a second policy.
    """
    p = "I" if pron == "I" else ("We" if sentence_initial else "we")
    if form == "final":
        return "%s should" % p
    if form == "medial":
        return "%s should probably" % p
    if form == "absent":
        return p
    if form == "final_ought":
        return "%s ought to" % p
    raise ValueError(form)


def _expand_kernel(k):
    """One kernel -> its cells. Ported verbatim; see `_stance`."""
    sent_initial = k["joiner"].strip().endswith(".") or k["joiner"] == ". "
    cells = {}
    for arm in ("indiv", "inst"):
        for pron, suffix in (("I", "sg"), ("we", "pl")):
            clause = k["%s_%s" % (arm, suffix)]
            forms = ["final", "medial", "absent"] + (["final_ought"] if pron == "I" else [])
            for form in forms:
                cells["%s_%s_%s" % (arm, pron, form)] = clause + k["joiner"] + \
                    _stance(pron, form, sent_initial)
    return cells


# ----------------------------------------------------------------- loading

def _load(force=False):
    if _CACHE and not force:
        return _CACHE["by_id"], _CACHE["order"]
    import yaml
    by_id, order = {}, []

    def add(row):
        pid = row["prompt_id"]
        #: A REPEATED prompt_id is a collision the archive's module refuses, and
        #: so does this one. Two designs may share a TEXT; they may not share an id.
        if pid in by_id:
            raise ValueError("duplicate prompt_id %r (in %s and %s)"
                             % (pid, by_id[pid]["file"], row["file"]))
        by_id[pid] = row
        order.append(pid)

    for f in sorted(glob.glob(os.path.join(PROMPTS, "pairs", "*.yaml"))):
        base = os.path.basename(f)
        for rec in yaml.safe_load(open(f, encoding="utf-8")) or []:
            pid = rec.get("pair_id")
            for role, key in (("MARKED", "MARKED"), ("UNMARKED", "UNMARKED")):
                if not rec.get(key):
                    continue
                add({"prompt_id": "%s_%s" % (pid, "M" if role == "MARKED" else "U"),
                     "prompt": rec[key], "pair_id": pid, "pair_role": role,
                     "partner_text": rec.get("UNMARKED" if role == "MARKED" else "MARKED"),
                     "domain": rec.get("domain"), "subdomain": rec.get("subdomain"),
                     "language": rec.get("language", "en"),
                     "contrast_type": rec.get("contrast_type"), "swap": rec.get("swap"),
                     "writer": rec.get("writer"),
                     "admitted": bool(rec.get("admitted", True)),
                     "source": _PAIR_SOURCE.get(base, ""),
                     "family": "pairs", "file": base})

    for f in sorted(glob.glob(os.path.join(PROMPTS, "generated", "*.yaml"))):
        base = os.path.basename(f)
        doc = yaml.safe_load(open(f, encoding="utf-8")) or {}
        #: ALL THREE BLOCKS, not just `kernels`. They carry identical fields
        #: (id, domain, f21, frame, joiner, and the four situation clauses), so
        #: one expander serves all: 6 + 4 + 8 = 18 records x 14 cells = 252,
        #: which is exactly what the archive catalogue holds for this source.
        #: Expanding `kernels` alone gave 84 and the shortfall was visible only
        #: because the catalogue count was there to compare against.
        for k in ((doc.get("kernels") or []) + (doc.get("conversions") or [])
                  + (doc.get("unanchored") or [])):
            for cell_id, text in _expand_kernel(k).items():
                add({"prompt_id": "%s_%s" % (k["id"], cell_id), "prompt": text,
                     "domain": k.get("domain"), "language": "en",
                     "kernel_id": k["id"], "cell": cell_id, "frame": k.get("frame"),
                     "admitted": True, "source": "M03_SPEAKER_KERNEL",
                     "family": "generated", "file": base})

    #: **THE SLOT CORPUS, WHICH NO PRODUCER COULD SEE UNTIL NOW.** 173 items sat
    #: in `roster/prompts/slots/` read only by the authoring stack (`slots.py`,
    #: `serve.py`, `slot_client.py`), so no fleet worklist could reach them and
    #: only 2 of 173 had ever been measured beyond their screening pair.
    #:
    #: `item_id` becomes `prompt_id` unchanged: it is already a pure function of
    #: the prompt, already unique across the three files, and collides with none
    #: of the existing 3,120 ids (checked, not assumed).
    #:
    #: **ONE SOURCE PER FILE, because the corpus is two instruments.** The
    #: `round3` items were screened on `meta-llama/Llama-3.1-8B` and everything
    #: since on `SmolLM3-3B-Base`, so their masses are not comparable -- saved and
    #: recomputed `share` agree within 0.01 on only 31 of 96. A single `SLOTS`
    #: tag would bury that; three tags make it a query.
    #:
    #: **QUARANTINED ITEMS STAY ADMITTED AND ARE MEASURED.** They were briefly
    #: stamped `admitted: false`, on the reasoning that this is the mechanism the
    #: 232 rejected pairs use. RH caught it: the fleet selects with
    #: `Prompts.all()` (`runners.py:690`), which filters `admitted=True`, so an
    #: unadmitted prompt is never scored by ANY path -- not even `--all-prompts`,
    #: whose help text says "every admitted prompt" and which I had misread as
    #: bypassing the filter.
    #:
    #: Quarantine judges the TAGGING; twp measures the PROMPT'S DISTRIBUTION.
    #: The two are orthogonal, and measuring a quarantined prompt costs one cell
    #: while keeping the option open -- where skipping it forecloses that option
    #: until another fleet pass. So the flag travels on the row and downstream
    #: excludes them; the measurement does not.
    for f in sorted(glob.glob(os.path.join(PROMPTS, "slots", "*.yaml"))):
        base = os.path.basename(f)
        src = _SLOT_SOURCE.get(base) or ("SLOT_" + re.sub(r"[^A-Z0-9]+", "_",
                                         base.rsplit(".", 1)[0].upper()).strip("_"))
        for rec in yaml.safe_load(open(f, encoding="utf-8")) or []:
            if not rec.get("item_id") or not rec.get("prompt"):
                continue
            add({"prompt_id": rec["item_id"], "prompt": rec["prompt"],
                 "domain": rec.get("domain"), "subdomain": None,
                 #: Detected rather than assumed: every slot prompt is English
                 #: today and nothing stops a CJK one being authored tomorrow.
                 "language": "zh" if _CJK_RE.search(rec["prompt"]) else "en",
                 "admitted": bool(rec.get("admitted", True)),
                 #: The flag, not the reason. The `quarantine` block beside it in
                 #: the yaml records who flagged the item and why.
                 "quarantined": bool(rec.get("quarantined")),
                 #: Carried through so a population can be selected on review
                 #: state, which is the open work on this corpus.
                 "reviewed": rec.get("reviewed"),
                 "authored_by": rec.get("authored_by"),
                 "source": src, "family": "slots", "file": base})

    #: **`subject/` IS READ THE SAME WAY AS `flat/` AND KEPT SEPARATE ANYWAY.**
    #: The record shape is identical, so the loop is shared; the FAMILY is not,
    #: because these are the only prompts in the catalogue authored for the
    #: FRAMED instrument. They are questions -- the other 2,983 are continuation
    #: stems, and 0 of them are questions -- so a caller that wants "the
    #: catalogue" and a caller that wants "things you can ask a chat model" want
    #: different sets, and `family` is what lets them say which.
    #:
    #: One file per CLASS so provenance travels with the class and a class can be
    #: excluded on its own: `subject_refusal` is coconot TEST (frozen strings,
    #: derivation recorded in the file), the other three are authored. A control
    #: drawn from a training mix is seen by some arms and not others, and that
    #: fact has to survive into the catalogue rather than living in a docket post.
    for sub, fam in (("flat", "flat"), ("subject", "subject")):
        for f in sorted(glob.glob(os.path.join(PROMPTS, sub, "*.yaml"))):
            base = os.path.basename(f)
            doc = yaml.safe_load(open(f, encoding="utf-8")) or {}
            for rec in doc.get("prompts") or []:
                r = dict(rec)
                r.setdefault("prompt_id",
                             "%s_%d" % (doc.get("source", base), len(order)))
                r.update({"source": doc.get("source"), "admitted": True,
                          "family": fam, "file": base})
                add(r)

    _CACHE.update(by_id=by_id, order=order)
    return by_id, order


def reload():
    _CACHE.clear()
    return _load(force=True)


#: The 105-pair transgressive sample, in the READ-ONLY archive. Declared here so
#: the one archive dependency of this module has a name rather than being a
#: literal inside a function.
PAIRS_CSV = "/Users/rj416/github/malign-logits/data/beam_sample_105.csv"


class Prompt:
    """One catalogue entry, keyed by prompt_id."""

    def __init__(self, prompt_id):
        by_id, _ = _load()
        if prompt_id not in by_id:
            raise KeyError("no prompt_id %r" % prompt_id)
        self.prompt_id = prompt_id
        self._row = by_id[prompt_id]

    def __repr__(self):
        return "Prompt(%r)" % self.prompt_id

    def __getattr__(self, name):
        try:
            return self._row[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def text(self):
        return self._row["prompt"]

    @property
    def partner(self):
        """The other arm of the pair, or None. STRUCTURAL for `pairs/`."""
        pid = self._row.get("pair_id")
        if not pid:
            return None
        other = "%s_%s" % (pid, "U" if self._row.get("pair_role") == "MARKED" else "M")
        by_id, _ = _load()
        return Prompt(other) if other in by_id else None


#: **A ROW IS LIVE IF ITS STATUS IS ACTIVE OR ABSENT.** RH's ruling, 2026-08-16.
#:
#: This port kept the `admitted` gate and DROPPED the status one, so every count
#: silently included 93 RETIRED, 2 DISPUTED and 10 "MIXED: ACTIVE/DISPUTED"
#: prompts -- 95 rows a previous seat had struck. The archive's own docstring
#: says why it defaults on: *"ACTIVE BY DEFAULT. Every count wants the status
#: filter and forgetting it once produced 'source=OTHER: 55' where the answer
#: was 4."* Two gates existed for two different reasons; carrying one across is
#: how the other's work gets quietly undone.
#:
#: MISSING COUNTS AS LIVE because 1,852 of 3,120 rows carry no status field at
#: all -- these predate the field, and reading absence as "retired" would delete
#: 60% of the corpus on a technicality. Absence is not a withdrawal.
LIVE_STATUS = ("ACTIVE", "")


def _is_live(row):
    return str(row.get("status") or "").upper() in LIVE_STATUS


class Prompts:
    @staticmethod
    def all(admitted=True, live=True):
        """Declared prompts. `live=False` opts into RETIRED/DISPUTED as well."""
        by_id, order = _load()
        return [Prompt(p) for p in order
                if (admitted is None or by_id[p].get("admitted") == admitted)
                and (not live or _is_live(by_id[p]))]

    @staticmethod
    def struck():
        """The rows a seat withdrew: RETIRED, DISPUTED, or MIXED. Visible on purpose."""
        by_id, order = _load()
        return [Prompt(p) for p in order if not _is_live(by_id[p])]

    @staticmethod
    def where(admitted=True, live=True, **fields):
        out = []
        for p in Prompts.all(admitted=admitted, live=live):
            if all(p._row.get(k) == v for k, v in fields.items()):
                out.append(p)
        return out

    # ------------------------------------------------------------ populations
    #
    # **A NAMED FUNCTION IS THE DEFINITION.** The archive's `representative
    # pairs` had six answers on one afternoon because the definition lived in six
    # producers instead of one name. Each helper below states its rule, and each
    # returns ROWS rather than a count so a reader can see the selection instead
    # of inferring it from a total.

    @staticmethod
    def transgressive_pairs(language=None):
        """MARKED/UNMARKED pairs whose contrast is a TRANSGRESSIVE SWAP.

        1,513 prompts of 2,888 -- the dominant design. One token apart by
        construction: `sedative -> cinnamon`, `diary -> postcard`. **Not every
        pair is this**: `pole_swap` (190) forces a choice between two poles and
        tests superposition, `intensity_ladder` (111) varies degree, and pooling
        them measures neither -- which is the distinction `finding` was added to
        the archive's schema to protect.
        """
        f = {"contrast_type": "transgressive_swap"}
        if language:
            f["language"] = language
        return Prompts.where(**f)

    @staticmethod
    def institutional():
        """The M03 speaker-kernel scenarios. 252 prompts, DERIVED from 18 kernels.

        Institutional against individual stance, crossed with speaker, person and
        form. These are the only prompts in the catalogue that are GENERATED
        rather than authored one by one, and editing an output is impossible
        because outputs are not stored -- see `roster/prompts/generated/`.
        """
        return Prompts.where(family="generated")

    @staticmethod
    def framed_population(pairs_csv=None):
        """The declared prompt set for the FRAMED (prefill) measurement. 840 texts.

        **A UNION OVER DISTINCT STRINGS, WHICH IS NOT WHAT SUMMING GIVES.**

            F01       49      M03      252      PAIR105   210
            F21       51      SLOT     279      SUBJECT    34
                                                ------------------
                                                UNION     874

        The parts sum to 841. Forty-eight duplicate strings sit inside the slot
        corpus alone (327 entries, 279 texts), one inside F21, and one string is
        shared between F01 and SLOT -- so summing the GROUPS gives 890 and
        over-costs a fleet by 6%, and summing the distinct parts gives 841 and
        is still wrong by one. Only the set union is right, and it is taken over
        `.text` because the corpus is keyed by the string, not by the entry.

        **RETURNS STRINGS, NOT PROMPT OBJECTS.** One text can be several
        catalogue entries -- 127 entries share a text with another -- and a
        framed cell is keyed by (model, prompt, frame, ...) with no entry in it.
        Returning objects would invite a caller to measure the same surface
        twice and count it as two.

        The 105-pair transgressive sample lives in the READ-ONLY archive
        (`malign-logits/data/beam_sample_105.csv`, seed 20260805). It is read,
        never written, and the artifact built from this
        (`roster/prompts/populations/prefill.txt`, via
        `scripts/build_prompt_population.py`) lives here -- so the dependency is
        on a source we could lose rather than on a file we could not rebuild.
        Absent, the sample contributes nothing and the caller is told; it is not
        silently 210 prompts short.
        """
        import csv as _csv
        import os as _os
        g = lambda p_, k: getattr(p_, k, None)                    # noqa: E731
        ps = Prompts.all()
        out = {
            "F01": {p_.text for p_ in ps if g(p_, "finding") == "F01"},
            "F21": {p_.text for p_ in ps if g(p_, "finding") == "F21"},
            "M03": {p_.text for p_ in Prompts.institutional()},
            "SLOT": {p_.text for p_ in ps
                     if str(g(p_, "source") or "").startswith("SLOT")},
            #: **THE ONLY PROMPTS IN THE SET THAT ARE QUESTIONS.** The other 840
            #: are continuation stems -- 0 questions, 1 occurrence of the word
            #: "you" -- which suits the RAW instrument and suits `prefill`,
            #: where the stem becomes a started assistant turn. It does not suit
            #: `chat`, where "The capital of France is" is a user message nobody
            #: would send, and it cannot ask the question the frame makes
            #: askable at all: what the model becomes when it is ADDRESSED.
            #:
            #: `SUBJECT_NEUTRAL` is the one that makes the rest readable. Every
            #: framed prompt is addressed, so an all-addressed population HAS NO
            #: NULL -- without a floor you cannot separate "the model speaks in
            #: the first person" from "the model was addressed at all". Measured
            #: by lacan on Tulu-3-8B-SFT, first-person mass at the answer slot:
            #: refusal 0.905, identity 0.806, conversational 0.034, neutral
            #: 0.001. The floor costs 8 prompts and is what the other three are
            #: read against.
            "SUBJECT": {p_.text for p_ in ps
                        if g(p_, "family") == "subject"},
        }
        path = pairs_csv or PAIRS_CSV
        if _os.path.exists(path):
            with open(path) as fh:
                out["PAIR105"] = {r["prompt"] for r in _csv.DictReader(fh)}
        else:
            out["PAIR105"] = set()
        return out

    @staticmethod
    def chinese():
        """The 457 Chinese-language prompts.

        Kept as their own population because the tail behaves differently: a
        Chinese cell carries more of its mass below theta, so `js_tail` is
        systematically larger and a pooled JS understates divergence there.
        """
        return Prompts.where(language="zh")

    @staticmethod
    def pairs(contrast_type=None, **fields):
        """Every prompt that has a partner. `contrast_type` narrows the design."""
        out = [p for p in Prompts.all() if p._row.get("pair_id")]
        if contrast_type:
            out = [p for p in out if p._row.get("contrast_type") == contrast_type]
        return [p for p in out if all(p._row.get(k) == v for k, v in fields.items())]

    @staticmethod
    def rejected():
        """The 232 prompts from pairs NOT admitted to the catalogue.

        Present here and absent from the archive entirely. `admitted: false`
        records the FACT; for round 2 the REASON was never written down, and
        `round2_animal` alone is 70 of 120 rejected.
        """
        return Prompts.all(admitted=False)

    @staticmethod
    def texts(admitted=True):
        """DISTINCT prompt TEXTS — the grain the corpus is keyed at."""
        return sorted({p.text for p in Prompts.all(admitted=admitted)})


DDL = """
CREATE TABLE IF NOT EXISTS {db}.prompts (
    prompt_id String, prompt String,
    family LowCardinality(String), file LowCardinality(String),
    source LowCardinality(String), finding LowCardinality(String),
    language LowCardinality(String),
    domain LowCardinality(String), subdomain LowCardinality(String),
    slot LowCardinality(String), contrast_type LowCardinality(String),
    pair_id String, pair_role LowCardinality(String), partner_text String,
    kernel_id LowCardinality(String), cell LowCardinality(String),
    swap String, writer String,
    status LowCardinality(String), admitted UInt8,
    archive_prompt_id String
) ENGINE = ReplacingMergeTree ORDER BY prompt_id
"""

#: EVERY COLUMN IS WRITTEN, EVEN WHEN EMPTY. The archive's `prompt_catalogue`
#: table carried 13 of the JSON's 20 fields -- `contrast_type`, `axes_expected`,
#: `group_id`, `group_role`, `ladder_id`, `ladder_rank` and `pair_contrast` were
#: dropped -- so anything needing one of them had to go back to the JSON, and the
#: table and the file were two grains of the same catalogue. Here the YAML is the
#: only source and the table carries what it holds.
COLUMNS = ("prompt_id", "prompt", "family", "file", "source", "finding",
           "language", "domain", "subdomain", "slot", "contrast_type",
           "pair_id", "pair_role", "partner_text", "kernel_id", "cell",
           "swap", "writer", "status", "admitted", "archive_prompt_id")


# ---------------------------------------------------------------------------
# Corpus accessors (moved from corpus.py)
# ---------------------------------------------------------------------------

PAIRS_POPULATION = """SELECT base FROM {db}.pairs
                      UNION DISTINCT SELECT aligned FROM {db}.pairs"""


def panel(models=None, live=True, verbose=False):
    """(n_models, prompts) -- prompts held by EVERY model in the population.

    **NOT "all prompts".** Prompt sets are fleet-defined and do not nest: the
    universal intersection over all 402 measured models is ONE prompt; over the
    154 in `pairs` it is 2,190. A cross-model comparison on anything wider is
    comparing differently-composed batteries.

    **THE STATUS GATE IS APPLIED, NOT ASSUMED.** Building the panel from
    `twp_words` alone takes whatever was MEASURED, which is not the declared
    population -- it admitted `f11_reason_BOTH`, status
    `MIXED: ACTIVE/DISPUTED`, which `Prompts.all()` excludes. One prompt of
    1,760, and the defect is not its size: the panel was being defined by
    measurement history rather than by the declaration, and a seat struck that
    prompt for a reason.

    `models=None` means the pairs population. Pass an explicit set for a
    different population -- the step/ladder checkpoints, say, whose own crossed
    panel is 2,247 and shares only 473 prompts with this one.
    """
    from . import ch
    if models is None:
        n = ch.scalar("SELECT count(DISTINCT base) FROM (%s) AS t"
                      % PAIRS_POPULATION.replace("base FROM", "base AS base FROM")
                      .replace("SELECT aligned", "SELECT aligned AS base"))
        rows = ch.query("""SELECT prompt FROM {db}.twp_words
            WHERE model IN (%s) GROUP BY prompt
            HAVING count(DISTINCT model) = %d""" % (PAIRS_POPULATION, n))
    else:
        ms = "','".join(m.replace("'", "\\'") for m in sorted(models))
        n = len(set(models))
        rows = ch.query("""SELECT prompt FROM {db}.twp_words
            WHERE model IN ('%s') GROUP BY prompt
            HAVING count(DISTINCT model) = %d""" % (ms, n))
    crossed = [r["prompt"] for r in rows]
    if not live:
        return n, crossed
    declared = {p.text for p in Prompts.all()}
    kept = [p for p in crossed if p in declared]
    if verbose and len(kept) != len(crossed):
        print("  panel: %d crossed, %d dropped by the status gate"
              % (len(crossed), len(crossed) - len(kept)))
    return n, kept


@functools.lru_cache(maxsize=1)
def _rows_by_text():
    """{prompt_text: [row, ...]} -- ALL declared rows, because texts repeat.

    2,783 declared rows are 2,706 distinct TEXTS: 73 texts appear more than
    once and **47 of those disagree about `domain`**. `He slammed her against
    the wall and` is `violence` under `setd_and_M_2` and `other` under
    `store_g004_B`. Collapsing to one row per text -- by dict comprehension, or
    by `setdefault` in a loop -- resolves that by ITERATION ORDER, silently, and
    every experiment stratifying by domain has been doing so.
    """
    out = collections.defaultdict(list)
    for p in Prompts.all():
        out[p.text].append(p._row)
    return dict(out)


def domain_conflicts():
    """{text: {domain: [prompt_id, ...]}} for texts whose rows disagree.

    Reported, not resolved silently. A stratified result should say how many of
    its prompts sat here.
    """
    out = {}
    for text, rows in _rows_by_text().items():
        by = collections.defaultdict(list)
        for r in rows:
            d = (r.get("domain") or "").strip()
            if d:
                by[d].append(r.get("prompt_id"))
        if len(by) > 1:
            out[text] = dict(by)
    return out


def domains(prompts=None, on_conflict="specific"):
    """{prompt_text: domain}. Deterministic, and the rule is declared.

    `on_conflict`:
      "specific"  prefer a named domain over the catch-all `other`; among
                  equals take the lexicographically first prompt_id, so the
                  answer does not depend on file order. THE DEFAULT, because
                  `other` is an absence of classification rather than a claim.
      "drop"      exclude conflicted texts entirely. The conservative choice for
                  a result that leans on domain.
      "first_id"  lowest prompt_id wins whatever it says.
    """
    keep = set(prompts) if prompts is not None else None
    conflicted = set(domain_conflicts())
    out = {}
    for text, rows in _rows_by_text().items():
        if keep is not None and text not in keep:
            continue
        cands = sorted((r.get("prompt_id") or "", (r.get("domain") or "").strip())
                       for r in rows if (r.get("domain") or "").strip())
        if not cands:
            continue
        if text in conflicted:
            if on_conflict == "drop":
                continue
            if on_conflict == "specific":
                named = [c for c in cands if c[1] != "other"]
                cands = named or cands
        out[text] = cands[0][1]
    return out


@functools.lru_cache(maxsize=1)
def prompt_map():
    """{prompt_text: row}. FIRST row by prompt_id, deterministically.

    **THE AUTHORED FILES ARE THE AUTHORITY AND `{db}.prompts` IS DOWNSTREAM.**
    The first version of this module read the ClickHouse table and moved 970
    rows -- prompts the declaration gives a domain came back as `other`,
    silently, inside a SHARED accessor every experiment was about to adopt. A
    read layer that changes the source of truth is worse than the inline SQL it
    replaces, because the inline copy at least showed which table it hit.
    """
    return {t: sorted(rows, key=lambda r: r.get("prompt_id") or "")[0]
            for t, rows in _rows_by_text().items()}


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    by_id, order = _load()
    fam = collections.Counter(by_id[p]["family"] for p in order)
    adm = sum(1 for p in order if by_id[p].get("admitted"))
    print("  roster/prompts/ -> %d entries, %d admitted, %d not"
          % (len(order), adm, len(order) - adm))
    for k, v in fam.most_common():
        print("     %-12s %d" % (k, v))
    print("  distinct prompt TEXTS (the corpus grain): %d" % len(Prompts.texts()))
    dup = len(Prompts.all()) - len(Prompts.texts())
    print("  entries sharing a text with another: %d  <- why the key is prompt_id" % dup)
    if not a.write:
        print("\n  --write to build the prompts table")
        return 0
    from . import ch
    ch.execute("DROP TABLE IF EXISTS {db}.prompts")
    ch.execute(DDL)
    rows = []
    for p in order:
        r = by_id[p]
        row = {}
        for k in COLUMNS:
            v = r.get(k)
            row[k] = int(bool(v)) if k == "admitted" else ("" if v is None else str(v))
        row["admitted"] = int(bool(r.get("admitted")))
        rows.append(row)
    ch.insert("prompts", rows)
    print("\n  %s.prompts: %s rows" % (ch.DB, format(ch.scalar(
        "SELECT count() FROM {db}.prompts"), ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
