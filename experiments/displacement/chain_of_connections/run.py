"""Is `kill -> scream` a short walk through the embedding's own neighbourhoods?

    python -u run.py
    python -u run.py --k 4 --from kill --to scream
    python -u run.py --prompt "She was so furious she wanted to"

Freud: the idea acquires its substitute "by displacement along a chain of
connections which is determined in a particular way" (RSE 14:137). This asks
whether such a chain is visible in the one place a model keeps its associations
as geometry -- the embedding matrix -- and it starts from the observation that
makes the question worth asking.

## THE FALSIFIER, AND IT FIRES THE INTERESTING WAY

If `scream` were simply the nearest thing to `kill`, there would be no chain to
find and no question. It is not. In `Llama-3.1-8B`'s input embeddings,
**` scream` ranks 1,739th of 128,256 tokens by cosine to ` kill`** -- and
`kill`'s actual neighbours are its own inflections (`kills`, `killing`,
`killed`), then `destroy` 0.206 and `murder` 0.183. The substitute the roster
reaches for is not the geometry's nearest word.

## TWO VOCABULARIES, AND THE WAYPOINTS NEED NOT BE SAYABLE (RH)

**A CONNECTION IS NOT AN OUTPUT.** Freud's chain runs through associations,
not through things the subject would utter: the words a displacement passes
by are exactly the ones that never surface. Restricting the graph to the
prompt's candidate set forces every waypoint to be a possible completion,
which is the wrong constraint on a chain and was this file's first mistake.

    --vocab candidates   nodes are words above theta in >=1 of the 100 arms
                         on this prompt. Every waypoint is sayable HERE.
    --vocab words        nodes are every real English word in the tokenizer.
                         Waypoints may be words no arm would ever emit, which
                         is what a chain of connections is allowed to be.

Endpoints are fixed either way; only what may lie between them changes.

## THE CANDIDATE VOCABULARY, AND WHY IT IS NOT THE DEFAULT

Not a dictionary and not the whole tokenizer. The nodes are the words that sit
ABOVE THETA in at least one of the 100 arms on this prompt: 466 of them, of
which 380 are single tokens with a leading space and have a vector at all.

That restriction is what makes a path mean something. A k-NN graph over the
full tokenizer routes `kill -> murder -> assass -> cruc -> kry -> cry` -- three
of those five are BPE fragments, not words, and a chain through them is an
artefact of the segmentation. Every node here is a word some model was
genuinely willing to say at this blank.

## WHAT THIS IS NOT

**A path in this graph is a fact about geometry, not a mechanism.** Nothing
here shows a model traversing anything; the forward pass does not walk a k-NN
graph. It says that a chain of short associative steps exists between the two
words within the model's own candidate space, which is the weaker claim Freud's
sentence actually licenses and the only one this instrument can support.
"""
import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import embed  # noqa: E402

FIG2 = "She was so angry she wanted to"


