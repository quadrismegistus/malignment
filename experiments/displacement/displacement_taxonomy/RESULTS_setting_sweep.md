# What a coding is worth depends on the setting that produced it

2026-08-19. Eight cells, coded under five model/effort/batching settings, then judged blind.

## The settings

    setting            batched  rel/cell  two-sided/cell  tok/cell  weighted/cell
    opus / unbatched      no       3.00        3.00        46,676     77,948
    opus / medium        yes       2.75        1.12        15,390     25,701
    sonnet / high        yes       2.00        1.12        16,252     16,252
    sonnet / xhigh       yes       1.62        1.62        18,450     18,450
    sonnet / medium      yes       1.50        1.12         6,608      6,608

`weighted` applies the ~1.67x factor Opus carries against the weekly limit.

## A RELATION COUNT IS NOT A RELATION COUNT

Opus/medium's 2.75 is an artefact. **13 of its 22 relations have an empty side** -- it splits one substitution into two one-sided halves, `Genitals expelled to the tail` with no B-words followed by `Face and facial hair ascend` with no A-words. That is one relation described twice, and the schema's own text says a relation names a group on each side.

Counting only two-sided relations, three of the four batched settings collapse to exactly **1.12 per cell**, against 3.00 unbatched with zero one-sided relations.

**This corrects a conclusion drawn two hours earlier**: that batching does not thin Opus. It does. The count disguised it. Sonnet/xhigh is the only batched setting with no one-sided relations at all (0 of 13).

## THE BLIND JUDGMENT: 15 OF 16 FOR UNBATCHED OPUS

Eight cells, each judged twice with the two readings in opposite order, unlabelled, with the word table present. Position bias is ruled out by the design: judges said "one" when Opus was first and "two" when Opus was second.

    verdict                  opus/unbatched 15   sonnet/xhigh 1
    supported relations      opus 1.88           sonnet 1.19
    over-read relations      opus 1.12           sonnet 0.44
    one-sided relations      opus 0.00           sonnet 0.00

**The reason was coverage, never accuracy.** Every judge that gave one said so:

> it accounts for more of the table with genuinely distinct groups on both sides
> it accounts for nearly every word on the table and gives the largest movement in it a relation of its own, whereas Reading One states a single hedged relation that is true but leaves the table's biggest facts unremarked

And judges twice praised the losing reading for being *honest in grading itself low*. **The cheaper setting is more careful and less complete.** That is the opposite of what a cost-quality tradeoff is usually assumed to look like, and it is the finding.

## What the judges caught that the metrics did not

Three independent judges found the same over-read in Opus's third relation on the Llama stroking cell: `hard` (13->126) and `erect` (19->129) set against `long` (20->13), where *the entire B side rests on a single word shifting seven ranks, trivial beside the +55 to +116 shifts elsewhere*. Opus had marked that relation `low` itself, so per-relation confidence would have filtered it.

And the `missed` field found things **neither** reading named:

- *Neither reading names `own` (6->16), the one word on the A side that is not an object at all but a possessive marker: A keeps the hand on the speaker's own body as a matter of grammar, not just of anatomy.*
- *Neither says the head of the distribution does not move at all: `fire` is rank 1 under both conditions, `terminate` 2->3, `take` 3->2 -- the same three words lead in both and the entire shift happens below them.*

The second is a real finding about the union frame that 145 codings did not surface.

## THE CONFOUND THIS CREATES, AND IT IS NOT LOCAL TO THIS FOLDER

Completeness is a property of the production setting. So **any comparison between codings made under different settings is measuring the settings as much as the raters.** An agreement number computed across a setting boundary is not an agreement number.

This is the sharper form of the distinction already booked in `RESULTS_interrater.md`:

    a single coding is a RELIABLE guide to which words carry a difference
    an UNVALIDATED guide to what the difference is
    and a guide whose COMPLETENESS depends on the setting that produced it

Everything in this folder was produced under one setting per instrument, so nothing here is affected. Whether that holds elsewhere in the campaign is not checkable from here.

## Recommendation

**Unbatched Opus for anything quoted or harmonised**, because an unnamed relation cannot be harmonised while an over-read one gets marked `low` and filtered -- so completeness is the property a corpus needs and conservatism is the property a headline needs.

**Sonnet/xhigh if cost forces batching**, never Opus/medium: at 18,450 against 15,390 tokens per cell it is the only batched setting buying whole relations rather than halves.

**And assert at ingest that a relation has both sides.** One check, catches the entire Opus/medium inflation, and no close reading required.
