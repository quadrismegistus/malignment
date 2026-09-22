"""The CI figure: the bottleneck corridor folded into two columns at 4.33 in.

    python ci_plate.py --basis faller --min-lineages 2
    python ci_plate.py --all           every basis x cutoff, for comparison

## THE SPEC (RH, via the drafting seat)

CI prints figures at **4.33 in wide and at most ~6.5 in tall**. The corridor is
17 ranks deep and about 1:2.1, so unfolded it would print 3.1 in wide and waste
the measure. It folds without crossings because it is a SPINE with short side
branches: `kill` to `bash` down the left column, `bash` to `scream` down the
right, branches hanging outward from their spine nodes.

    Arial, nothing under 7 pt, black and greys in the 20-80% band only.
    Destinations bold, no fill, count as a small grey numeral AFTER the word --
      "scream 18", not a second line reading "18 of 33" ten times over.
    Waypoints regular, 60% grey, so the eye reads the bold sequence first.
    Width still encodes the link's cosine; no red; the weakest link on the
      route to the heaviest destination carries a small grey number instead.
    No title, no legend, no axis. The caption carries all of it.

## WHY THE LAYOUT IS COMPUTED AND NOT DRAWN BY HAND

The spine and the branch attachment points are read off the actual maximum
spanning tree every run. Hardcoding the fold would mean that if the corridor
ever changed -- a different prompt, stage, or space -- the plate would keep the
old shape and misrepresent the new data while still rendering perfectly. The
structure is asserted, then laid out.

`neato -n2` is used with explicit positions because `dot` cannot be made to
fold a spine, and a fold is the whole point.

## n>=2 NARROWS AND DOES NOT SHORTEN

Measured on all three bases: the cutoff drops the tree from 22-28 nodes to
17-18 and leaves the DEPTH at 17 in every case, because the `scream` corridor
IS the depth and `scream` survives every filter. So the fold is required
whatever the cutoff; the cutoff only buys width.
"""
import argparse, collections, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE) + "/substitution_shape")
sys.path.insert(0, HERE)
import cosines  # noqa: E402
import pathways  # noqa: E402
import threshold  # noqa: E402
import run  # noqa: E402

PT = 72.0
GREY_WAY = "#999999"      # 60% -- waypoints
GREY_EDGE = "#6f757a"
GREY_NUM = "#8a8a8a"


def corridor(prompt, space, stage, basis, cut, src="kill"):
    """-> (routes {dst: [words]}, counts, S, pos, words) -- structure asserted."""
    dsts, stayed, nb = pathways.targets(prompt, basis, src)
    keep = {w: c for w, c in dsts.items() if c >= cut}
    if not keep:
        raise SystemExit("no destination reaches %d lineages on basis=%s" % (cut, basis))
    words, W, ids = cosines.space(space, prompt, stage=stage)
    W = W[[ids[w] for w in words]]
    S = (W @ W.T).numpy()
    B, adj, pos = threshold.bottlenecks(W, words, src)
    par = {pos[src]: None}
    q = collections.deque([pos[src]])
    while q:
        x = q.popleft()
        for y, _v in adj[x]:
            if y not in par:
                par[y] = x
                q.append(y)
    routes = {}
    for w in keep:
        if w not in pos:
            raise SystemExit("%r is not in the %s vocabulary" % (w, space))
        p, x = [], pos[w]
        while x is not None:
            p.append(words[x])
            x = par[x]
        routes[w] = list(reversed(p))
    return routes, keep, S, pos, words, sum(dsts.values())


def label_w(w, counts, fontsize):
    """-> approximate rendered width in inches. Arial averages ~0.55 em."""
    n = len(w) + (len(" %d" % counts[w]) if w in counts else 0)
    return n * fontsize * 0.55 / PT


