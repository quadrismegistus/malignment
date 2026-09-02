"""Word norms and semantic fields over the JUDGED stories. -> per-lineage JSON.

    python fields_stats.py                     -> results/fields_stats.json
    python fields_stats.py --cap 40            fewer stories per cell, faster

## WHY THIS EXISTS RATHER THAN analyse.py

`analyse.py` already computes both contrasts, and this differs from it in three
ways that matter for anything comparing them to the annotation results.

**1. THE POPULATION.** `analyse.py:load_raw` takes every raw generation over 150
words that survives a regex escape check. It does NOT use the story judge, so
about 30% of the base arm it measures is not narrative -- 12% essay and 14%
incoherent by the judge's count. A valence or concreteness difference computed
there is partly "the base arm writes essays", which is true and is a different
claim from "base STORIES differ". This gates on `pure_story` and the same
200-word floor `conflict.py` uses, so the norms panel and the annotation panel
describe the same texts.

**2. SEMANTIC FIELDS WERE POOLED ACROSS LINEAGES.** `semantic_fields_contrast`
accumulates every lineage into one counter and reports a single base/aligned
ratio. That has no per-lineage value, so it cannot be sign-tested over lineages
and cannot show which models move -- one prolific lineage can carry a category.
Here every category is a per-lineage share and gets the same paired tests as
everything else.

**3. `endpoints()` vs the judged corpus.** analyse.py reads the stash through
`roster.endpoints()`, one aligned model per base. This reads the judged corpus,
which carries `model` and covers every rung.

Norm values are the mean over a lineage's stories of that story's token-weighted
norm mean, which is analyse.py's definition kept deliberately so the two are
comparable where the populations overlap.

COVERAGE IS EMITTED AND MUST BE READ. Warriner covers ~69% of content tokens and
Brysbaert ~98%. If coverage differs between arms the norm difference is partly a
coverage difference, so `*_coverage` scales are in the output as first-class rows.
"""
import argparse
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('MALIGNMENT_DATA', os.path.expanduser('~/malignment-data'))
CORPUS = os.path.join(DATA, 'national_story', 'judged_stories_v2.jsonl')
NORMS = ['warriner_valence', 'warriner_arousal', 'warriner_dominance',
         'brysbaert_concreteness', 'k_transgressiveness', 'k_charge',
         'k_register_level', 'k_vulgarity', 'brooke_formality',
         'warriner_coverage', 'brysbaert_coverage', 'k_coverage']


