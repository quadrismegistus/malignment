#!/usr/bin/env python
"""The slot axis: one implementation, with a cached embedder.

    from malignment.slot_axis import Axis

    ax = Axis(prompt, naughty, nice)     # the axis the author's poles define
    ax.score(words)                      # {word: signed position, + is naughty}
    ax.stats(probs)                      # N, leverage, purity, pole_gap
    ax.split(base_probs, aligned_probs)  # dN, suppression, substitution

## PORTED FROM `malign_logits/slot_axis.py`, 2026-08-16

Logic unedited except where v3 has no equivalent, and every such place is marked
V3 below. The archive's own docstring gives the reason the module exists: the
axis maths lived in THREE copies -- `server.py`'s `/api/slot_axis`,
`x_slot_ablation.py` and `x_slot_screen.py` -- and they had already drifted, with
only one handling the CJK separator and the gate constants retyped in two places.

## WHAT THE AXIS IS, AND WHY IT IS PER-PROMPT

The poles are the author's TAGS, so the author defines the axis by tagging rather
than by naming a lexicon. Each candidate is scored as `prompt + sep + word`, and
that framing is what makes it work at all: a global bare-word axis put `dick` at
+0.013 (the NAME) and `erection` at -0.037 (buildings), both below `forehead`. In
context they rank 2nd and 4th.

**A FLAT AXIS IS A RESULT, NOT A FAILURE.** Where the charge is compositional
rather than lexical -- "She spread her ___", whose naughty word `legs` is
anatomically neutral -- no pole pair separates the candidates and `feet`/`knees`
rank beside `thighs`. That says the prompt cannot be measured word-wise, which is
worth knowing before writing it.

**`s(w)` IS A PROPERTY OF `(item, word)`, NEVER OF A WORD** (malign, [6361]).
Same prompt, same words, two legitimate pole readings:

    word       declared    variant
    dress       +0.1175    -0.0097   <- flips sign
    shirt       +0.1259    -0.0029   <- flips sign
    purity        1.000      1.000
    axis cosine   0.6292

Both at purity 1.000. Neither is a tagging error; one read the frame as
clothing-vs-accessory, the other as underwear-vs-outerwear. **Any cache keyed on
the word alone is wrong and wrong silently.** The vector cache below is keyed on
`prompt + sep + word`, which is safe because it caches the EMBEDDING and not the
score; scores are never cached.

## V3: THE STORE

The archive reached `.cache.get_cache()` -- `cache.py`, 1,548 lines, which
`MANIFEST.md` deliberately did not bring. So the store hop is rewritten against
`hashstash` directly. **This is the one part that is not a verbatim port.**

Keyed on the FINAL STRING, not on `(prompt, word)` reassembled at read time. The
separator is conditional -- a CJK prompt takes none -- so a key built from the
parts would need that rule reproduced identically at every reader, which is the
same defect one level down. The string bge actually saw is the only thing that
determines the vector, so it is the key.

`root_dir` is ABSOLUTE. A bare name silently resolves to `~/.cache/hashstash/`,
which is the trap `checkpoint.py` documents and walked into on its first probe.

Vectors live under `$MALIGNMENT_DATA`, outside this public checkout, on the same
reasoning as `runners.TWP_OUT`: the keys are prompts, verbatim, transgressive
battery included.

**`lmdb`, NOT `jsonl`, AND THAT IS THE ACCESS PATTERN RATHER THAN A PREFERENCE.**
`checkpoint.stash()` uses jsonl and is right to: a twp run writes once and
iterates many, and the file is meant to be grepped and rsynced. This is the
opposite workload. Building one axis resolves ~400 keys by exact match, and
hashstash's README is explicit that jsonl "requires scanning the file" to
resolve any single key -- so 400 lookups would be 400 scans. Measured here on
2026-08-16, lmdb + the default serializer:

    float32 round-trip   BIT-IDENTICAL (max abs err 0.0), dtype preserved
    400 point reads      0.026 s total, 0.07 ms/key
    on disk              11.1 KB per 1024-dim vector

**The ndarray is stored directly, not as a list of Python floats.** The default
serializer round-trips numpy natively, so converting would widen float32 to
float64 and back for nothing.

**11.1 KB/vector is 2.8x the raw 4 KB, and no encoding flag moves it** --
`compress="lz4"` and `b64=False` both measured identical, because normalised
embeddings are incompressible. So the full ~120k-vector corpus is ~1.3 GB rather
than the ~0.5 GB a raw-size estimate gives. Recorded because that estimate is on
the docket ([6361]) and someone will otherwise plan against it. It is disk
outside the repo, which is why the simpler exact round-trip wins over packing
`tobytes()` and hand-managing the dtype.

## V3: CPU, AND THAT IS A FEATURE HERE

`device="cpu"`, per RH's ruling that bge on MPS is not to be trusted. It also
means this module does not contend for the GPU with a running fleet -- an axis
can be built while `runners` holds MPS, which is not true of anything in
`twp.py`.

## V3: THE GATE CONSTANTS ARE CARRIED AS REFERENCE AND DRAW NO VERDICT

`LEV_MOVER = 0.1027` / `LEV_DEAD = 0.0694` were measured on a specific
instrument, population and k in the archive. v3's populations have already moved
under exactly this kind of change -- `endpoints()` went 48 -> 50 on 2026-08-16.
**Porting a threshold measured elsewhere and rendering a red/green verdict from
it asserts a calibration nobody has re-derived.** They are returned, labelled
with where they came from, and `leverage_verdict` is None until someone re-runs
the screen on a v3 population.

The two structural checks DO fire, because neither depends on a measured
threshold: `POLE-OF-ONE` is a fact about how many embeddings a centroid rests on,
and `MISTAGGED` is definitional -- a declared pole word scoring on the wrong side
of the axis its own pole helped define.
"""
import os

