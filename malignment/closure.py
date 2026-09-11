"""Line closure: p(the line ends here | context + " " + w), per candidate word.

`plan_rhyme.md`'s decomposition, 2026-08-13, which is RH's own objection turned
into a design: *a non-rhyming slot distribution may mean the model does not know
THE LINE ENDS THERE (a metrical failure), not that it cannot rhyme.* Measuring
closure separately splits one instrument into two capacities:

    line_closure         = sum p(w).c(w) / sum p(w)                 METER
    rhyme_given_closure  = sum_{w in class} p(w).c(w) / sum p(w).c(w)  RHYME

**THIS MODULE STORES THE PRIMITIVE `c(w)`, NOT EITHER RATIO**, and that is the
whole point of it existing. Both prior implementations computed `c(w)` per word
and threw it away, keeping a ratio:

    rhyme_pull_pilot.parquet        96 x 14   per model/poem, ratios only
    verse_fleet_smoke.parquet       27 x 14   per poem/slot, close_given_class
    verse_fleet_smoke_words.parquet 2082 x 4  NO closure column at all
    the 250-file verse fleet        nothing -- the rider never ran ([6062])

A stored ratio bakes in the RIME CLASS, so producing it needs the class
vocabulary wherever the model runs. `c(w)` does not, which is what lets a cloud
box do no phonology at all (RH, 2026-09-11: *"Let's not run prosodic on the
cloud... We can do the prosodic analysis after we have the data"*). It also
survives a rime-key revision, and there has already been one: v1 fell back to
syllable SPELLING and shattered /ei/ into 'ay' / 'ey' / 'eigh'. Any ratio
computed under v1 was unrecoverable without re-running the model.

Derivation runs one way only: `line_closure`, `rhyme_given_closure` and
`close_given_class` all follow from (rows, closure.words, manifest). None of
them recovers the others.

## THE RIDER IS TOP-K BY MASS, AND K=40

Selecting the top-K *class members* (`verse_fleet_producer`'s `N_RIDER_CLASS=8`)
would need the rime classes at measurement time, and yields only the
class-internal ratio. Top-K BY MASS needs no phonology and supports both
statistics. Measured cost, 12 real verse slots, SmolLM2-360M / MPS:

    K=9   expand 0.661s  rider 0.060s  +9%     class-internal ratio only
    K=40  expand 0.581s  rider 0.159s  +27%    THE DECOMPOSITION
    K=80  expand 0.583s  rider 0.256s  +44%

The beam is only 2-6 forward passes at these context lengths, which is why a
rider that looks like 2-3x is 27%: one more batched forward beside a shallow
beam, not K sequential ones.
"""
import os

#: the pilot's own TOP_K. See the cost table above.
K_RIDER = int(os.environ.get("MALIGNMENT_CLOSURE_K") or 40)

#: A rider word longer than this in tokens is dropped rather than truncated --
#: a truncated word is a different word and its closure is a different quantity.
MAX_WORD_TOKENS = 6


def newline_ids(tok, n):
    """Token ids that END A LINE: the newline family plus EOS.

    `Ċ` is the byte-level BPE spelling of `\\n`, `<0x0A>` its sentencepiece
    byte-fallback spelling, and a literal leading `\\n` covers the rest. EOS is
    included because a model that ends the TEXT has also ended the line.
    """
    ids = set()
    for i, t in enumerate(tok.convert_ids_to_tokens(list(range(min(n, len(tok)))))):
        if t and ("Ċ" in t or t.startswith("\n") or t == "<0x0A>"):
            ids.add(i)
    if tok.eos_token_id is not None:
        ids.add(tok.eos_token_id)
    return sorted(ids)


def p_close(model, tok, dev, context, words, nl_ids):
    """-> {word: p(newline family | context + " " + word)}.

    ONE padded batch of full sequences, no cache assumed -- malign [5737]: twp
    never caches, so the rider shares the honest price. Words whose tokenisation
    exceeds `MAX_WORD_TOKENS` are omitted from the result rather than scored
    short, so a caller can tell a dropped word from a word scored at zero.
    """
    import torch
    ctx = tok(context, return_tensors="pt")["input_ids"][0].tolist()
    rows = []
    for w in words:
        wid = tok(" " + w, add_special_tokens=False)["input_ids"]
        if 0 < len(wid) <= MAX_WORD_TOKENS:
            rows.append((w, ctx + wid))
    if not rows:
        return {}
    mx = max(len(i) for _, i in rows)
    pad = tok.eos_token_id or 0
    batch = torch.full((len(rows), mx), pad, dtype=torch.long)
    att = torch.zeros((len(rows), mx), dtype=torch.long)
    for i, (_, ids) in enumerate(rows):
        batch[i, :len(ids)] = torch.tensor(ids)
        att[i, :len(ids)] = 1
    with torch.no_grad():
        lg = model(input_ids=batch.to(dev), attention_mask=att.to(dev)).logits.float()
    nl = torch.tensor(nl_ids, device=lg.device)
    return {w: float(torch.softmax(lg[i, len(ids) - 1, :], -1)[nl].sum())
            for i, (w, ids) in enumerate(rows)}


def rider(model, tok, dev, context, surface_mass, nl_ids, k=None):
    """The payload for one cell: top-`k` surfaces BY MASS, scored for closure.

    `surface_mass` is {surface: p}, already folded across first tokens -- expand
    keys are (surface, first_token) and one word is reachable by several, which
    is RH's catch and is summed by the caller before ranking.
    """
    k = K_RIDER if k is None else k
    top = [w for w, _ in sorted(surface_mass.items(), key=lambda kv: -kv[1])[:k]]
    got = p_close(model, tok, dev, context, top, nl_ids)
    return {"k": k, "nl_ids": len(nl_ids), "n_scored": len(got), "words": got}