def lexicon(name="subtlex", min_fpm=0.0, min_zipf=2.0, wordnet=True):
    """-> a membership predicate for "is this a word".

    **SUBTLEX-US IS A WORD LIST; `wordfreq` IS A FREQUENCY MODEL** (RH), and
    for excluding segmentation debris that difference decides it. `wordfreq`
    assigns frequency to any string that occurs, so BPE fragments inherit one
    and clear any floor: `shr` 2.37, `shri` 3.58, `kry` 1.55. SUBTLEX simply
    does not contain them -- 60,384 entries, and `shr`, `shri`, `assass`,
    `cruc` and `kry` are all absent.

    Already in the repo at `lexicons/frequency/subtlex_us.tsv` and wired
    through `fields.SOURCES`; nothing new is downloaded.

    **THE KNOWN RESIDUE IS PROPER NAMES.** `cher` survives at 2.47 fpm because
    Cher appears in film subtitles. A frequency floor would remove it and take
    `perish` (2.59) and `cherish` (4.45) with it, so the floor is left at zero
    and the residue is named instead.

    **BYU/COCA IS NOT AVAILABLE AND SHOULD NOT BE.** `fields.py` records that
    the file was never in the clone -- it lived in two Dropbox paths -- and
    that it is TYPE-level, one lemma and POS per surface, which is the defect
    that retired it from this project.

    ## THE SECOND FILTER, AND WHY IT IS A DICTIONARY AND NOT A FLOOR

    SUBTLEX membership alone leaves fragments that occur in subtitles as typos
    and truncations: `sho` 0.961, `shou` 0.137, `kil` 0.059, `sla` 0.039, and
    the bge path ran `kill -> shoot -> sho -> shou -> scream`, i.e. through two
    spellings of the word it starts from.

    **A FREQUENCY FLOOR CANNOT REMOVE THEM.** Measured at `--min-fpm 1.0`: the
    floor takes `sho` (0.961 is below it) but also takes `strangle`, `weep`,
    `shriek`, `gouge`, `pummel`, `wail`, `thrash` and `smite` -- the exact
    vocabulary this corpus displaces into. Rare real verbs and common fragments
    occupy the same frequency band, so no floor separates them.

    A dictionary does. WordNet has an entry for every one of those verbs and
    for none of the fragments, and the test is orthogonal to frequency. On this
    prompt's candidate set it removes 31 of 372: 22 fragments (`bl`, `kil`,
    `sho`, `shou`, `sla`, `thro`, `wr`, ...) and 9 closed-class words WordNet
    does not cover (`the`, `to`, `him`, `her`, `what`, `something`, ...). It
    removes no content word.

    **THE RESIDUE IS CHEMICAL SYMBOLS**: `pu`, `sm`, `sn` survive as plutonium,
    samarium and tin. Real dictionary entries, so the dictionary keeps them;
    they are named rather than special-cased, on the same logic as `cher`.
    """
    if name == "subtlex":
        import csv as _csv
        from malignment import fields as F
        path, ok = F.sources()["subtlex_us"]
        if not ok:
            raise SystemExit("missing %s" % path)
        with open(path, encoding="utf-8") as fh:
            tab = {r["word"].lower(): float(r["fpm"])
                   for r in _csv.DictReader(fh, delimiter="\t")}
        base = lambda w: tab.get(w, -1.0) >= min_fpm  # noqa: E731
        n = len(tab)
    else:
        from wordfreq import zipf_frequency
        base = lambda w: zipf_frequency(w, "en") >= min_zipf  # noqa: E731
        n = None
    if not wordnet:
        return base, n
    from nltk.corpus import wordnet as wn
    wn.synsets("seed")  # force the lazy loader outside the lambda
    return (lambda w: base(w) and bool(wn.synsets(w))), n


def real_words(tok, name="subtlex", min_fpm=0.0, min_zipf=2.0, wordnet=True):
    """-> {word: token id} for single-token space-prefixed real English words."""
    ok, _n = lexicon(name, min_fpm, min_zipf, wordnet)
    out = {}
    for i in range(len(tok)):
        s = tok.decode([i])
        if len(s) > 2 and s[0] == " " and s[1:].isalpha() and s[1:].islower():
            if ok(s[1:]):
                out[s[1:]] = i
    return out


def candidates(prompt):
    """-> {word: how many of the 100 arms carry it above theta}"""
    from malignment import ch, roster
    eps, _ = roster.endpoints()
    models = sorted(set(eps) | set(eps.values()))
    q = ("SELECT word, uniqExact(model) AS m FROM {db}.twp_words_v4 "
         "WHERE prompt='%s' AND rule_version=4 AND frame='' AND topup=0 "
         "AND model IN (%s) GROUP BY word"
         % (prompt.replace("'", "\\'"),
            ", ".join("'%s'" % m.replace("'", "\\'") for m in models)))
    return {r["word"]: int(r["m"]) for r in ch.query(q, limit_bytes=None)}


def graph(words, ids, W, k):
    """-> (adjacency, similarity matrix, index) over the candidate words."""
    import torch
    M = torch.nn.functional.normalize(W[[ids[w] for w in words]], dim=1)
    S = M @ M.T
    S.fill_diagonal_(-2.0)
    nb = torch.topk(S, k, dim=1).indices
    adj = collections.defaultdict(set)
    for i in range(len(words)):
        for j in nb[i].tolist():
            #: **UNDIRECTED.** "x is among y's k nearest" is not symmetric, and
            #: a directed k-NN graph would make reachability depend on which
            #: word happens to sit in a dense part of the space.
            adj[i].add(j)
            adj[j].add(i)
    return adj, S