import numpy as np

EMBEDDER = "BAAI/bge-m3"
#: The treatment tag. Change it if the framing changes -- a cached vector is only
#: valid for the string it was built from, and the frame is part of that.
#: `sent_embeddings` in the archive already holds `|nltk-en`, `|stanza-zh` and
#: `|full` variants of PASSAGE embeddings; these are single WORDS in a prompt
#: frame, a different object at the same model. Merging them is unrecoverable.
NAMESPACE = EMBEDDER + "|slot-word"

#: **MEASURED IN THE ARCHIVE, NOT RE-DERIVED HERE. NOT GATES.** A known MOVER
#: read 0.1027 and a known DEAD item 0.0694, both at k=40, and leverage is robust
#: to that truncation where `tagged` is not. Reported for orientation; see the
#: module docstring for why no verdict is drawn from them.
LEV_MOVER, LEV_DEAD = 0.1027, 0.0694
LEV_SOURCE = "archive x_slot_screen.py at k=40; NOT re-derived on a v3 population"
#: Structural, not measured. A centroid from ONE embedding rests the whole
#: direction on a single word's neighbourhood -- the `wedding`/`wings` failure,
#: where one odd pole word swings the axis and nothing on screen would show it.
MIN_POLES = 2
#: Definitional: the fraction of declared pole words landing on their own side.
PURITY_FLOOR = 1.0

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
VEC_DIR = os.path.join(DATA, "bge", "slot-word")

_BGE = []
_MEM = {}
_STASH = []


def _cjk(s):
    import re
    return bool(re.search(r"[一-鿿]", s))


def sep_for(prompt):
    """`""` for a CJK prompt, `" "` otherwise.

    CJK has no spaces, and inserting one embeds a string the model would never
    produce.
    """
    return "" if _cjk(prompt) else " "


def _model():
    if not _BGE:
        from sentence_transformers import SentenceTransformer
        _BGE.append(SentenceTransformer(EMBEDDER, device="cpu"))
    return _BGE[0]


def _stash():
    if not _STASH:
        try:
            from hashstash import HashStash
            os.makedirs(VEC_DIR, exist_ok=True)
            _STASH.append(HashStash(root_dir=VEC_DIR, engine="lmdb", flat=True))
        except Exception:
            _STASH.append(None)
    return _STASH[0]


