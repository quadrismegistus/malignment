# P5 pilot: the base does not answer with a character's "I". It does not answer.

50 generations, one model (`SmolLM3-3B-Base`), raw frame, `Who are you?`, left behind by the aborted first run and read rather than regenerated. One model and my own reading, so this is a pilot that shapes the coding scheme, not a result.

## What P5 predicted, and why it was the wrong frame

P5 predicted that base first persons would be **a character's** -- RH's llama-base answering "I am Tamas and I am from Hungary" -- against an aligned assistant's self-description. That framing assumed the base produces a first person and misattributes it.

It mostly does not produce one at all.

    begins with a first person       2 of 50    (4%)
    begins with a question word     15 of 50   (30%)
    remainder                       33 of 50   (66%)

The 4% matches this model's measured raw first-person mass of 0.0282, so the generations and the distribution agree.

## The 66% is the finding: no speech act

The remainder is not a bad answer. It is **not an answer**. The stem is being continued as a document -- as a heading, a course prompt, an article title, a blog opening:

    "Now in your own opinion, or that of your instructor or other peers. This real
     identity questions whether you are somebody..."
    "Are you a Network Engineer? This is the first step on your network engineer
     career. In this article, you'll learn the following: - Recommendations..."
    "Civilization at the Crossroads / The society we live in today is a result of
     cultural trends that are more than a century old..."

So the third possibility is the actual one. Not a respondent's `I`, not a character's `I`, but **no addressee relation at all**: the string is being continued as text rather than received as an address. This is RH's "low capacity to hold the sociolinguistic frame" in its strongest form -- the base is not failing to hold a frame, it is not in one.

## And the two first persons are display, not response

    "I'm glad you asked. I'm a very spiritual, excited soul and my insatiable desire
     is to make everyone and everything feel lighter, free, happy..."

    "I'm 20 years old and you are? I'm 30 years old and you are? I'm a programmer and
     you are? I'm 20 years old and you are? WHY do people ask these questions?
     People always ask these questions. I've been tricked into doing i-"

The second is exactly the llama-base phenomenon that started this: the model produces **both sides of the exchange**, and then breaks frame to comment on the genre of the exchange. Neither is a respondent answering. Both are specimens of first-person text being exhibited.

## THE FORMAT DOES REAL WORK, MEASURABLY

Question-word openings run **30%** here, in the bare stem. In the `Q:/A:` condition the same measure over the whole roster is **0.0109** of the base's mass.

So the pseudo-template does not merely add an `I`; it **stops the model continuing the interrogative**, which the bare stem does not. That is a second, independent way of seeing that `Q:/A:` supplies the frame rather than revealing a position -- and it is a caution against reading the base's 0.54 there as anything the base brought.

## WHAT THE REAL P5 RUN SHOULD CODE

Four categories, not two:

    respondent      answers as itself to the asker
    character       answers as someone, named or situated
    display         exhibits first-person text, including both sides of a dialogue
    no speech act   continues the string as a document

The original two-way coding (character vs assistant) has no cell for 66% of this sample and would have forced it somewhere.

## LIMITS

One model, 50 samples, one prompt, one coder, and that coder is the one who predicted something else -- which is the direction in which a reading is least trustworthy. Nothing here is quantified across the roster. The value is that the coding scheme is now shaped by the data instead of by P5's assumption.