def shortest(adj, a, b):
    """-> list of node indices, or None."""
    if a == b:
        return [a]
    prev, q = {a: None}, collections.deque([a])
    while q:
        x = q.popleft()
        for y in adj[x]:
            if y not in prev:
                prev[y] = x
                if y == b:
                    p = [b]
                    while prev[p[-1]] is not None:
                        p.append(prev[p[-1]])
                    return list(reversed(p))
                q.append(y)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=FIG2)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--to", dest="dst", default="scream")
    ap.add_argument("--model", default=embed.MODEL)
    ap.add_argument("--space", default="llama",
                    choices=("llama", "glove", "bge"),
                    help="llama: the model's input embedding table, which is "
                         "about half orthographic. glove: a static semantic "
                         "space with no tokenizer in it. bge: the word IN "
                         "THIS PROMPT, mean-pooled over its own tokens.")
    ap.add_argument("--vocab", default="words",
                    choices=("words", "candidates"),
                    help="words: every real English word in the tokenizer, so "
                         "a waypoint need not be sayable. candidates: only "
                         "words above theta on this prompt.")
    ap.add_argument("--lexicon", default="subtlex",
                    choices=("subtlex", "wordfreq"),
                    help="subtlex: membership in SUBTLEX-US, a word LIST. "
                         "wordfreq: a frequency MODEL, which gives BPE "
                         "fragments a frequency and lets them through.")
    ap.add_argument("--min-fpm", type=float, default=0.0)
    ap.add_argument("--min-zipf", type=float, default=2.0)
    #: **A DICTIONARY, NOT A FLOOR.** See `lexicon.__doc__`: `--min-fpm 1.0`
    #: removes `strangle`, `weep` and `shriek` before it removes `sho`, and
    #: WordNet removes the fragments and no content word. On by default; the
    #: flag exists so the cost of the filter can be measured, not turned off
    #: because it is inconvenient.
    ap.add_argument("--no-wordnet", dest="wordnet", action="store_false",
                    help="do not require a WordNet entry (keeps `kil`, `sho`, "
                         "`shou`, `sla`, `thro`)")
    a = ap.parse_args(argv)

    import torch
    W, tok = embed.matrix(a.model)
    print("PROMPT: %r" % a.prompt)
    if a.vocab == "candidates":
        cand = candidates(a.prompt)
        #: **THE CANDIDATE SET CONTAINS DEBRIS AND IT REACHED THE PATH.** 84 of
        #: the 466 are not words -- 50-odd runs of underscores, `<|im_end|>`,
        #: and the word-boundary rule's fragments `kil`, `sla`, `sho`, `shou`,
        #: `thro`. They are genuine above-theta completions and belong in
        #: `substitution_shape`'s counts, but the bge path ran
        #: `kill -> shoot -> sho -> shou -> scream`, which is a chain through
        #: two pieces of the word it starts from. Same filter as the `words`
        #: vocabulary, applied to the candidates too -- and SUBTLEX alone does
        #: NOT remove them, because they are in it; the WordNet test does.
        _ok, _n = lexicon(a.lexicon, a.min_fpm, a.min_zipf, a.wordnet)
        n_all = len(cand)
        cand = {w: v for w, v in cand.items() if _ok(w.lower())}
        print("  %d of %d candidates are real words (%d dropped: underscore "
              "runs, specials, and word-boundary fragments)%s"
              % (len(cand), n_all, n_all - len(cand),
                 "" if a.wordnet else "  [--no-wordnet: FRAGMENTS KEPT]"))
        if a.space == "bge":
            #: a contextual encoder gives every token a vector, so a
            #: multi-token word is the mean of its pieces and all 466 are
            #: usable -- the single-token rule belongs to the Llama table
            ids, multi = {w: None for w in sorted(cand)}, 0
        else:
            ids, multi = embed.words(tok, sorted(cand))
        print("  vocab=candidates: %d words above theta in at least one of "
              "the 100 arms; %d single-token (%d multi-token, dropped)"
              % (len(cand), len(ids), multi))
    else:
        ids = real_words(tok, a.lexicon, a.min_fpm, a.min_zipf, a.wordnet)
        print("  vocab=words, lexicon=%s%s: %d real English words in the "
              "tokenizer, single token with a leading space"
              % (a.lexicon, "+wordnet" if a.wordnet else "", len(ids)))
    words = sorted(ids)
    if a.space == "bge":
        M, words = embed.bge_in_context(a.prompt, words)
        #: **CENTRING IS NOT COSMETIC HERE.** Every vector is the same eight-
        #: token frame with one word changed, so the frame dominates and RAW
        #: cosines run 0.70-0.97 for everything -- `accordion` 0.715 against
        #: `scream` 0.781. Subtracting the candidate mean removes the shared
        #: component and leaves what the word contributes. It moves `scream`
        #: from rank 230 of 466 to 409, which is the difference between "mid-
        #: pack" and "one of the least similar words in the set".
        W = torch.nn.functional.normalize(M - M.mean(0), dim=1)
        ids = {w: i for i, w in enumerate(words)}
        print("  space=bge: %d candidates embedded in context, mean-centred"
              % len(words))
    elif a.space == "glove":
        #: the SAME word list, restricted to what GloVe carries, so the two
        #: spaces are compared over one vocabulary rather than two
        G, words = embed.glove(words)
        print("  space=glove: %d of those words have a GloVe vector" % len(words))
        Wg = torch.zeros(len(words), G.shape[1])
        Wg[:] = G
        ids = {w: i for i, w in enumerate(words)}
        W = Wg
    pos = {w: i for i, w in enumerate(words)}
    for w in (a.src, a.dst):
        if w not in pos:
            raise SystemExit("%r is not a single-token candidate here" % w)

    #: **THE FALSIFIER HAS TO SPEAK THE SPACE IT IS IN.** This block decoded
    #: row indices with the TOKENIZER, which is right for the Llama table
    #: (rows are token ids) and nonsense for GloVe (rows are positions in a
    #: word list). Under `--space glove` it printed "` kill`'s nearest:
    #: protest 1.000, ils 0.629, psych 0.624" -- a cosine of 1.000 to a
    #: DIFFERENT WORD is the tell, and it was printed with the same authority
    #: as the real thing.
    V = torch.nn.functional.normalize(W, dim=1)
    if a.space in ("glove", "bge"):
        label = lambda r: words[r]
        universe = ("the %d-word GloVe vocabulary" if a.space == "glove"
                    else "the %d in-context candidates") % len(words)
        src_row, dst_row = pos[a.src], pos[a.dst]
    else:
        label = lambda r: tok.decode([r]).strip()
        universe = "the whole %d-token vocabulary" % W.shape[0]
        src_row, dst_row = ids[a.src], ids[a.dst]
    sims_all = V @ V[src_row]
    rank = int((sims_all > sims_all[dst_row]).sum())
    print("\n  THE FALSIFIER: ` %s` ranks %d of %d by cosine to ` %s` over %s, "
          "so it is not simply the nearest word."
          % (a.dst, rank, len(sims_all), a.src, universe))
    top = torch.topk(sims_all, 8)
    print("    ` %s`'s nearest: %s" % (a.src, ", ".join(
        "%s %.3f" % (label(int(r)), float(sc))
        for sc, r in zip(top.values, top.indices))))
    adj, S = graph(words, ids, W, a.k)
    p = shortest(adj, pos[a.src], pos[a.dst])
    print("\n  k=%d, undirected, over the %d candidate words" % (a.k, len(words)))
    if not p:
        print("    NO PATH from %s to %s" % (a.src, a.dst))
    else:
        print("    %s" % " -> ".join(words[i] for i in p))
        print("    %d hops; steps: %s"
              % (len(p) - 1, ", ".join(
                  "%.3f" % float(S[p[i], p[i + 1]]) for i in range(len(p) - 1))))

    #: **THE NULL: IS THAT SHORT?** A four-hop path in a small-world graph may
    #: be unremarkable, so the distance is read against every other candidate
    #: word rather than admired on its own.
    d = {pos[a.src]: 0}
    q = collections.deque([pos[a.src]])
    while q:
        x = q.popleft()
        for y in adj[x]:
            if y not in d:
                d[y] = d[x] + 1
                q.append(y)
    hist = collections.Counter(d.values())
    reach = len(d)
    print("\n  DISTANCE FROM %s TO EVERY OTHER CANDIDATE (%d of %d reachable)"
          % (a.src, reach, len(words)))
    for h in sorted(hist):
        print("    %d hops  %4d words%s" % (h, hist[h],
              "   <- %s" % a.dst if h == (len(p) - 1 if p else -1) else ""))
    med = sorted(d.values())[len(d) // 2]
    print("    median distance %d; %s is at %s"
          % (med, a.dst, len(p) - 1 if p else "unreachable"))
    print("    SO THE PATH IS %s"
          % ("NOT SHORT: it is the typical distance in this graph"
             if p and len(p) - 1 == med else
             "NOT SHORT: it is LONGER than typical" if p and len(p) - 1 > med
             else "shorter than typical" if p else "absent"))

    #: **THE CONTROL THAT DECIDES IT.** A readable chain is not evidence:
    #: in a small-world k-NN graph EVERY pair has one, and it will look like
    #: an association because the steps are near-neighbours by construction.
    #: So the same path is drawn to words chosen to have nothing to do with
    #: the prompt. If they read as well as the real one, the real one is a
    #: property of the graph.
    print("\n  CONTROL: the same walk to words with nothing to do with it")
    #: controls must exist IN the vocabulary being walked. On the candidate
    #: set `pension` and `accordion` are not above theta at this blank, so the
    #: control silently printed nothing -- an empty control reads exactly like
    #: a passed one. These are candidates here and are unrelated to killing.
    ctrl = (("sit", "sleep", "read", "dance", "write", "eat")
            if a.vocab == "candidates"
            else ("sofa", "accordion", "pension", "wallpaper", "custard"))
    shown = 0
    for t in ctrl:
        if t not in pos:
            continue
        cp = shortest(adj, pos[a.src], pos[t])
        if cp:
            shown += 1
            print("    %-10s %d hops  %s"
                  % (t, len(cp) - 1, " -> ".join(words[i] for i in cp)))
    if not shown:
        print("    NONE of %s is in this vocabulary -- the control did not "
              "run, which is not the same as passing." % ", ".join(ctrl))

    #: **HOW MUCH OF THIS GRAPH IS SPELLING?** Input embeddings carry
    #: orthography heavily, so a chain through them may be a chain of prefixes
    #: rather than of associations. Emitted rather than asserted, because it
    #: is the number that decides whether the whole approach means anything.
    import random
    rs = random.Random(0)
    samp = rs.sample(range(len(words)), min(400, len(words)))
    import torch as _t
    Ms = _t.nn.functional.normalize(W[[ids[w] for w in words]], dim=1)
    Ss = Ms[samp] @ Ms.T
    Ss[_t.arange(len(samp)), _t.tensor(samp)] = -2.0
    nb3 = _t.topk(Ss, 3, dim=1).indices
    def shared(x, y):
        n = 0
        for c1, c2 in zip(x, y):
            if c1 != c2:
                break
            n += 1
        return n
    hit = sum(1 for r, i in enumerate(samp) for j in nb3[r].tolist()
              if shared(words[i], words[j]) >= 3)
    #: the verdict has to follow the number, not the number the verdict: this
    #: line said "about half a chain of SPELLINGS" unconditionally and would
    #: have said it of GloVe, where the share is 28%
    share = 100.0 * hit / (len(samp) * 3)
    print("\n  ORTHOGRAPHY CHECK: %.0f%% of 3-NN pairs over %d sampled nodes "
          "share a three-letter prefix." % (share, len(samp)))
    print("  %s" % ("About half the edges are spellings rather than "
                    "associations." if share >= 40 else
                    "A substantial minority of edges are spellings." if share >= 20
                    else "Orthography is not driving this graph."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
