# Figure 3 — candidate pole words

Fourteen scales: the scatter's eighteen minus the four `_absz` spread scales. Poles are the scale's own ends, **low left, high right**, unreoriented — so the side of every marker on the plate is a result.

A word enters only if `words_long_v4` records it MOVING on an endpoint lineage (riser or faller, content words, >= 3 cells): a pole naming a word alignment never touched would illustrate the scale and not the finding. `n` is how many cells moved it.

Lexicon scales carry a context-free rating per word type. The six `v6:` scales are rated per (prompt, word), so a word's value is the mean over the frames it was rated in and `f` is how many.

**Floors** (paper-claude): every candidate has moved in at least 50 cells, and on the `v6:` scales has been rated in at least 5 frames — ranking by value alone put words rated once at the head of a pole. Non-words are excluded by a `wordfreq` membership test, applied to every list rather than to the two that were noticed.

## no harm  <->  bodily harm

`k_bodily_harm`, 3109 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 5.00 at the cut), ranked within that by how often the word moved.

- **no harm** (low end) — then (1.0, n=31720), said (1.0, n=31454), put (1.0, n=27917), made (1.0, n=24043), took (1.0, n=23916), told (1.0, n=23247), began (1.0, n=21972), went (1.0, n=21814), asked (1.0, n=21189), gave (1.0, n=20052), started (1.0, n=19918), left (1.0, n=19779), let (1.0, n=18330), got (1.0, n=17180)
- **bodily harm** (high end) — kill (7.0, n=4213), killed (7.0, n=3561), die (7.0, n=2947), stabbed (7.0, n=1811), shoot (6.0, n=1616), slashed (6.0, n=968), died (6.0, n=953), strangle (7.0, n=890), murder (7.0, n=673), trampled (6.0, n=621), raped (6.0, n=536), choke (6.0, n=507), hanging (7.0, n=462), rape (7.0, n=440)

## unmarked  <->  transgressive

`k_transgressiveness`, 3109 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 5.00 at the cut), ranked within that by how often the word moved.

- **unmarked** (low end) — then (1.0, n=31720), said (1.0, n=31454), put (1.0, n=27917), made (1.0, n=24043), took (1.0, n=23916), told (1.0, n=23247), began (1.0, n=21972), went (1.0, n=21814), asked (1.0, n=21189), gave (1.0, n=20052), started (1.0, n=19918), left (1.0, n=19779), let (1.0, n=18330), got (1.0, n=17180)
- **transgressive** (high end) — kill (6.0, n=4213), stole (6.0, n=3745), killed (6.0, n=3561), stabbed (6.0, n=1811), strangle (6.0, n=890), murder (7.0, n=673), raped (7.0, n=536), lie (5.0, n=497), violated (6.0, n=476), threaten (5.0, n=475), hanging (5.0, n=462), steal (6.0, n=455), rape (7.0, n=440), desecrated (6.0, n=434)

## abstract  <->  concrete

`k_concreteness`, 3109 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 7.00 at the cut), ranked within that by how often the word moved.

- **abstract** (low end) — then (1.0, n=31720), said (1.0, n=31454), told (1.0, n=23247), began (1.0, n=21972), went (1.0, n=21814), let (1.0, n=18330), got (1.0, n=17180), get (1.0, n=12664), also (1.0, n=10863), now (1.0, n=10559), just (1.0, n=9861), know (1.0, n=8200), never (1.0, n=6724), thought (1.0, n=5580)
- **concrete** (high end) — needle (7.0, n=63), horse (7.0, n=61), carrots (7.0, n=61), tattoo (7.0, n=61), concrete (7.0, n=61), field (7.0, n=61), sleeve (7.0, n=61), dock (7.0, n=60), plants (7.0, n=60), scarf (7.0, n=60), shore (7.0, n=60), headphones (7.0, n=59), tail (7.0, n=59), revolver (7.0, n=59)

## low register  <->  high register

`k_register_level`, 3109 rated movers. Ratings run 1.00 to 6.00; each pole is the 60 most extreme by rating (2.00 and 5.00 at the cut), ranked within that by how often the word moved.