def layout(routes, counts, width_in, fontsize, gap=0.20, pad=0.10):
    """-> ({word: (x_in, band, sub)}, spine, bands) laid out BOUSTROPHEDON.

    **LEFT TO RIGHT, THEN BACK RIGHT TO LEFT ALONG THE NEXT ROW** (RH). The
    corridor is 17 ranks and the page is landscape-ish, so running it in rows
    uses the measure the vertical fold was wasting. The turn is the reason to
    prefer it: when the direction reverses, the last word of a row sits
    directly above the first word of the next, so the fold is a SHORT VERTICAL
    DROP -- not the diagonal that crossed the two-column plate, and not the
    full-height elbow that read as a divider.

    Rows are packed from MEASURED label widths rather than a fixed count, so a
    row of `disappear` and `explode` holds fewer words than a row of `hit` and
    `cry`, and nothing overhangs the measure.

    Branches run in the same direction as their row, one sub-row below the
    spine, so a branch reads as a parallel strand rather than a descent.
    """
    head = max(counts, key=lambda w: (counts[w], len(routes[w])))
    spine = routes[head]
    on_spine = {w: i for i, w in enumerate(spine)}

    #: **BRANCHES COME FROM THE UNION TREE, NOT FROM PER-DESTINATION ROUTES.**
    #: Taking each route's non-shared tail produced two bugs at once. A
    #: destination that lies ON the spine (`hurt`, `hit`, `cry`, `smash` all
    #: do) yields an EMPTY tail, and `min()` over it raises -- which it did,
    #: silently, because the regeneration had stderr redirected, so the
    #: measurements were of stale files that looked fine. And `punch` and
    #: `slap` both hang off `hit`, so their tails were `[punch]` and
    #: `[punch, slug, slap]`: the same word placed twice.
    #:
    #: The drawn object is one TREE. Build the parent map from the union of
    #: the routes, then every non-spine node has exactly one chain back to a
    #: spine node, and each such chain is drawn once.
    parent = {}
    for r in routes.values():
        for a, b in zip(r, r[1:]):
            parent[b] = a
    chains = {}
    for w in parent:
        if w in on_spine:
            continue
        path, x = [w], w
        while parent[x] not in on_spine:
            x = parent[x]
            path.append(x)
        chains.setdefault(parent[x], []).append(list(reversed(path)))
    #: a spine node with several chains keeps the longest as one run and the
    #: rest as separate runs; each is laid out and collision-checked below
    branches = []
    for anchor, cs in chains.items():
        for c in sorted(cs, key=len, reverse=True):
            if any(set(c) < set(o) for o in cs):
                continue        # this chain is a prefix of another; drawn there
            branches.append((on_spine[anchor], c))

    avail = width_in - 2 * pad

    def fits(rs):
        return all(sum(label_w(w, counts, fontsize) for w in r)
                   + gap * (len(r) - 1) <= avail for r in rs)

    def split(n):
        """spine into n rows as evenly as possible, in order"""
        out, i = [], 0
        for k in range(n):
            take = (len(spine) - i) // (n - k)
            out.append(spine[i:i + take])
            i += take
        return out

    #: **BALANCED, NOT GREEDY.** Greedy packing filled each row to the measure
    #: and left the remainder alone on the last -- 8/8/1, with `scream` as an
    #: orphan row, which reads as a mistake rather than a fold. The smallest
    #: row count that fits is found first, then the words are divided evenly
    #: across exactly that many rows, so 17 goes 6/6/5 rather than 8/8/1.
    n = 1
    while n <= len(spine) and not fits(split(n)):
        n += 1
    rows = split(n)

    #: a branch needs its own horizontal run, so the row that carries it must
    #: be wide enough for the attachment plus the branch; if it is not, the
    #: branch simply runs off its own sub-row and we widen the gap search
    place, row_of = {}, {}
    for bi, rw in enumerate(rows):
        ltr = bi % 2 == 0
        widths = [label_w(w, counts, fontsize) for w in rw]
        total = sum(widths) + gap * (len(rw) - 1)
        #: justify the row across the measure, so short rows do not float
        g = gap if len(rw) < 2 else max(gap, (avail - sum(widths)) / (len(rw) - 1))
        x = pad
        seq = rw if ltr else list(reversed(rw))
        ws = widths if ltr else list(reversed(widths))
        for w, lw in zip(seq, ws):
            place[w] = (x + lw / 2.0, bi, 0)
            row_of[w] = bi
            x += lw + g
    #: branches: same direction as their row, starting one slot along
    #:
    #: **TWO BRANCHES IN ONE ROW WILL OVERPRINT.** `slash..rip` off `bash` and
    #: `crush..destroy` off `smash` both hang under the middle row and their x
    #: spans overlap, which rendered as "desrtipoy" and "crusstcratch" -- two
    #: words drawn on top of each other, perfectly legibly wrong. Each branch
    #: now takes the shallowest sub-row whose occupied spans it misses.
    sub_depth = {bi: 0 for bi in range(len(rows))}
    taken = {}          # (band, sub) -> [(x0, x1), ...]
    for at, tail in branches:
        anchor = spine[at]
        bi = row_of[anchor]
        ltr = bi % 2 == 0
        step = 1 if ltr else -1
        xs, x = [], place[anchor][0]
        for j, w in enumerate(tail):
            lw = label_w(w, counts, fontsize)
            x = x + step * (lw / 2.0 + gap) if j == 0 else x + step * (lw + gap)
            x = min(max(x, pad + lw / 2.0), width_in - pad - lw / 2.0)
            xs.append((w, x, lw))
        span = (min(x - lw / 2.0 for _w, x, lw in xs),
                max(x + lw / 2.0 for _w, x, lw in xs))
        sub = 1
        while any(not (span[1] < a or span[0] > b)
                  for a, b in taken.get((bi, sub), [])):
            sub += 1
        taken.setdefault((bi, sub), []).append(span)
        for w, x, _lw in xs:
            place[w] = (x, bi, sub)
        sub_depth[bi] = max(sub_depth[bi], sub)
    return place, spine, rows, sub_depth, head


