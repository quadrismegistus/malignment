"""Contextual POS for every (prompt, word) in twp_words_v4, en then zh, serially.

    python -u pos_pass.py                       # both, en first
    python -u pos_pass.py --lang zh
    python -u pos_pass.py --limit 50            # smoke test

Warms `malignment.pos`'s stash AND writes a portable table, so downstream code can
either call `get_pos` (warm, no spaCy) or read the file.

## WHY SERIAL

The stash is a single `data.jsonl` under `data/pos_context/` with a lock file. Two
long-running writers appending ~1.4M entries each to one jsonl on the strength of
an untested lock is not a risk worth taking for a pass that runs once, so en and zh
go one after the other. The tagger ids differ (`en_core_web_sm` vs `zh_core_web_sm`)
and a prompt is either English or Chinese, never both, so the two key sets are
disjoint -- the concern was the file, not the keys.

## BATCHED, AND VERIFIED IDENTICAL TO get_pos

`get_pos` calls `nlp(prompt + " " + w)` once per word and takes `doc[-1].pos_`.
This uses `nlp.pipe` over the same strings, which is the same computation batched.
Checked before relying on it: single-call, piped, and `get_pos` agree exactly on a
probe including the cases that matter (`table` -> VERB after "wanted to", `the` ->
PRON, `out` -> VERB).

## THE CHINESE CHECKS THAT COULD HAVE FAILED SILENTLY

Chinese does not use spaces, and a Chinese word can segment into several tokens --
either would make `doc[-1].pos_` the tag of a trailing morpheme rather than of the
word. Both were checked rather than assumed: on `他把手机掉进马桶里，大喊` + `“`,
`她在花园里坐在他身旁，握着他的` + `手`, and three more, the space makes no
difference to the tag, and `准备` / `报仇` / `结束` each segment as ONE token. The
space is kept so the string is byte-identical to what `get_pos` would have built,
because a stash entry that disagrees with the function that reads it is worse than
no stash entry.

## A LATENT HAZARD IN THE STASH KEY, RECORDED NOT FIXED

`pos.tagger_id` reads `nlp.meta["name"]`, which is `core_web_sm` for BOTH models --
the language lives in `meta["lang"]`, which it does not read. So
`en_core_web_sm` and `zh_core_web_sm` both key as `core_web_sm-3.8.0` and the stash
cannot tell an English tag from a Chinese one.

It is safe here because a prompt is either English or Chinese and the two prompt
sets are disjoint, so no key actually collides. It is NOT safe in general: anything
that tags a prompt with the wrong model overwrites silently and the key records
nothing about which model produced the value. Not fixed here because `tagger_id` is
shared code and a new key would cold-start every existing entry -- that is a
decision for whoever owns `malignment/pos.py`. **The portable table below carries
`lang` explicitly so the artifact is unambiguous even though the stash is not.**

## RESUMABLE, AND THE RETRY IS WHY

The first full run died at 1,250 of 2,612 English prompts with
`ClickHouseError: Code: 210, Connection refused (localhost:9000)` -- the server
went away mid-pass. Nothing was lost: every pair tagged before that point was
already in the stash, verified by sampling the pass's own output table against it
(12 of 12 agreed). **The stash IS the resume mechanism**, since only misses are
tagged, so a re-run costs a lookup per already-done pair and no spaCy at all.

What was missing is tolerance for a transient server. `q()` retries a ClickHouse
call with backoff rather than letting one refused connection discard the rest of
the pass. It re-raises after the last attempt: a server that is genuinely down
should stop the run, not be retried silently for an hour.

## WHAT THIS IS FOR

The rating manifest (`priority.py`) filtered ratability on BARE words via
`is_function_word`, which is the unreliable path -- it left `“` at the top of the
Chinese tier and `out`/`back` in the English one. Contextual POS is the correct
filter and it is the same one `named_under_dose --verbs-only` already uses, so one
pass makes the manifest and the analysis agree instead of disagreeing silently.

Tagging is done for EVERY word regardless of POS. The content-vs-verb decision is a
filter applied afterward, so one pass serves both and the choice stays visible.
"""