- **low register** (low end) — thought (2.0, n=5580), so (1.0, n=4308), smashed (2.0, n=4052), lay (2.0, n=3143), wait (1.0, n=3102), lit (2.0, n=2974), shut (1.0, n=2264), very (2.0, n=1829), yanked (2.0, n=1542), question (2.0, n=1338), request (2.0, n=1335), fuck (1.0, n=1238), requested (2.0, n=1216), submitted (1.0, n=1138)
- **high register** (high end) — therefore (6.0, n=1099), subsequently (6.0, n=273), invoked (6.0, n=123), Therefore (6.0, n=114), honored (5.0, n=89), parole (5.0, n=87), detained (5.0, n=86), disposed (5.0, n=85), bosom (5.0, n=83), automate (5.0, n=83), cite (5.0, n=83), prescription (5.0, n=81), initiated (5.0, n=81), concealed (5.0, n=81)

## not vulgar  <->  vulgar

`k_vulgarity`, 3109 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 2.00 at the cut), ranked within that by how often the word moved.

- **not vulgar** (low end) — then (1.0, n=31720), said (1.0, n=31454), put (1.0, n=27917), made (1.0, n=24043), took (1.0, n=23916), told (1.0, n=23247), began (1.0, n=21972), went (1.0, n=21814), asked (1.0, n=21189), gave (1.0, n=20052), started (1.0, n=19918), left (1.0, n=19779), let (1.0, n=18330), got (1.0, n=17180)
- **vulgar** (high end) — fuck (7.0, n=1238), cock (7.0, n=393), penis (3.0, n=358), dick (5.0, n=347), smack (2.0, n=331), fucked (7.0, n=327), masturbate (2.0, n=306), fondle (2.0, n=294), curse (3.0, n=286), nipples (2.0, n=278), cocked (4.0, n=257), crotch (2.0, n=255), whacked (2.0, n=254), nipple (2.0, n=253)

## calm  <->  aroused

`warriner_arousal`, 2221 rated movers. Ratings run 1.67 to 7.60; each pole is the 60 most extreme by rating (2.67 and 6.33 at the cut), ranked within that by how often the word moved.

- **calm** (low end) — back (2.6, n=3602), glanced (2.6, n=3540), mention (2.6, n=3399), paused (2.6, n=1567), rested (2.3, n=1390), counted (2.3, n=1265), ground (2.4, n=772), emptied (2.2, n=735), quiet (1.9, n=700), mentioned (2.6, n=697), grow (2.6, n=500), shirt (2.3, n=492), study (2.5, n=458), count (2.3, n=333)
- **aroused** (high end) — laughed (6.6, n=5133), kill (6.8, n=4213), killed (6.8, n=3561), fight (6.3, n=3536), screamed (6.7, n=3445), die (6.9, n=2947), shot (6.5, n=2914), scream (6.7, n=2723), attack (7.0, n=1507), argue (6.7, n=1497), laugh (6.6, n=1336), fuck (7.1, n=1238), attacked (7.0, n=1168), died (6.9, n=953)

## unpleasant  <->  pleasant

`warriner_valence`, 2221 rated movers. Ratings run 1.40 to 8.48; each pole is the 60 most extreme by rating (2.33 and 7.56 at the cut), ranked within that by how often the word moved.

- **unpleasant** (low end) — kill (1.8, n=4213), killed (1.8, n=3561), sue (2.2, n=3469), die (1.7, n=2947), attack (2.0, n=1507), attacked (2.0, n=1168), died (1.7, n=953), failed (2.3, n=785), hate (2.0, n=773), suffer (2.0, n=689), murder (1.5, n=673), vomit (2.0, n=640), steal (2.2, n=455), rape (1.5, n=440)
- **pleasant** (high end) — smiled (7.9, n=9170), give (7.7, n=8968), kissed (7.8, n=5139), live (8.0, n=2637), grinned (7.7, n=2430), kiss (7.8, n=1690), love (8.0, n=1401), rested (7.9, n=1390), create (7.9, n=1389), hugged (8.2, n=1333), thanked (7.8, n=1026), happy (8.5, n=896), created (7.9, n=892), thank (7.8, n=848)

## submissive  <->  dominant

`warriner_dominance`, 2221 rated movers. Ratings run 2.43 to 7.86; each pole is the 60 most extreme by rating (3.32 and 7.00 at the cut), ranked within that by how often the word moved.

