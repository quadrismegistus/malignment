"""Lift the vocabulary from the 307 above-theta candidates to every infinitive.

    python wide_vocab.py                  compute the residual, then the tree
    python wide_vocab.py --reuse          skip the model, read the saved npz

## THE LIMITATION THIS TESTS (RH)

Every chain in this folder was routed through the **307 words that clear theta
on this prompt**. That is a small island, and a corridor found on it may be an
artefact of what was allowed in rather than a fact about the model. The
vocabulary here is instead every INFINITIVE in the model's own vocabulary --
any word that could fill this slot -- which is 11x larger.

## WHY NOT `get_pos`

RH proposed tagging all 16,705 real single-token words with `pos.get_pos` at
this slot. Run: it tags **12,099 of them VERB, 72%**, including `abdomen`,
`abortion`, `absence`, `abrasive` and `aboard`. After "wanted to" the parser
EXPECTS a verb and assigns VERB to whatever follows, so at a slot with a strong
syntactic expectation contextual POS reports the EXPECTATION, not the word. It
is the right instrument for "what role does this word play here" and the wrong
one for "is this a verb".

WordNet's verb sense has the opposite flaw: its 7,965 include `absorbs`,
`accuses`, `achieves`, `acts` -- real verbs, but inflected, and "wanted to
absorbs" is not English.

**The test that works is lexical AND morphological**: a WordNet verb sense, and
already the base form under `morphy`. 3,312 words.

## AND THE UNION IS NOT OPTIONAL

47 of the current 307 candidates FAIL that test -- `avenge`, `fling`, `gouge`,
`howl`, `injure`, `lunge`, `pounce`, `puke`, `pummel`, `retaliate`, `cuss`,
`lynch`. WordNet simply has no verb sense for them, and they are precisely this
corpus's displacement vocabulary. So the vocabulary is the union, 3,359 words:
dropping them would remove words the corridor already runs through, and would
do it silently.

The residue is left in. `cheek`, `cheese`, `cheque` and `choir` have verb
senses and are not plausible here; they sit in the graph unused unless
something routes through them. **Hand-pruning a vocabulary toward the answer
you expect is how a corridor gets manufactured**, which is the failure this
file exists to test for.
"""
import argparse, collections, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(HERE) + "/substitution_shape")
sys.path.insert(0, HERE)
import embed  # noqa: E402
import pathways  # noqa: E402
import run as cc  # noqa: E402
import threshold  # noqa: E402

MODEL = "meta-llama/Llama-3.1-8B"


def mst_prim(W, words, src):
    """-> ({word: (bottleneck, hops)}, adjacency) by PRIM, for a dense graph.

    **KRUSKAL CANNOT DO 16,705 WORDS.** It needs every pair sorted: 139 million
    edges, and `triu_indices` alone is two int64 arrays of that length before
    any sorting. Prim on a dense similarity matrix is O(n^2) with no edge list
    at all -- one 16,705-wide row at a time -- and gives the same maximum
    spanning tree, so the bottleneck (the minimum edge on the tree path) is
    unchanged. The Kruskal path is kept for the small vocabularies so the two
    can be checked against each other.
    """
    import collections
    import numpy as np
    n = len(words)
    pos = {w: i for i, w in enumerate(words)}
    s = pos[src]
    best = np.full(n, -np.inf, dtype=np.float32)
    par = np.full(n, -1, dtype=np.int64)
    seen = np.zeros(n, dtype=bool)
    best[s] = np.inf
    adj = collections.defaultdict(list)
    for _ in range(n):
        u = int(np.argmax(np.where(seen, -np.inf, best)))
        if not np.isfinite(best[u]) and best[u] == -np.inf:
            break
        seen[u] = True
        if par[u] >= 0:
            v = float(W[u] @ W[par[u]])
            adj[int(par[u])].append((u, v))
            adj[u].append((int(par[u]), v))
        row = (W @ W[u]).numpy()
        row[seen] = -np.inf
        upd = row > best
        best = np.where(upd, row, best)
        par = np.where(upd, u, par)
    out = {src: (float("inf"), 0)}
    q = collections.deque([s])
    while q:
        x = q.popleft()
        bx, hx = out[words[x]]
        for y, v in adj[x]:
            if words[y] not in out:
                out[words[y]] = (min(bx, v), hx + 1)
                q.append(y)
    return out, adj, pos