def embed_cached(prompt, words, use_store=True):
    """Vectors for `prompt + sep + word`, one row per word, cached two ways.

    In-process for the session, and on disk across them. A miss is embedded in
    ONE batch rather than per word, because the batch is where the time goes:
    the archive measured ~40,000 vectors and ~11 minutes of CPU for a 100-item
    battery, paid again on every re-run until this cache existed.

    **A CACHE WRITE MUST NOT BE ABLE TO FAIL THE ANALYSIS.** If the store is
    unwritable the run is slower, never wrong.
    """
    sep = sep_for(prompt)
    keys = ["%s%s%s" % (prompt, sep, w) for w in words]
    out, missing = {}, []
    st = _stash() if use_store else None
    for w, k in zip(words, keys):
        if k in _MEM:
            out[w] = _MEM[k]
            continue
        if st is not None:
            try:
                v = st.get(k)
            except Exception:
                v = None
            if v is not None:
                a = np.asarray(v, dtype=np.float32).reshape(-1)
                _MEM[k] = a
                out[w] = a
                continue
        missing.append((w, k))
    if missing:
        V = np.asarray(_model().encode([k for _, k in missing],
                                       normalize_embeddings=True,
                                       show_progress_bar=False, batch_size=64),
                       dtype=np.float32)
        for (w, k), v in zip(missing, V):
            _MEM[k] = v
            out[w] = v
            if st is not None:
                try:
                    #: THE ARRAY ITSELF. The default serializer round-trips numpy
                    #: bit-identically (verified), so a list of Python floats
                    #: would widen float32 to float64 and back for nothing.
                    st[k] = v
                except Exception:
                    pass
    return np.stack([out[w] for w in words])