- **submissive** (low end) — threatened (3.3, n=4730), die (3.3, n=2947), cry (2.6, n=2747), strike (3.3, n=1070), died (3.3, n=953), fear (3.3, n=939), terminate (3.2, n=739), hissed (3.3, n=738), suffer (3.3, n=689), suspect (3.2, n=671), sob (3.3, n=577), crashed (3.3, n=532), violated (2.9, n=476), threaten (3.3, n=475)
- **dominant** (high end) — smiled (7.7, n=9170), laughed (7.4, n=5133), eat (7.3, n=2090), prepare (7.3, n=1695), laugh (7.4, n=1336), win (7.9, n=969), happy (7.2, n=896), friendly (7.6, n=706), safe (7.2, n=650), kind (7.6, n=626), safer (7.2, n=615), polite (7.4, n=577), respect (7.3, n=468), approve (7.3, n=428)

## does not fit  <->  fits the frame

`v6:fit`, 2050 rated movers. Ratings run 3.73 to 7.00; each pole is the 60 most extreme by rating (4.83 and 7.00 at the cut), ranked within that by how often the word moved.

- **does not fit** (low end) — gave (4.7, n=20052, f=837), get (4.4, n=12664, f=225), take (4.6, n=12119, f=337), called (4.3, n=11907, f=615), make (4.2, n=10734, f=240), give (4.6, n=8968, f=349), returned (4.8, n=7447, f=353), came (4.0, n=6320, f=228), find (4.7, n=5907, f=164), use (4.6, n=5259, f=151), add (4.3, n=3874, f=54), received (4.6, n=3156, f=91), turn (4.7, n=2822, f=158), caused (4.5, n=2706, f=114)
- **fits the frame** (high end) — whip (7.0, n=113, f=8), breakfast (7.0, n=113, f=5), chatted (7.0, n=113, f=6), chucked (7.0, n=110, f=5), vagina (7.0, n=110, f=7), manhood (7.0, n=108, f=6), betray (7.0, n=108, f=6), clung (7.0, n=107, f=7), slump (7.0, n=106, f=6), abdomen (7.0, n=104, f=7), stumble (7.0, n=103, f=6), eliminate (7.0, n=102, f=5), relaxed (7.0, n=102, f=5), sick (7.0, n=102, f=5)

## undirected  <->  directed

`v6:directedness`, 2050 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 7.00 at the cut), ranked within that by how often the word moved.

- **undirected** (low end) — never (1.0, n=6724, f=30), noticed (1.0, n=4529, f=182), didn (1.0, n=3159, f=10), prayed (1.0, n=3030, f=139), spent (1.0, n=2859, f=109), probably (1.0, n=2730, f=6), note (1.0, n=2435, f=18), signed (1.0, n=2244, f=90), knew (1.0, n=1891, f=87), pocketed (1.0, n=1676, f=54), recited (1.0, n=1666, f=80), drank (1.0, n=1658, f=62), noted (1.0, n=1652, f=73), became (1.0, n=1604, f=49)
- **directed** (high end) — strangled (7.0, n=322, f=13), scolded (7.0, n=320, f=13), sued (7.0, n=297, f=12), fondle (7.0, n=294, f=13), hug (7.0, n=288, f=14), assaulted (7.0, n=286, f=14), handcuffed (7.0, n=286, f=14), please (7.0, n=279, f=20), harass (7.0, n=274, f=42), rob (7.0, n=273, f=23), assault (7.0, n=252, f=25), abuse (7.0, n=249, f=28), forgive (7.0, n=217, f=12), tease (7.0, n=212, f=13)

## does not improve  <->  makes better

`v6:makes_better`, 2050 rated movers. Ratings run 1.00 to 6.25; each pole is the 60 most extreme by rating (1.00 and 4.86 at the cut), ranked within that by how often the word moved.

- **does not improve** (low end) — stole (1.0, n=3745, f=118), killed (1.0, n=3561, f=178), die (1.0, n=2947, f=121), hurt (1.0, n=1692, f=72), destroyed (1.0, n=1523, f=81), cursed (1.0, n=1513, f=92), attack (1.0, n=1507, f=125), spat (1.0, n=1432, f=8), stormed (1.0, n=1363, f=82), destroy (1.0, n=1273, f=59), punch (1.0, n=1197, f=60), glared (1.0, n=1004, f=61), strangle (1.0, n=890, f=44), spit (1.0, n=867, f=27)
- **makes better** (high end) — help (5.7, n=2592, f=181), love (5.1, n=1401, f=69), hugged (5.1, n=1333, f=70), save (6.1, n=1097, f=56), apologized (4.9, n=1085, f=51), hope (5.4, n=1018, f=7), protect (5.6, n=1018, f=59), happy (5.4, n=896, f=45), thank (5.6, n=848, f=15), nice (5.5, n=769, f=31), free (5.4, n=732, f=38), friendly (5.9, n=706, f=24), safe (6.0, n=650, f=24), encouraged (4.9, n=646, f=22)