def base_forms(words):
    """-> the subset that is not another inflection of a word already present.

    **THE MORPHOLOGICAL SHORTCUT IS NOT A CONNECTION.** With every real word
    admitted, the corridor ran `kill -> killed -> kills -> hurts -> hits ->
    beats -> beat`, and `kill`'s nearest neighbours were `murder`, `killed`,
    `killing`, `hurt`, `murdered`, `murdering`, `kills`. Four of the first
    eight are inflections of the query word. Those are not steps between
    IDEAS; they are one idea in four forms, and they let a route cross the
    space without associating anything.

    The fix is not to require infinitives -- that would restrict intermediates
    to words that could actually be uttered here, which is the constraint RH
    rejected on the grounds that a chain's connections need not be its output.
    It is to keep ONE FORM PER LEMMA: every real word, deduplicated by
    inflection, with the base form preferred.

    A word is dropped when WordNet can reduce it to a different word that is
    itself in the vocabulary. `killed -> kill` goes; `kill` stays; `batter`
    and `perish`, which reduce to themselves, stay.
    """
    from nltk.corpus import wordnet as wn
    have = set(words)
    out = []
    for w in words:
        lemmas = {wn.morphy(w, p) for p in (wn.VERB, wn.NOUN, wn.ADJ, wn.ADV)}
        lemmas.discard(None)
        lemmas.discard(w)
        if any(l in have for l in lemmas):
            continue
        out.append(w)
    return out


def vocabulary(prompt, mode="infinitive"):
    """-> sorted vocabulary. `all` = every non-fragment word, no verb test.

    **`all` IS THE HONEST DEFAULT AND `infinitive` IS A JUDGEMENT.** My
    infinitive test was wrong in both directions -- it dropped `avenge`,
    `gouge`, `lunge`, `pummel` and `lynch` for want of a WordNet verb sense,
    and it kept `cheek`, `cheese`, `cheque` and `choir` for having one. RH's
    instruction is to stop deciding: take every real non-fragment word and let
    the geometry place it. A word that cannot fill this slot will simply not be
    near anything on a route, which is a fact the graph can report rather than
    one the vocabulary asserts in advance.
    """
    from malignment import fields as F
    from nltk.corpus import wordnet as wn
    _W, tok = embed.matrix(embed.MODEL)
    path, ok = F.sources()["subtlex_us"]
    if not ok:
        raise SystemExit("missing %s" % path)
    sub = {r["word"].lower() for r in
           csv.DictReader(open(path, encoding="utf-8"), delimiter="\t")}
    keep = set()
    for i in range(len(tok)):
        s = tok.decode([i])
        if s[:1] == " " and s[1:].isalpha() and s[1:].islower() and len(s) > 3:
            w = s[1:]
            if w not in sub or not wn.synsets(w):
                continue
            if mode in ("all", "lemma") or (wn.synsets(w, pos=wn.VERB)
                                            and wn.morphy(w, wn.VERB) == w):
                keep.add(w)
    cand, _why = cc.candidate_words(prompt)
    words = sorted(keep | set(cand))
    if mode == "lemma":
        n0 = len(words)
        words = base_forms(words)
        print("  lemma dedup: %d -> %d (%d inflections removed)"
              % (n0, len(words), n0 - len(words)))
    return words, len(keep), len(cand)