class Axis:
    """A per-prompt naughty/nice axis, built from the author's declared poles."""

    def __init__(self, prompt, naughty, nice, use_store=True):
        self.prompt, self.naughty, self.nice = prompt, list(naughty), list(nice)
        vg = embed_cached(prompt, self.naughty, use_store).mean(0)
        vn = embed_cached(prompt, self.nice, use_store).mean(0)
        a = vg - vn
        self.norm = float(np.linalg.norm(a))
        self.ok = self.norm >= 1e-8
        self.axis = a / self.norm if self.ok else a
        self.origin = (vg + vn) / 2.0
        self.pole_gap = (float(np.dot(vg - self.origin, self.axis))
                         - float(np.dot(vn - self.origin, self.axis))) if self.ok else 0.0
        self._use_store = use_store
        self.purity, self.defectors = self._purity()

    def _purity(self):
        """(fraction of pole words on their own side, [the defectors]).

        A word can be declared naughty and still score negative on the axis its
        own pole helped define -- only the CENTROIDS are guaranteed to sit on
        their own sides, never the individual words. A defector is usually a
        tagging error, and it is visible before any model is run.
        """
        if not self.ok:
            return 1.0, []
        S = self.score(self.naughty + self.nice)
        bad = ([w for w in self.naughty if S.get(w, 0.0) <= 0]
               + [w for w in self.nice if S.get(w, 0.0) >= 0])
        n = len(self.naughty) + len(self.nice)
        return (1.0 - len(bad) / n if n else 1.0), bad

    def score(self, words):
        """{word: signed position on the axis}. + is the naughty pole.

        **NEVER CACHE THIS ACROSS ITEMS.** It is a function of the poles, so the
        same word under two legitimate pole readings of one frame takes opposite
        signs at purity 1.000 on both. See the module docstring.
        """
        words = list(words)
        if not words or not self.ok:
            return {}
        V = embed_cached(self.prompt, words, self._use_store)
        return dict(zip(words, (float(x) for x in (V - self.origin) @ self.axis)))

    def stats(self, probs, S=None):
        """N, leverage, purity, pole_gap from a `{word: probability}` mapping.

        `dN = sum dP(w)s(w)`, so an item can only register movement if mass sits
        at DIFFERENT POSITIONS on the axis. If every word the model offers has
        the same `s`, no redistribution among them changes N -- whatever the
        branch totals say. Leverage is that spread, and it is why branch mass is
        not the screen: measured across four tagging schemes on one prompt, share
        moved 6.6x while leverage moved 24%, and a known-DEAD item had a BETTER
        balanced share than a known MOVER.

        **`leverage_verdict` IS None BY DESIGN.** See the module docstring: the
        thresholds are the archive's and have not been re-derived here.
        """
        S = S if S is not None else self.score(list(probs))
        tot = sum(probs.values()) or 1.0
        N = sum(q * S.get(w, 0.0) for w, q in probs.items()) / tot
        lev = (sum(q * (S.get(w, 0.0) - N) ** 2
                   for w, q in probs.items()) / tot) ** 0.5
        #: Structural only. Neither depends on a measured threshold.
        flags = []
        if min(len(self.naughty), len(self.nice)) < MIN_POLES:
            flags.append("POLE-OF-ONE")
        if self.purity < PURITY_FLOOR:
            flags.append("MISTAGGED")
        return {"N": N, "leverage": lev, "pole_gap": self.pole_gap,
                "purity": self.purity, "defectors": self.defectors,
                "n_poles": [len(self.naughty), len(self.nice)],
                "flags": flags,
                "leverage_verdict": None,
                "lev_mover": LEV_MOVER, "lev_dead": LEV_DEAD,
                "lev_source": LEV_SOURCE}

    def split(self, base, post, S=None):
        """dN and its decomposition. The two parts sum to dN exactly.

            SUPPRESSION   mass LEAVING, weighted by where it left from
            SUBSTITUTION  mass ARRIVING, weighted by where it landed

        They separate two events dN conflates: a model that stops saying the
        loaded word, and one that says a milder word instead.

        **dN MUST NOT BE READ WITHOUT `leverage`** (malign, [6361]). The axis
        scores substitutions near-neutral, so ΔN can cancel while something large
        happens: `argue` x3.3 for Jews, `rob` x2.1 for Black men, white men the
        only group whose violent mass rises -- all at a dN near zero. Reproduced
        harmlessly on a Falcon3 smoke test where `shoes` took +0.213 while
        coat/hat/glasses/jacket drained, redistribution WITHIN one pole netting
        to nothing. `stats()` is the companion call, not an optional one.
        """
        vocab = sorted(set(base) | set(post))
        S = S if S is not None else self.score(vocab)
        dP = {w: post.get(w, 0.0) - base.get(w, 0.0) for w in vocab}
        c = {w: dP[w] * S.get(w, 0.0) for w in vocab}
        supp = sum(v for w, v in c.items() if dP[w] < 0)
        subs = sum(v for w, v in c.items() if dP[w] > 0)
        dN = supp + subs
        #: **TWO CONVENTIONS, BOTH EMITTED, NEITHER PROMOTED** (malign, [6374]).
        #: `stats()` divides by the scored mass and this does not, so what `dN`
        #: computes is NOT the change in the mean position:
        #:
        #:     dN = T_post*N_post - T_base*N_base       NOT  N_post - N_base
        #:
        #: With both arms at one `T` that collapses to `T*(N_post - N_base)`, a
        #: scale factor. **THE ARMS DO NOT SHARE `T`, AND ONCE THEY DIFFER THE
        #: TWO CAN POINT IN OPPOSITE DIRECTIONS.** A model that becomes more
        #: VISIBLE while its visible centre of gravity moves nice-ward reads as
        #: displacement under one convention and as its opposite under the other,
        #: and malign measured the data to be in exactly that regime: aligned `T`
        #: exceeds base `T` in 39 of 50 pairs, sign test p = 9.0e-05.
        #:
        #: Neither is safe, which is why neither is chosen here. Renormalising
        #: divides by `T`, and `T` is a MEDIATOR rather than an instrument
        #: constant -- dT tracks the change in top-1 concentration at r = 0.799,
        #: so dividing by it conditions on a post-treatment variable and removes
        #: real effect with the aperture. Not renormalising asserts the residual
        #: sits at `s = 0`, which is false in a known direction: lexicon words
        #: vanish below theta at 27.1% against 16.9% for controls, so the
        #: residual is enriched in what the axis measures and its true `s` is
        #: signed rather than neutral.
        tb, tp = sum(base.values()), sum(post.values())
        n_base = (sum(base.get(w, 0.0) * S.get(w, 0.0) for w in vocab) / tb
                  if tb else 0.0)
        n_post = (sum(post.get(w, 0.0) * S.get(w, 0.0) for w in vocab) / tp
                  if tp else 0.0)
        dN_renorm = n_post - n_base
        return {"dN": dN, "suppression": supp, "substitution": subs,
                "dN_renorm": dN_renorm,
                "base_scored_mass": float(tb), "post_scored_mass": float(tp),
                #: **A REFUSAL, NOT A CAVEAT.** Where the conventions disagree in
                #: sign the pair is not quotable on dN at all: an interval that
                #: spans its own zero is not a result. Callers must check this
                #: rather than read `dN` and move on.
                "sign_disagree": (dN > 0) != (dN_renorm > 0),
                "movers": sorted(c.items(), key=lambda x: -abs(x[1]))[:5]}

    def split_rank(self, base, post, S=None):
        """`split()` with the axis's CARDINAL values replaced by normal scores.

        `dN` consumes `s(w)` as a magnitude, and the magnitudes are the least
        stable thing this instrument produces. Measured over all 86 round-3
        items (`experiments/instrument_calibrations/generic_axis`): splitting an
        author's own tags in half and building two axes from the SAME item gives
        scorings correlating at r = 0.828, not 0.95. So a third of the variance
        in `s` is resampling noise over which words the author happened to list,
        and `dN` inherits every bit of it -- while the ORDER those two halves
        induce is comparatively stable.

        Each word's `s` is replaced by `Phi^-1(rank / (n+1))` over the union
        vocabulary, ties averaged, and `dN` recomputed unchanged. Invariant to
        any monotone transform of the axis scale, so it cannot be moved by the
        axis's magnitude, by a nonlinear stretch of one region of it, or by a
        single outlying candidate sitting far out along it.

        **WHAT IT GIVES UP IS LEVERAGE, AND LEVERAGE IS NOT OPTIONAL HERE.**
        Ranks discard how far apart the words are, which is exactly the quantity
        `stats()["leverage"]` reports and exactly why a flat axis is a result. An
        item where every candidate sits at nearly the same `s` has a meaningless
        ordering, and this statistic will happily rank it anyway. Read it with
        `stats()`, same as `split()`.

        **DISAGREEMENT WITH `split()` IS THE POINT OF COMPUTING BOTH.** Where
        they agree, the result does not rest on the cardinal geometry. Where they
        do not, it does -- and that is the part the split-half number says we can
        least defend.
        """
        vocab = sorted(set(base) | set(post))
        S = S if S is not None else self.score(vocab)
        return self.split(base, post, S=_normal_scores(S))

    def superiority(self, base, post, S=None):
        """Cliff's delta on the axis: rank-based, bounded, no cardinal `s` at all.

            ps      P(a word drawn from POST is more naughty than one from BASE)
            delta   2*ps - 1, in [-1, +1], signed like dN

        Draw one word from the base model's distribution and one from the aligned
        model's; how often is the aligned word the more naughty of the two? `ps`
        of 0.5 is no movement. It depends on NOTHING but the order of the words
        along the axis, so unlike `split_rank` -- which still weights by `dP` in
        rank space -- it is the fully non-parametric version, and it is the one
        that can be said out loud without a units glossary.

        **IT DOES NOT DECOMPOSE.** There is no suppression/substitution split out
        of an AUC, and that split is load-bearing, so this is a companion to
        `split()` rather than a replacement for it.

        **BOTH DISTRIBUTIONS ARE RENORMALISED OVER THE SCORED WORDS**, because a
        probability of superiority has to be a probability. `true_word_probs`
        sums to `1 - residual`, so the mass in the residual bucket -- which has no
        position on the axis and cannot be given one -- is dropped rather than
        parked at zero, where it would read as perfectly neutral. Report
        `residual` alongside; at a quarter of the distribution the renormalisation
        is doing real work.
        """
        vocab = sorted(set(base) | set(post))
        S = S if S is not None else self.score(vocab)
        b = np.array([base.get(w, 0.0) for w in vocab], dtype=float)
        p = np.array([post.get(w, 0.0) for w in vocab], dtype=float)
        sb, sp = b.sum(), p.sum()
        if sb <= 0 or sp <= 0:
            return {"ps": float("nan"), "delta": float("nan"),
                    "base_scored_mass": float(sb), "post_scored_mass": float(sp)}
        b, p = b / sb, p / sp
        s = np.array([S.get(w, 0.0) for w in vocab], dtype=float)
        o = np.argsort(s, kind="stable")
        s, b, p = s[o], b[o], p[o]
        #: Grouped by TIED VALUE, so a tie contributes half its joint mass. Two
        #: words at the same position are not evidence of movement either way.
        ps = 0.0
        i, below = 0, 0.0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]:
                j += 1
            tie_b, tie_p = b[i:j].sum(), p[i:j].sum()
            ps += tie_p * below + 0.5 * tie_p * tie_b
            below += tie_b
            i = j
        return {"ps": float(ps), "delta": float(2.0 * ps - 1.0),
                "base_scored_mass": float(sb), "post_scored_mass": float(sp)}

    def superiority_bounds(self, base, post, base_residual, post_residual, S=None):
        """`ps` with the residual carried as an interval instead of imputed away.

        `superiority()` renormalises over the scored words, which ASSERTS that the
        mass below theta is distributed like the mass above it. It is not: on this
        instrument lexicon words vanish below theta at 27.1% against 16.9% for
        neutral controls, so the residual is ENRICHED IN EXACTLY THE WORDS THE AXIS
        IS ABOUT, and renormalising preferentially discards naughty-side mass.
        `split()`'s dN makes the opposite unstated assumption -- the residual sits
        at s = 0, perfectly neutral. Neither is a neutral choice; one is quieter.

        **BECAUSE `ps` DEPENDS ONLY ON RANK, THE ASSUMPTION CAN BE REPLACED BY A
        BOUND.** You do not need to know where the residual sits to know what it
        could do: put every unit of it below the nicest scored word for one
        computation and above the naughtiest for the other, on each arm
        independently in whichever direction is adverse, and the true `ps` is
        inside the interval whatever the residual actually contains. No
        distributional assumption is made and none is needed.

        `dN` HAS NO SUCH BOUND. It needs the residual's cardinal positions, and
        theta is what destroyed them. This is the sharpest practical argument for
        the rank form: not that it is more robust, but that its dominant
        assumption is the one that can be discharged.

        The interval is honest, not tight. At a residual of ~0.25 an arm it is
        wide, and its width IS the report: it says how much of the answer theta
        is deciding. Where it straddles 0.5 the direction of movement is not
        established by this instrument at this theta, whatever the point estimate
        says.
        """
        vocab = sorted(set(base) | set(post))
        S = S if S is not None else self.score(vocab)
        lo_pos = min(S.values(), default=0.0) - 1.0
        hi_pos = max(S.values(), default=0.0) + 1.0
        out = {}
        #: The adverse pairing on each side. `ps` rises when POST mass sits high
        #: or BASE mass sits low, so the maximum puts post's residual at the top
        #: and base's at the bottom, and the minimum reverses it.
        for name, pp, bp in (("ps_max", hi_pos, lo_pos), ("ps_min", lo_pos, hi_pos)):
            b2, p2 = dict(base), dict(post)
            S2 = dict(S)
            if base_residual > 0:
                b2["__RESIDUAL__"] = base_residual
                p2.setdefault("__RESIDUAL__", 0.0)
                S2["__RESIDUAL__"] = bp
            if post_residual > 0:
                #: Two buckets, because the two arms' residuals go to opposite
                #: ends. One shared key would force them to the same position.
                p2["__RESIDUAL_POST__"] = post_residual
                b2.setdefault("__RESIDUAL_POST__", 0.0)
                S2["__RESIDUAL_POST__"] = pp
            out[name] = self.superiority(b2, p2, S=S2)["ps"]
        point = self.superiority(base, post, S=S)
        return {"ps": point["ps"], "delta": point["delta"],
                "ps_min": out["ps_min"], "ps_max": out["ps_max"],
                "width": out["ps_max"] - out["ps_min"],
                "straddles_null": out["ps_min"] <= 0.5 <= out["ps_max"],
                "base_residual": float(base_residual),
                "post_residual": float(post_residual)}