## does not worsen  <->  makes worse

`v6:makes_worse`, 2050 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 5.98 at the cut), ranked within that by how often the word moved.

- **does not worsen** (low end) — consult (1.0, n=1477, f=11), like (1.0, n=1316, f=5), clean (1.0, n=1080, f=97), first (1.0, n=926, f=5), happy (1.0, n=896, f=45), thank (1.0, n=848, f=15), nice (1.0, n=769, f=31), free (1.0, n=732, f=38), friendly (1.0, n=706, f=24), safe (1.0, n=650, f=24), safer (1.0, n=615, f=24), chat (1.0, n=592, f=76), polite (1.0, n=577, f=24), smiling (1.0, n=529, f=30)
- **makes worse** (high end) — beat (6.0, n=4256, f=204), kill (7.0, n=4213, f=202), killed (7.0, n=3561, f=178), die (6.9, n=2947, f=121), shot (6.4, n=2914, f=121), punched (6.0, n=2476, f=110), fire (6.0, n=1943, f=75), stabbed (6.9, n=1811, f=74), shoot (6.9, n=1616, f=124), attack (6.6, n=1507, f=125), destroy (6.1, n=1273, f=59), attacked (6.4, n=1168, f=72), died (6.8, n=953, f=49), burn (6.1, n=898, f=47)

## charged  <->  mundane

`v6:mundanity`, 2050 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.67 and 6.00 at the cut), ranked within that by how often the word moved.

- **charged** (low end) — kill (1.0, n=4213, f=202), killed (1.1, n=3561, f=178), die (1.1, n=2947, f=121), shot (1.4, n=2914, f=121), stabbed (1.0, n=1811, f=74), shoot (1.1, n=1616, f=124), attack (1.4, n=1507, f=125), destroy (1.5, n=1273, f=59), attacked (1.5, n=1168, f=72), slashed (1.6, n=968, f=40), died (1.1, n=953, f=49), burn (1.6, n=898, f=47), strangle (1.0, n=890, f=44), stab (1.0, n=799, f=43)
- **mundane** (high end) — work (6.0, n=3349, f=192), out (6.7, n=1398, f=31), sit (6.6, n=1354, f=111), clean (6.6, n=1080, f=97), drink (6.2, n=810, f=79), nice (6.2, n=769, f=31), together (6.6, n=759, f=27), update (6.2, n=721, f=8), quiet (6.5, n=700, f=28), late (6.8, n=695, f=29), outside (6.6, n=646, f=29), around (6.5, n=630, f=25), sitting (6.6, n=630, f=44), chat (7.0, n=592, f=76)

## silent  <->  vocalized

`v6:vocalisation`, 2050 rated movers. Ratings run 1.00 to 7.00; each pole is the 60 most extreme by rating (1.00 and 6.90 at the cut), ranked within that by how often the word moved.

- **silent** (low end) — pulled (1.0, n=15132, f=633), sat (1.0, n=12161, f=565), felt (1.0, n=11035, f=519), saw (1.0, n=9593, f=397), stared (1.0, n=8034, f=397), stepped (1.0, n=7360, f=385), grabbed (1.0, n=6507, f=338), tossed (1.0, n=6335, f=291), headed (1.0, n=6115, f=269), leaned (1.0, n=5923, f=304), thought (1.0, n=5580, f=264), quickly (1.0, n=5255, f=52), shoved (1.0, n=5162, f=251), kicked (1.0, n=4669, f=246)
- **vocalized** (high end) — said (7.0, n=31454, f=1050), told (6.9, n=23247, f=861), whispered (7.0, n=9203, f=403), tell (6.9, n=7827, f=285), say (6.9, n=7307, f=202), shouted (7.0, n=6825, f=289), talk (7.0, n=5809, f=220), yelled (7.0, n=4705, f=218), speak (7.0, n=4658, f=193), spoke (7.0, n=4033, f=206), screamed (7.0, n=3445, f=170), scream (7.0, n=2723, f=172), declared (6.9, n=1907, f=107), complain (6.9, n=1752, f=58)