import argparse, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
OUT = os.path.expanduser("~/malignment-data/contextual_norms")
CJK = re.compile(r"[一-鿿]")
MODEL = {"en": "en_core_web_sm", "zh": "zh_core_web_sm"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=0, help="first N prompts, smoke test")
    ap.add_argument("--batch", type=int, default=256, help="spaCy pipe batch")
    ap.add_argument("--pbatch", type=int, default=60,
                    help="prompts per ClickHouse query")
    ap.add_argument("--every", type=int, default=25, help="progress every N prompts")
    ap.add_argument("--no-stash", action="store_true",
                    help="write the table only, leave the stash cold")
    a = ap.parse_args(argv)

    import gzip, csv, spacy
    from malignment import ch, pos as P

    def q(sql, tries=6, wait=5.0):
        """ClickHouse with backoff. Re-raises after the last attempt."""
        for k in range(tries):
            try:
                return ch.query(sql)
            except Exception as e:
                if k == tries - 1:
                    raise
                print("  [retry %d/%d in %.0fs] %s"
                      % (k + 1, tries - 1, wait * (k + 1), str(e)[:90]), flush=True)
                time.sleep(wait * (k + 1))

    prompts = [r["prompt"] for r in
               q("SELECT DISTINCT prompt FROM twp_words_v4 ORDER BY prompt")]
    byl = {"en": [p for p in prompts if not CJK.search(p)],
           "zh": [p for p in prompts if CJK.search(p)]}
    print("twp_words_v4 prompts: %d total | en %d | zh %d"
          % (len(prompts), len(byl["en"]), len(byl["zh"])), flush=True)

    langs = [a.lang] if a.lang else ["en", "zh"]
    os.makedirs(os.path.expanduser(a.out), exist_ok=True)
    st = None if a.no_stash else P._stash()

    for lang in langs:
        plist = byl[lang]
        if a.limit:
            plist = plist[:a.limit]
        if not plist:
            print("[%s] no prompts, skipping" % lang, flush=True)
            continue
        nlp = spacy.load(MODEL[lang])
        tid = P.tagger_id(nlp)
        path = os.path.join(os.path.expanduser(a.out), "pos_%s.csv.gz" % lang)
        print("\n[%s] %s prompts, model %s, tagger_id %s\n[%s] -> %s"
              % (lang, len(plist), MODEL[lang], tid, lang, path), flush=True)

        t0 = time.time()
        n_pairs = n_hit = 0
        counts = {}
        #: APPEND on resume. Opening "wt" would truncate the 1M pairs the dead run
        #: already wrote and silently hand back a shorter table that still looks
        #: complete. The header is written only when the file is new.
        fresh = not os.path.exists(path)
        with gzip.open(path, "wt" if fresh else "at", encoding="utf-8",
                       newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            if fresh:
                w.writerow(["lang", "prompt", "word", "pos"])
            else:
                print("[%s] appending to an existing table" % lang, flush=True)
            #: ONE QUERY PER BATCH OF PROMPTS, NOT PER PROMPT. The first version
            #: issued `WHERE base64Encode(prompt) = ...` once per prompt, which is
            #: 3,019 full scans of a 491M-row table. Batched, it is ~50 queries.
            import base64, collections as _c
            i = 0
            for s0 in range(0, len(plist), a.pbatch):
                blk = plist[s0:s0 + a.pbatch]
                inlist = ",".join(
                    "'" + base64.b64encode(x.encode()).decode() + "'" for x in blk)
                bag = _c.defaultdict(list)
                for r in q(
                        "SELECT prompt, word FROM twp_words_v4 "
                        "WHERE base64Encode(prompt) IN (%s) GROUP BY prompt, word"
                        % inlist):
                    bag[r["prompt"]].append(r["word"])
                for prompt in blk:
                    i += 1
                    words = bag.get(prompt) or []
                    if not words:
                        continue
                    #: only MISSES are tagged, matching get_pos, so a re-run is cheap
                    miss, got = [], {}
                    if st is not None:
                        for x in words:
                            h = st.get({"tagger": tid, "prompt": prompt, "word": x})
                            if h is None:
                                miss.append(x)
                            else:
                                got[x] = h
                                n_hit += 1
                    else:
                        miss = words
                    if miss:
                        for x, doc in zip(miss, nlp.pipe(
                                [prompt + " " + x for x in miss], batch_size=a.batch)):
                            pv = doc[-1].pos_ if len(doc) else "X"
                            got[x] = pv
                            if st is not None:
                                st[{"tagger": tid, "prompt": prompt, "word": x}] = pv
                    for x in words:
                        w.writerow([lang, prompt, x, got[x]])
                        counts[got[x]] = counts.get(got[x], 0) + 1
                    n_pairs += len(words)
                    if i % a.every == 0 or i == len(plist):
                        el = time.time() - t0
                        rate = n_pairs / max(el, 1e-9)
                        left = (len(plist) - i) * (n_pairs / i) / max(rate, 1e-9)
                        print("[%s] %5d/%-5d prompts | %9d pairs | %6.0f pair/s | "
                              "cached %d | elapsed %5.1fm | eta %5.1fm"
                              % (lang, i, len(plist), n_pairs, rate, n_hit,
                                 el / 60, left / 60), flush=True)
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
        print("[%s] DONE %d pairs in %.1fm | %s"
              % (lang, n_pairs, (time.time() - t0) / 60,
                 "  ".join("%s %d" % (k, v) for k, v in top)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