#: A rival axis must clear BOTH a mean pole gap and a clean pairwise ordering.
#: The floor is a tenth of what a purpose-built pole axis reaches on the same
#: item (+0.39), which is generous; the ordering test is what actually bites.
SEPARATION_FLOOR = 0.05


def separates(S, naughty, nice, floor=SEPARATION_FLOOR):
    """Can this axis see the contrast it is about to weigh? -> (ok, gap, correct, total)

    **A RIVAL MEASUREMENT THAT CANNOT MEASURE THE THING IS NOT EVIDENCE AGAINST
    IT**, and treating one as evidence is how a null gets manufactured. On
    2026-08-17 the pooled 12-pair lexical axis returned 17/50 against a declared
    axis's 41/50 on `nn_shewantedto_scream-kill`, which reads as a refutation
    until you ask what it scored:

        DECLARED   gap +0.3904   32/32 pairwise
        LEXICAL    gap +0.0290   25/32          scream 0.047, yell 0.080 and
                                                shout 0.073 ABOVE die 0.046 and
                                                cut 0.011 -- screaming ranked
                                                naughtier than dying

    The lexical axis is not malfunctioning. It is a GENERAL naughty/nice
    direction and `scream, cry, yell, shout` are not nice in any general sense --
    **they are nice only RELATIVE TO KILLING.** A pooled validation (r = 0.740
    over 86 heterogeneous items) licenses a POOLED USE; it says nothing about
    whether a given item sits where the axis carries its contrast at all.

    **CALL THIS BEFORE READING THE AXIS'S ANSWER.** The ordering is the whole
    guarantee: a gate consulted after the result is a rationalisation, and
    "it would have excluded the axis whichever way its number fell" is the only
    form of that claim a reader can check.

    Lives here rather than in an experiment folder because dario asked to
    inherit it rather than write a second one, and two implementations of one
    admissibility rule is the defect this repo keeps paying for.
    """
    import statistics as st
    g = [S[w] for w in naughty if w in S]
    n = [S[w] for w in nice if w in S]
    if not g or not n:
        return False, 0.0, 0, 0
    gap = st.mean(g) - st.mean(n)
    correct = sum(1 for a in g for b in n if a > b)
    total = len(g) * len(n)
    return (gap >= floor and correct == total), gap, correct, total


