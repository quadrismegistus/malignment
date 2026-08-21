"""Generate the API-model passages that place a model on the anchor plane.

    python .../run_api_passages.py --model deepseek/deepseek-v4-flash --version 3
    python .../run_api_passages.py --model claude-haiku-4-5 --version 3

Writes `$MALIGNMENT_DATA/api_passages/<slug>.jsonl`, one row per passage, ready
for `ref_surprisal.py`.

## THE STEMS ARE THE NARRATIVE-CODED SET, EXACTLY

Taken from `ref_pool.jsonl`'s `model_narrative` rows, which are 5,687 passages
over **exactly 100 distinct stems, all English, zero CJK** -- the passC
`narrative_A == True` population that `two_axes.csv` is built from. So an API
model lands on the same stems as the 57 open models by construction rather than
by a filter that has to be kept in step. f11_l2 has 197 stems; the other 97 are
Chinese and were never coded.

## SIX SAMPLES, AND WHY NOT ONE OR TWENTY

ICC of `bits_per_byte` within (model, prompt) is **0.072** over 58 models, so
resampling a stem costs little: 600 passages carry an effective n of 442 against
the human corpora's 500. Twenty would give 847 for 3.3x the spend; one would give
100. The corpus itself sampled 20 per cell.

Adding STEMS would beat adding samples -- 298 stems x 2 gives an effective 555 --
but the extra stems come from the `passage` corpus, which has no passC coding, so
that population is not comparable. The 100 is the binding constraint and it is
the right one.

## METADATA IS THE CACHE KEY, AND THAT CUTS BOTH WAYS

`llm.py:_make_key` puts metadata in the key. At temperature 1 that is what makes
six samples six passages rather than one passage returned six times -- `sample`
must vary or they collapse. `version` is here so a rerun can be made deliberately
fresh; bumping it re-keys everything and re-pays in full, which the library's own
docstring warns about citing this seat's field report (24 items became 48 keys).
So bump it on purpose, never by accident.
"""

import argparse, collections, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)
from generate_task import (SYSTEM_PROMPT, CORPUS_TEMPERATURE, clean)   # noqa: E402

CJK = re.compile(r"[一-鿿]")
OUT_DIR = os.path.join(DATA, "api_passages")


def stems():
    """The 100 narrative-coded English stems. -> sorted list

    Sorted so the file is reproducible; the SAMPLING is over the model's own
    randomness at temperature 1, not over which stems were picked.
    """
    p = os.path.join(DATA, "ref_pool", "ref_pool.jsonl")
    out = set()
    for line in open(p):
        r = json.loads(line)
        if r.get("pool") == "model_narrative":
            out.add(r["prompt"])
    bad = [s for s in out if CJK.search(s)]
    assert not bad, "CJK stems in the narrative set, which should be impossible: %s" % bad[:3]
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--samples", type=int, default=6)
    ap.add_argument("--version", type=int, required=True,
                    help="bump to force fresh generations; it re-keys and re-pays")
    ap.add_argument("--max-tokens", type=int, default=400)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-stems", type=int)
    a = ap.parse_args(argv)

    from largeliterarymodels.llm import LLM
    st = stems()
    if a.limit_stems:
        st = st[:a.limit_stems]
    slug = re.sub(r"[^a-z0-9]+", "_", a.model.lower()).strip("_")
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "%s_v%d.jsonl" % (slug, a.version))

    prompts, metas = [], []
    for s in st:
        for i in range(a.samples):
            prompts.append(s)
            #: `sample` MUST vary or all six collapse to one cache entry.
            metas.append({"stem": s, "sample": i, "version": a.version})
    print("%s | %d stems x %d = %d calls | temp %.1f | max_tokens %d"
          % (a.model, len(st), a.samples, len(prompts), CORPUS_TEMPERATURE, a.max_tokens))
    print("system: %r" % SYSTEM_PROMPT)

    llm = LLM(model=a.model, temperature=CORPUS_TEMPERATURE, max_tokens=a.max_tokens)
    errors = {}
    got = llm.map(prompts, system_prompt=SYSTEM_PROMPT, metadata_list=metas,
                  num_workers=a.workers, errors=errors)

    rows, fired, n_none = [], collections.Counter(), 0
    for m, text in zip(metas, got):
        if not text:
            n_none += 1
            continue
        cleaned, what = clean(text, m["stem"])
        fired["stem"] += what["stem_chars"] > 0
        fired["stars"] += what["stars"] > 0
        fired["recased"] += bool(what["recased"])
        rows.append(dict(id="%s-v%d-%03d-%d" % (slug, a.version,
                                                st.index(m["stem"]), m["sample"]),
                         corpus="api", model=a.model, stem=m["stem"],
                         sample=m["sample"], version=a.version,
                         text=cleaned, raw=text, n_words=len(cleaned.split()),
                         n_bytes=len(cleaned.encode()), **what))
    with open(out_path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\nwrote %d passages (%d empty, %d errors) -> %s"
          % (len(rows), n_none, len(errors), out_path))
    print("clean() fired: %s of %d" % (dict(fired), len(rows)))
    if rows:
        w = sorted(r["n_words"] for r in rows)
        b = sorted(r["n_bytes"] for r in rows)
        print("words  min %d  p10 %d  median %d  p90 %d  max %d"
              % (w[0], w[len(w)//10], statistics.median(w), w[9*len(w)//10], w[-1]))
        print("bytes  min %d  p10 %d  median %d  p90 %d  max %d   (corpus median 1,082)"
              % (b[0], b[len(b)//10], statistics.median(b), b[9*len(b)//10], b[-1]))
        #: the M=200 prefix is what every comparison uses, so report the loss HERE
        #: rather than discovering it after scoring. ~4.3 chars/token on this
        #: corpus, so this is an estimate and the scorer's count is the truth.
        est = sum(1 for r in rows if r["n_bytes"] < 200 * 4.3)
        print("estimated under the M=200 prefix: %d of %d" % (est, len(rows)))
    if errors:
        k = list(errors.items())[:2]
        print("first errors: %s" % k)


if __name__ == "__main__":
    main()