def holm(pairs):
    ordered = sorted(pairs, key=lambda kp: kp[1])
    m, out, run = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def main(argv=None):
    from scipy.stats import binomtest, ttest_rel, wilcoxon
    from malignment import fields

    ap = argparse.ArgumentParser()
    ap.add_argument('--frame', default='raw', choices=('raw', 'prefill'))
    ap.add_argument('--cap', type=int, default=0, help='0 = every story')
    ap.add_argument('--min-per-cell', type=int, default=5)
    ap.add_argument('--min-share', type=float, default=0.002,
                    help='drop categories rarer than this in both arms')
    ap.add_argument('--out', default='results/fields_stats.json')
    a = ap.parse_args(argv)

    cells = collections.defaultdict(list)
    for line in open(CORPUS, encoding='utf-8'):
        r = json.loads(line)
        if not r['pure_story'] or r['frame'] != a.frame or r['n_words'] < 200:
            continue
        cells[(r['lineage'], r['arm'])].append(r)
    lins = sorted({L for L, _ in cells}
                  & {L for L, arm in cells if arm == 'base'}
                  & {L for L, arm in cells if arm == 'aligned'})
    lins = [L for L in lins
            if len(cells[(L, 'base')]) >= a.min_per_cell
            and len(cells[(L, 'aligned')]) >= a.min_per_cell]
    print('%d lineages, %d stories'
          % (len(lins), sum(len(cells[(L, x)]) for L in lins
                            for x in ('base', 'aligned'))))

    per = collections.defaultdict(dict)      #: scale -> {lineage: (base, aligned)}
    for i, L in enumerate(lins):
        got = {}
        for arm in ('base', 'aligned'):
            rows = cells[(L, arm)]
            if a.cap:
                #: interleave demonyms so a cap cannot select on nationality
                bd = collections.defaultdict(list)
                for r in rows:
                    bd[r['demonym']].append(r)
                woven = []
                for j in range(max(len(v) for v in bd.values())):
                    for dm in sorted(bd):
                        if j < len(bd[dm]):
                            woven.append(bd[dm][j])
                rows = woven[:a.cap]
            ns, tokcat, typecat, ntok, ntyp = [], collections.Counter(), \
                collections.Counter(), 0, 0
            for r in rows:
                n = fields.norms(r['text'])
                if n and n.get('n_content'):
                    ns.append(n)
                toks = [w.lower() for w in fields.TOKEN.findall(r['text'])]
                for w in toks:
                    for c in (fields.usas(w) or set()):
                        tokcat['usas:' + c] += 1
                    for c in (fields.rid(w) or set()):
                        tokcat['rid:' + c] += 1
                ntok += len(toks)
                for w in set(toks):
                    for c in (fields.usas(w) or set()):
                        typecat['usas:' + c] += 1
                    for c in (fields.rid(w) or set()):
                        typecat['rid:' + c] += 1
                ntyp += len(set(toks))
            v = {k: st.mean(n[k] for n in ns if k in n)
                 for k in NORMS if any(k in n for n in ns)}
            for c, k in tokcat.items():
                v['tok/' + c] = k / max(1, ntok)
            for c, k in typecat.items():
                v['typ/' + c] = k / max(1, ntyp)
            got[arm] = v
        for k in set(got['base']) & set(got['aligned']):
            per[k][L] = (got['base'][k], got['aligned'][k])
        print('  %2d/%d %s' % (i + 1, len(lins), L.split('/')[-1][:40]))

    rows = []
    for scale, d in per.items():
        if len(d) < 6:
            continue
        b = [x for x, _ in d.values()]
        al = [y for _, y in d.values()]
        if scale.startswith(('tok/', 'typ/')) and \
                max(sum(b) / len(b), sum(al) / len(al)) < a.min_share:
            continue
        diffs = [y - x for x, y in zip(b, al)]
        up = sum(1 for x in diffs if x > 0)
        dn = sum(1 for x in diffs if x < 0)
        if up + dn < 3:
            continue
        md = sum(diffs) / len(diffs)
        sd = (sum((x - md) ** 2 for x in diffs) / (len(diffs) - 1)) ** 0.5
        kind = ('coverage' if scale.endswith('_coverage')
                else 'norm' if scale in NORMS
                else 'field_tokens' if scale.startswith('tok/') else 'field_types')
        rows.append(dict(
            scale=scale, kind=kind, n_lineages=len(d), up=up, down=dn,
            ties=len(diffs) - up - dn,
            base=sum(b) / len(b), aligned=sum(al) / len(al), mean_diff=md,
            ratio=(sum(al) / len(al)) / (sum(b) / len(b)) if sum(b) else None,
            dz=md / sd if sd else 0.0,
            p_sign=float(binomtest(up, up + dn, 0.5).pvalue),
            p_wilcoxon=float(wilcoxon(diffs).pvalue) if len(diffs) > 5 else 1.0,
            p_t=float(ttest_rel(al, b).pvalue),
            per_lineage={L: [round(x, 6), round(y, 6)] for L, (x, y) in d.items()}))

    #: Holm within kind: a word norm and a USAS category share are not one family
    for kind in {r['kind'] for r in rows}:
        fam = [r for r in rows if r['kind'] == kind]
        for name, key in (('p_sign', 'h_sign'), ('p_wilcoxon', 'h_wilcoxon'),
                          ('p_t', 'h_t')):
            adj = holm([(r['scale'], r[name]) for r in fam])
            for r in fam:
                r[key] = adj[r['scale']]
        for r in fam:
            r['holm_family'] = kind
            r['holm_family_size'] = len(fam)

    rows.sort(key=lambda r: min(r['h_sign'], r['h_wilcoxon'], r['h_t']))
    outp = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    payload = dict(
        experiment='national_story fields+norms', frame=a.frame,
        population='pure_story, >=200 words -- SAME gate as the annotation panel',
        unit='lineage', n_lineages=len(lins),
        aggregation=('norm = mean over a lineage stories of that story '
                     'token-weighted norm mean; field = category share of that '
                     'lineage tokens (tok/) or types (typ/)'),
        correction='holm within kind (norm | coverage | field_tokens | field_types)',
        warnings=[
            'coverage scales are first-class rows: Warriner covers ~69% of '
            'content tokens, so a valence difference can be a coverage difference',
            'tok/ and typ/ answer different questions -- density vs breadth -- '
            'and disagree on the direction of a minority of categories',
            'analyse.py computes these on a DIFFERENT population: no judge gate, '
            'so ~30% of its base arm is essay or incoherent text',
        ],
        n_rows=len(rows), values=rows)
    tmp = outp + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(payload, fh)
    os.replace(tmp, outp)
    print('\nwrote %s  (%d scales, %.1f MB)'
          % (outp, len(rows), os.path.getsize(outp) / 1e6))
    for kind in sorted({r['kind'] for r in rows}):
        fam = [r for r in rows if r['kind'] == kind]
        sig = sum(1 for r in fam
                  if min(r['h_sign'], r['h_wilcoxon'], r['h_t']) < 0.05)
        print('   %-14s %4d scales, %3d at holm p<0.05' % (kind, len(fam), sig))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