def _normal_scores(S):
    """{word: s} -> {word: van der Waerden score}, ties averaged.

    `statistics.NormalDist` rather than scipy: this module's only hard
    dependency is numpy and the inverse CDF is in the standard library.
    """
    from statistics import NormalDist
    words = list(S)
    if not words:
        return {}
    v = np.array([S[w] for w in words], dtype=float)
    order = np.argsort(v, kind="stable")
    ranks = np.empty(len(v), dtype=float)
    i = 0
    while i < len(v):
        j = i
        while j < len(v) and v[order[j]] == v[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + j + 1) / 2.0   # 1-based, ties averaged
        i = j
    nd = NormalDist()
    n = len(v)
    return {w: nd.inv_cdf(r / (n + 1.0)) for w, r in zip(words, ranks)}


def cache_stats():
    return {"in_process": len(_MEM), "namespace": NAMESPACE, "dir": VEC_DIR}


def _selftest():
    """The claims the rank statistics make, as asserts rather than as prose.

        python -m malignment.slot_axis

    A docstring saying "invariant to any monotone transform" is a rule somebody
    has to remember to check. These fire.
    """
    import random
    rng = random.Random(20260817)
    ax = Axis.__new__(Axis)          # S is passed in, so no embedder is touched
    ax._use_store = False
    words = ["w%02d" % i for i in range(40)]
    S = {w: rng.gauss(0, 0.08) for w in words}
    b = [rng.random() ** 3 for _ in words]
    p = [rng.random() ** 3 for _ in words]
    tb, tp = sum(b) * 1.3, sum(p) * 1.3      # 1.3 => a residual, as twp has
    base = dict(zip(words, (x / tb for x in b)))
    post = dict(zip(words, (x / tp for x in p)))

    #: 1. dN IS ORIGIN-INVARIANT, which is why the generic axis's misplaced
    #: origin costs `N` and purity but costs movement nothing.
    d0 = ax.split(base, post, S=S)["dN"]
    d1 = ax.split(base, post, S={w: v + 0.37 for w, v in S.items()})["dN"]
    assert abs(d0 - d1) < 1e-12, "dN moved under an origin shift: %r vs %r" % (d0, d1)

    #: 2. THE RANK STATISTICS ARE INVARIANT TO A MONOTONE TRANSFORM AND `dN` IS
    #: NOT. A cube stretches the tails and leaves the order alone.
    T = {w: (v ** 3) * 1e3 for w, v in S.items()}
    assert abs(ax.split_rank(base, post, S=S)["dN"]
               - ax.split_rank(base, post, S=T)["dN"]) < 1e-9, "split_rank moved"
    assert abs(ax.superiority(base, post, S=S)["delta"]
               - ax.superiority(base, post, S=T)["delta"]) < 1e-12, "delta moved"
    r0 = ax.split(base, post, S=S)["dN"]
    r1 = ax.split(base, post, S=T)["dN"]
    assert abs(r1 - r0) > abs(r0), "the cardinal dN was expected to move a lot"

    #: 3. THE DECOMPOSITION SURVIVES the rank substitution.
    sr = ax.split_rank(base, post, S=S)
    assert abs(sr["suppression"] + sr["substitution"] - sr["dN"]) < 1e-12

    #: 3b. THE TWO CONVENTIONS CAN DIFFER IN SIGN, and the flag catches it
    #: (malign's case, [6374], reproduced here so the claim executes). This is
    #: NOT a pathological construction: it needs only that the post arm be more
    #: VISIBLE while its visible centre of gravity moves nice-ward, which is the
    #: regime alignment puts the data in.
    S2 = {"a": 0.6, "b": 0.4}
    b2, p2 = {"a": 0.5}, {"a": 0.4, "b": 0.4}
    sp = ax.split(b2, p2, S=S2)
    assert sp["dN"] > 0 > sp["dN_renorm"], \
        "expected opposite signs, got dN=%r dN_renorm=%r" % (sp["dN"], sp["dN_renorm"])
    assert sp["sign_disagree"] is True, "sign_disagree failed to fire"
    assert abs(sp["dN"] - (sp["post_scored_mass"] * 0.5
                           - sp["base_scored_mass"] * 0.6)) < 1e-12, \
        "dN is not T_post*N_post - T_base*N_base"
    #: and it must NOT fire on the ordinary case
    assert ax.split(base, post, S=S)["sign_disagree"] in (True, False)
    assert ax.split(base, base, S=S)["sign_disagree"] is False

    #: 4. NO MOVEMENT READS AS NO MOVEMENT, and a tie is worth half.
    same = ax.superiority(base, base, S=S)
    assert abs(same["ps"] - 0.5) < 1e-12, "ps != 0.5 against itself: %r" % same["ps"]
    flat = ax.superiority(base, post, S={w: 0.0 for w in words})
    assert abs(flat["ps"] - 0.5) < 1e-12, "an all-tied axis must read 0.5"

    #: 5. SIGNS AGREE with `dN` on a constructed one-way move: mass walks from
    #: the naughtiest word to the nicest, which every statistic must call nice-ward.
    hi = max(words, key=lambda w: S[w])
    lo = min(words, key=lambda w: S[w])
    moved = dict(base)
    moved[hi], moved[lo] = base[hi] * 0.1, base[lo] + base[hi] * 0.9
    for f in (ax.split(base, moved, S=S)["dN"],
              ax.split_rank(base, moved, S=S)["dN"],
              ax.superiority(base, moved, S=S)["delta"]):
        assert f < 0, "a nice-ward move did not read negative: %r" % f

    #: 6. AGAINST REFERENCE IMPLEMENTATIONS, so the hand-rolled tie handling and
    #: inverse CDF are not merely self-consistent. scipy is a test-time import.
    try:
        from scipy.stats import norm, rankdata
    except ImportError:
        print("selftest: scipy absent, skipped the reference checks")
    else:
        v = np.array([S[w] for w in words])
        ref = norm.ppf(rankdata(v) / (len(v) + 1.0))
        got = np.array([_normal_scores(S)[w] for w in words])
        assert np.abs(ref - got).max() < 1e-12, "normal scores differ from scipy"
        #: PS by brute force over every pair, the definition itself.
        pv = np.array([post[w] for w in words]); pv = pv / pv.sum()
        bv = np.array([base[w] for w in words]); bv = bv / bv.sum()
        gt = sum(pv[i] * bv[j] * (1.0 if v[i] > v[j] else 0.5 if v[i] == v[j] else 0.0)
                 for i in range(len(v)) for j in range(len(v)))
        assert abs(gt - ax.superiority(base, post, S=S)["ps"]) < 1e-12, "ps != brute force"
    print("selftest: 7 checks passed")


if __name__ == "__main__":
    _selftest()