def emit(place, spine, rows, sub_depth, routes, counts, S, pos, head, base,
         width_in=4.33, height_in=5.0, fontsize=8.0):
    edges = set()
    for r in routes.values():
        edges.update(zip(r, r[1:]))
    vs = [float(S[pos[a], pos[b]]) for a, b in edges]
    lo, hi = min(vs), max(vs)

    def wid(v):
        t = (v - lo) / (hi - lo) if hi > lo else 0.5
        return 0.45 + 1.75 * t

    #: the marked link is the weakest step on the route to the heaviest
    #: destination -- "the weakest connection on the route most lineages take"
    hr = routes[head]
    mark = min(zip(hr, hr[1:]), key=lambda ab: float(S[pos[ab[0]], pos[ab[1]]]))
    mark_v = float(S[pos[mark[0]], pos[mark[1]]])

    #: band heights: a row with a branch needs a sub-row under it
    sub_h = 0.24
    band = [0.34 + sub_h * sub_depth[b] for b in range(len(rows))]
    top = 0.12
    ytop = {}
    y = top
    for b in range(len(rows)):
        ytop[b] = y
        y += band[b]
    total_h = y - band[-1] + 0.34 + sub_h * sub_depth[len(rows) - 1] + 0.12

    def xy(w):
        x, b, sub = place[w]
        return x * PT, (total_h - (ytop[b] + sub * sub_h)) * PT

    L = ["digraph {", "  graph [bgcolor=white margin=0.02];",
         '  node [shape=plaintext fontname="Arial" fontsize=%.1f '
         'height=0.14 width=0.01 margin="0.01,0.005"];' % fontsize,
         #: graphviz scales the arrowhead with penwidth, so at 2.2 pt the
         #: heads were larger than the gaps between words
         '  edge [arrowsize=0.2 color="%s"];' % GREY_EDGE]
    for w in place:
        x, y = xy(w)
        if w in counts:
            lab = ('<<B>%s</B> <FONT POINT-SIZE="7" COLOR="%s">%d</FONT>>'
                   % (w, GREY_NUM, counts[w]))
            L.append('  "%s" [label=%s pos="%.1f,%.1f!"];' % (w, lab, x, y))
        elif w == spine[0]:
            L.append('  "%s" [label=<<B>%s</B>> pos="%.1f,%.1f!"];' % (w, w, x, y))
        else:
            L.append('  "%s" [label="%s" fontcolor="%s" pos="%.1f,%.1f!"];'
                     % (w, w, GREY_WAY, x, y))
    for a, b in sorted(edges):
        v = float(S[pos[a], pos[b]])
        extra = ""
        if (a, b) == mark:
            extra = (' label="%.2f" fontname="Arial" fontsize=7 fontcolor="%s"'
                     % (mark_v, GREY_NUM))
        L.append('  "%s" -> "%s" [penwidth=%.2f%s];' % (a, b, wid(v), extra))
    L.append("}")
    open(base + ".dot", "w").write("\n".join(L) + "\n")
    for ext, args in (("png", ["-Gdpi=300"]), ("pdf", []), ("tif", ["-Gdpi=300"])):
        r = subprocess.run(["neato", "-n2", "-T" + ext] + args
                           + [base + ".dot", "-o", base + "." + ext],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("neato -T%s failed: %s" % (ext, r.stderr[:400]))
    return mark, mark_v


def build(a, basis, cut, out_dir, name):
    routes, counts, S, pos, words, tot = corridor(
        a.prompt, a.space, a.stage, basis, cut, a.src)
    place, spine, rows, sub_depth, head = layout(
        routes, counts, a.width, a.fontsize)
    base = os.path.join(out_dir, name)
    mark, mv = emit(place, spine, rows, sub_depth, routes, counts, S, pos,
                    head, base, a.width, a.height, a.fontsize)
    print("  %-22s %2d dst (%2d/%2d lin)  %2d nodes  %d rows of %s  weakest "
          "%s->%s %.2f"
          % (name, len(counts), sum(counts.values()), tot, len(place),
             len(rows), "/".join(str(len(r)) for r in rows),
             mark[0], mark[1], mv))
    return base


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=run.FIG2)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--space", default="llama_resid_mean")
    ap.add_argument("--stage", default="base")
    ap.add_argument("--basis", default="faller",
                    choices=("argmax", "faller", "crossing"))
    ap.add_argument("--min-lineages", type=int, default=2)
    ap.add_argument("--width", type=float, default=4.33)
    ap.add_argument("--height", type=float, default=5.0)
    ap.add_argument("--fontsize", type=float, default=8.0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "figures"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    if a.all:
        for basis in ("argmax", "faller", "crossing"):
            for cut in (1, 2):
                build(a, basis, cut, a.out, "ci_chain_%s_n%d" % (basis, cut))
    else:
        build(a, a.basis, a.min_lineages, a.out,
              "ci_chain_%s_n%d" % (a.basis, a.min_lineages))
    return 0


if __name__ == "__main__":
    sys.exit(main())