def residual(prompt, words, device="mps", batch=24):
    """-> [len(words), dim] mean-over-layers residual at each word's position."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    spans = {w: tok.encode(" " + w, add_special_tokens=False) for w in words}
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, dtype=torch.float16, low_cpu_mem_usage=True).to(device).eval()
    p_ids = tok.encode(prompt, add_special_tokens=True)
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    out = []
    for s in range(0, len(words), batch):
        chunk = words[s:s + batch]
        seqs = [p_ids + spans[w] for w in chunk]
        L = max(len(x) for x in seqs)
        ids = torch.tensor([[pad] * (L - len(x)) + x for x in seqs], device=device)
        att = torch.tensor([[0] * (L - len(x)) + [1] * len(x) for x in seqs],
                           device=device)
        with torch.no_grad():
            h = model(ids, attention_mask=att, output_hidden_states=True).hidden_states
        nl = len(h) - 1
        for j, w in enumerate(chunk):
            k = len(spans[w])
            out.append(torch.stack([h[l][j, -k:].mean(0) for l in range(1, nl + 1)])
                       .mean(0).detach().float().cpu())
        if (s // batch) % 20 == 0:
            print("    %d/%d" % (s, len(words)), flush=True)
    del model
    if device == "mps":
        torch.mps.empty_cache()
    return torch.stack(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=cc.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--basis", default="faller")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--batch", type=int, default=24)
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--vocab", default="lemma",
                    choices=("all", "infinitive", "lemma"))
    a = ap.parse_args(argv)
    import numpy as np
    import torch

    res = os.path.join(HERE, "results")
    os.makedirs(res, exist_ok=True)
    npz = os.path.join(res, "wide_vocab_resid_%s.npz" % a.vocab)
    words, n_keep, n_cand = vocabulary(a.prompt, a.vocab)
    print("VOCABULARY %d = %d %s words + %d above-theta candidates (union)"
          % (len(words), n_keep, a.vocab, n_cand))
    allnpz = os.path.join(res, "wide_vocab_resid_all.npz")
    if a.vocab == "lemma" and os.path.exists(allnpz) and not os.path.exists(npz):
        #: the lemma vocabulary is a SUBSET of `all`, so its residual is a
        #: slice of one already computed -- no second pass over the model
        aw = np.load(allnpz, allow_pickle=True)
        have = {str(w): i for i, w in enumerate(aw["words"])}
        miss = [w for w in words if w not in have]
        if miss:
            raise SystemExit("%d lemma words absent from the `all` residual "
                             "(e.g. %s); rerun --vocab all first"
                             % (len(miss), ", ".join(miss[:5])))
        idx = [have[w] for w in words]
        np.savez_compressed(npz, words=np.array(words),
                            resid_mean=aw["resid_mean"][idx])
        print("  sliced %d rows out of the `all` residual -> %s"
              % (len(idx), os.path.basename(npz)))
    if os.path.exists(npz):
        z = np.load(npz, allow_pickle=True)
        words = [str(w) for w in z["words"]]
        M = torch.tensor(z["resid_mean"])
        print("  reusing %s" % npz)
    else:
        print("  %d forward passes through %s" % (len(words), MODEL))
        M = residual(a.prompt, words, a.device, a.batch)
        np.savez_compressed(npz, words=np.array(words), resid_mean=M.numpy())
        print("  wrote %s (%.0f MB)" % (npz, os.path.getsize(npz) / 1e6))

    W = torch.nn.functional.normalize(M - M.mean(0), dim=1)
    if len(words) > 6000:
        print("  %d words: Prim (dense), not Kruskal" % len(words))
        B, adj, pos = mst_prim(W, words, a.src)
    else:
        B, adj, pos = threshold.bottlenecks(W, words, a.src)
    par = {pos[a.src]: None}
    q = collections.deque([pos[a.src]])
    while q:
        x = q.popleft()
        for y, _v in adj[x]:
            if y not in par:
                par[y] = x
                q.append(y)

    def route(w):
        p, x = [], pos[w]
        while x is not None:
            p.append(words[x])
            x = par[x]
        return list(reversed(p))

    dsts, stayed, nb = pathways.targets(a.prompt, a.basis, a.src)
    v = (W @ W[pos[a.src]]).numpy()
    order = sorted(range(len(words)), key=lambda i: -v[i])
    print("\n  %r's nearest: %s" % (a.src, ", ".join(
        "%s %.3f" % (words[i], v[i]) for i in order[1:11])))
    print("\n  %-10s %8s %10s %6s   %s"
          % ("word", "direct", "bottleneck", "hops", "kind"))
    rows = [(w, "destination") for w in dsts] + \
           [(w, "CONTROL") for w in ("eat", "dance", "sit", "write")]
    for w, kind in sorted(rows, key=lambda t: -B.get(t[0], (-9, 0))[0]):
        if w not in B:
            print("  %-10s  not in the vocabulary" % w)
            continue
        bn, hp = B[w]
        print("  %-10s %8.3f %10.3f %6d   %s"
              % (w, v[pos[w]], bn, hp, kind))
    r = route("scream")
    print("\n  route to scream (%d hops, bottleneck %.3f):\n    %s"
          % (len(r) - 1, B["scream"][0], " -> ".join(r)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
