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


def real_words(tok, min_zipf=2.0):
    """-> {word: token id} for single-token space-prefixed real English words.

    `wordfreq`'s zipf frequency is the membership test this repo already uses
    (`norm_change/fig3_candidates.real_word`). A floor above zero is applied
    because the tokenizer is full of things with a nonzero frequency and no
    business in a chain -- and because the FIRST version of this graph, built
    on "lowercase and alphabetic" alone, routed `kill -> murder -> assass ->
    cruc -> kry -> cry`, where three of the five waypoints are BPE fragments.
    A chain through segmentation debris is an artefact, not an association.
    """
    from wordfreq import zipf_frequency
    out = {}
    for i in range(len(tok)):
        s = tok.decode([i])
        if len(s) > 2 and s[0] == " " and s[1:].isalpha() and s[1:].islower():
            if zipf_frequency(s[1:], "en") >= min_zipf:
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
    ap.add_argument("--vocab", default="words",
                    choices=("words", "candidates"),
                    help="words: every real English word in the tokenizer, so "
                         "a waypoint need not be sayable. candidates: only "
                         "words above theta on this prompt.")
    ap.add_argument("--min-zipf", type=float, default=2.0)
    a = ap.parse_args(argv)

    import torch
    W, tok = embed.matrix(a.model)
    print("PROMPT: %r" % a.prompt)
    if a.vocab == "candidates":
        cand = candidates(a.prompt)
        ids, multi = embed.words(tok, sorted(cand))
        print("  vocab=candidates: %d words above theta in at least one of "
              "the 100 arms; %d single-token (%d multi-token, dropped)"
              % (len(cand), len(ids), multi))
    else:
        ids = real_words(tok, a.min_zipf)
        print("  vocab=words: %d real English words in the tokenizer at "
              "zipf >= %.1f, single token with a leading space"
              % (len(ids), a.min_zipf))
    words = sorted(ids)
    pos = {w: i for i, w in enumerate(words)}
    for w in (a.src, a.dst):
        if w not in pos:
            raise SystemExit("%r is not a single-token candidate here" % w)

    V = torch.nn.functional.normalize(W, dim=1)
    sims_all = V @ V[ids[a.src]]
    rank = int((sims_all > sims_all[ids[a.dst]]).sum())
    print("\n  THE FALSIFIER: ` %s` ranks %d of %d by cosine to ` %s` over the "
          "WHOLE tokenizer, so it is not simply the nearest word."
          % (a.dst, rank, W.shape[0], a.src))
    top = torch.topk(sims_all, 8)
    print("    ` %s`'s nearest: %s" % (a.src, ", ".join(
        "%s %.3f" % (tok.decode([int(i)]).strip(), float(s))
        for s, i in zip(top.values, top.indices))))

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
    print("\n  ORTHOGRAPHY CHECK: %.0f%% of 3-NN pairs over %d sampled nodes "
          "share a three-letter prefix.\n  A chain through this graph is "
          "about half a chain of SPELLINGS." % (100.0 * hit / (len(samp) * 3),
                                                len(samp)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
