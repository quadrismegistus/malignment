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


def layout(routes, counts, fold_slack=0):
    """-> ({word: (col, row, lane)}, spine, n_rows). Fold chosen to balance.

    The SPINE is the route to the heaviest destination -- the word most
    lineages actually move to -- because that is the sequence the plate is
    about. Every other route shares a prefix with it and diverges once; the
    tail after divergence is a branch.
    """
    head = max(counts, key=lambda w: (counts[w], len(routes[w])))
    spine = routes[head]
    on_spine = {w: i for i, w in enumerate(spine)}
    branches = []          # (attach index on spine, [words])
    for w, r in routes.items():
        if w == head:
            continue
        i = 0
        while i < len(r) and r[i] in on_spine and on_spine[r[i]] == i:
            i += 1
        if i == 0:
            raise SystemExit("route to %r shares no prefix with the spine" % w)
        branches.append((i - 1, r[i:]))
    #: fold where the two columns come out closest in height, counting the rows
    #: each column's branches need below their attachment
    best, bestk = None, None
    for k in range(3, len(spine) - 2):
        lrows = k + 1
        rrows = len(spine) - k - 1
        for at, tail in branches:
            if at <= k:
                lrows = max(lrows, at + 1 + len(tail))
            else:
                rrows = max(rrows, (at - k - 1) + 1 + len(tail))
        cost = abs(lrows - rrows) + fold_slack * max(lrows, rrows)
        if best is None or (max(lrows, rrows), cost) < best:
            best, bestk = (max(lrows, rrows), cost), k
    k = bestk
    place = {}
    for i, w in enumerate(spine):
        place[w] = (0, i, 0) if i <= k else (1, i - k - 1, 0)
    #: branches share ONE outward lane per column wherever their row spans do
    #: not overlap, which on this corridor they never do
    used = {0: [], 1: []}
    for at, tail in branches:
        col = 0 if at <= k else 1
        r0 = (at if col == 0 else at - k - 1) + 1
        span = set(range(r0, r0 + len(tail)))
        lane = 1
        while any(span & s for l, s in used[col] if l == lane):
            lane += 1
        used[col].append((lane, span))
        for j, w in enumerate(tail):
            place[w] = (col, r0 + j, lane)
    nrows = max(r for _c, r, _l in place.values()) + 1
    return place, spine, nrows, k


def emit(place, spine, nrows, routes, counts, S, pos, head, base,
         width_in=4.33, height_in=5.0, fontsize=8.0):
    import math
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

    nlane = {c: max([l for (cc, _r, l) in place.values() if cc == c] + [0])
             for c in (0, 1)}
    #: **SPREAD TO THE MEASURE.** Height is the binding constraint and width
    #: was going spare -- 2.43 in used of 4.33 -- so the columns are placed
    #: from the available width rather than at a fixed gap. Lanes are 0.42 in
    #: outward of their spine; whatever is left becomes the gutter.
    #:
    #: The inset is half the widest label plus a hair: a node's box is its
    #: LABEL once `width` stops forcing 0.75 in, and positions are centres, so
    #: a column placed 0.2 in from the edge still hangs its text over it.
    lane_w = 0.42
    widest = max(len(w) for w in place) * fontsize * 0.0077 + 0.16
    inset = widest / 2.0
    left_edge = inset + lane_w * nlane[0]
    right_edge = width_in - inset - lane_w * nlane[1]
    colx = {0: left_edge, 1: right_edge}
    #: **THE SECOND COLUMN ASCENDS (serpentine).** With both columns running
    #: downward the fold connector is a diagonal from bottom-left to top-right
    #: that crosses the whole plate and dominates it; routing it as an elbow
    #: through the gutter instead draws a full-height vertical line that reads
    #: as a divider. Reversing the second column makes the connector a short
    #: hop at the bottom and sends the chain corner to corner, `kill` at top
    #: left to `scream` at top right. Direction is never ambiguous because
    #: every edge is arrowed.
    step = (height_in - 0.32) / max(1, nrows - 1)

    def xy(w):
        c, r, l = place[w]
        x = colx[c] + (-lane_w * l if c == 0 else lane_w * l)
        y = ((height_in - 0.16) - r * step) if c == 0 else (0.16 + r * step)
        return x * PT, y * PT

    #: **A plaintext node is still 0.5 in tall by default**, which added a
    #: quarter inch at each end and pushed a 5.00 in target to 5.29. `height`
    #: and a near-zero graph margin bring the rendered box back to the span
    #: the positions actually describe.
    L = ["digraph {", "  graph [bgcolor=white margin=0.02];",
         '  node [shape=plaintext fontname="Arial" fontsize=%.1f '
         'height=0.16 width=0.01 margin="0.01,0.005"];' % fontsize,
         #: graphviz scales the arrowhead with penwidth, so at 2.2 pt the
         #: heads were larger than the gaps between words. 0.2 holds them
         #: to a consistent small mark across the whole width range.
         '  edge [arrowsize=0.2 color="%s"];' % GREY_EDGE]
    for w in place:
        x, y = xy(w)
        if w in counts:
            lab = ('<<B>%s</B> <FONT POINT-SIZE="7" COLOR="%s">%d</FONT>>'
                   % (w, GREY_NUM, counts[w]))
            L.append('  "%s" [label=%s pos="%.1f,%.1f!"];' % (w, lab, x, y))
        elif w == spine[0]:
            #: the source is bold too: it is the word the plate is about, and
            #: in 60% grey it reads as one more way station
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
    #: `-n2` uses the positions in the file instead of running a layout, which
    #: is the only way to fold a spine; `dot` will not do it.
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
    head = max(counts, key=lambda w: (counts[w], len(routes[w])))
    place, spine, nrows, k = layout(routes, counts)
    base = os.path.join(out_dir, name)
    mark, mv = emit(place, spine, nrows, routes, counts, S, pos, head, base,
                    a.width, a.height, a.fontsize)
    print("  %-34s %2d dst (%2d/%2d lineages)  %2d nodes  %2d rows  fold after "
          "%r  weakest %s->%s %.2f"
          % (name, len(counts), sum(counts.values()), tot, len(place), nrows,
             spine[k], mark[0], mark[1], mv))
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
