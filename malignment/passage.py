"""One passage of text, as an object, with both axes as lazy properties.

    from malignment import Passage

    p = Passage("She was ugly and misshapen and she wanted to run.")
    p.sha            # the content address
    p.sentences      # nltk-en split
    p.surprisal      # reference bits/token
    p.surprisal_at(200)
    p.word_bits      # [{word, bits, partial}]
    p.drift          # mean_drift
    p.metrics        # the whole drift family

Generated passages carry their provenance and score the same way:

    ps = ck.generate(stem, n=10)      # -> [Passage]
    [p.drift for p in ps]

## THE NOUN IS HERE, THE MEASUREMENT IS IN `score.py`

The same split `Checkpoint` keeps against `runners`: this file answers questions
about a passage and holds no instrument. Every property delegates to
`score.py`, which owns the models, the content store and the guards. Nothing
here decides how a thing is measured, so there is no second way to measure it.

## THE PROPERTIES ARE LAZY, CACHED, AND CHEAP ONLY AFTER THE FIRST ONE

`p.surprisal` on an unscored passage loads a 7B model. `score.py` holds the
loaders as process-level singletons, so the SECOND passage is cheap and the
six-hundredth is free -- but the first call in a fresh process is not, and a
property that hides that would be a bad surprise.

**For anything at scale, use the batch calls.** `score.surprisal([...])` and
`score.drift([...])` take every text in one pass, which is one model load and
one forward loop rather than an interleaving of both instruments:

    score.surprisal([p.text for p in ps])     # then the properties are lookups

## A GENERATED PASSAGE IS THE SAME OBJECT AS A CORPUS ONE

`generate.Passage` was a namedtuple carrying text plus provenance. It is this
class now, so a passage sampled from a checkpoint and a passage read out of a
corpus answer the same questions -- and a function that scores one scores the
other. The generation fields are optional and `None` on a passage that was not
generated here.
"""

import os


class Passage:
    """Text, its identity, and both axes on demand."""

    #: the fields `generate.generate` fills in. Absent on a corpus passage,
    #: and named here so `_asdict()` round-trips through the generations stash.
    GEN_FIELDS = ("prompt", "model", "frame", "seed", "decoder",
                  "n_new_tokens", "finish", "sys_supported",
                  #: the full condition, so a stored passage is self-describing
                  #: and does not need its key to be interpretable
                  "system", "system_default", "user", "prefill", "user_msg",
                  "template")

    def __init__(self, text, id=None, corpus=None, **gen):
        self.text = text
        self.id = id
        self.corpus = corpus
        for f in self.GEN_FIELDS:
            setattr(self, f, gen.pop(f, None))
        #: anything else the caller attached travels rather than being dropped;
        #: a passage read from a store often carries fields this class has never
        #: heard of, and losing them silently is how a join key disappears.
        self.extra = gen

    # ---- identity -------------------------------------------------------
    @property
    def sha(self):
        """sha256(text)[:16] -- the content address `score.py` keys on."""
        from . import score
        return score.sha(self.text)

    def __repr__(self):
        return "Passage(%s %r%s)" % (
            self.sha, self.text[:38] + ("..." if len(self.text) > 38 else ""),
            "" if self.model is None else " from %s" % self.model)

    def __eq__(self, other):
        return isinstance(other, Passage) and other.text == self.text

    def __hash__(self):
        return hash(self.text)

    def __len__(self):
        return len(self.text)

    # ---- structure ------------------------------------------------------
    @property
    def sentences(self):
        """The nltk-en split, the same one the drift axis embedded."""
        from . import score
        return score._split(self.text)

    @property
    def n_sents(self):
        return len(self.sentences)

    # ---- the surprisal axis ---------------------------------------------
    @property
    def surprisal(self):
        """Reference bits/token over the WHOLE passage, or None if unscorable."""
        from . import score
        return score.surprisal([self.text])[0]

    def surprisal_at(self, m):
        """Bits/token over the first `m` scored tokens. None if shorter.

        The prefix control, not a convenience: passages differ in length, and a
        whole-passage mean is partly a length statistic. Returning None rather
        than a short-passage mean keeps a length-selected passage out of the
        comparison instead of quietly biasing it.
        """
        from . import score
        return score.surprisal([self.text], m=m)[0]

    @property
    def word_bits(self):
        """Per-word surprisal. -> [{word, bits, partial}]

        The first word is `partial` and unscored -- nothing precedes it -- so it
        is marked rather than dropped, and must be excluded from any extreme.
        """
        from . import score
        return score.word_bits(self.text)

    # ---- the drift axis --------------------------------------------------
    @property
    def sentence_vecs(self):
        """L2-normalised bge vectors, one per sentence. CPU, always."""
        from . import score
        return score.sentence_vecs(self.text)[1]

    @property
    def metrics(self):
        """The whole drift family. Only the length-free ones carry a claim."""
        from . import score
        return score.drift([self.text])[0]

    @property
    def drift(self):
        """`mean_drift`: the mean cosine step between consecutive sentences.

        None below two sentences, where there is no step to take -- not 0.0,
        which would read as a passage that held perfectly still.
        """
        return self.metrics.get("mean_drift")

    # ---- interop ---------------------------------------------------------
    def _asdict(self):
        """Everything, flat. What the generations stash stores."""
        d = {"text": self.text, "id": self.id, "corpus": self.corpus}
        d.update({f: getattr(self, f) for f in self.GEN_FIELDS})
        d.update(self.extra)
        return d

    @classmethod
    def from_row(cls, row):
        """Rebuild from a stored dict. Unknown keys survive in `extra`."""
        r = dict(row)
        return cls(r.pop("text"), id=r.pop("id", None),
                   corpus=r.pop("corpus", None), **r)


def score_all(passages, m=None):
    """Score a list in ONE pass per instrument. -> the same list.

    The batch path. Scoring by property in a loop interleaves the two
    instruments and, in a cold process, pays both loads before the first answer;
    this fills the content store for every text up front so the properties
    afterwards are lookups.
    """
    from . import score
    texts = [p.text for p in passages]
    score.surprisal(texts, m=m)
    score.drift(texts)
    return passages
