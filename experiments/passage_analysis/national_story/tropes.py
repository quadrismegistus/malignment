"""Rettberg's six plot tropes, as a measured instrument.

    from tropes import annotate
    a = annotate(story_text)
    a.votes()                 # {trope: 0-3}, how many independent sets fired
    a.present()               # {trope: bool}, majority of three
    a.counts()                # {trope: n hits}
    a.hits                    # [Hit], each with its sentence and character span

## WHERE THE PATTERNS CAME FROM, AND WHY THERE ARE THREE SETS

Rettberg & Wigers (2025) read four countries closely and describe a recurring
skeleton: a protagonist RETURNS to a SMALLTOWN, meets a SPIRIT, faces a THREAT,
ORGANISES the community, and the village is RENEWED.

Three agents were each given a DISJOINT sample of 12 stories from their released
corpus -- Norway/USA/Ghana, India/Israel/Palestine, Japan/Nigeria/Brazil -- and
each wrote detectors independently, without seeing the others' stories or
patterns. Keeping all three sets and voting is the point: one agent's threshold
does not decide, and disagreement between three readers who never met is
evidence about the trope rather than about the reader.

## VALIDATED ON HELD-OUT DATA, WHICH IS WHY THE WEAK ONES ARE NAMED

1,500 stories none of the agents saw, agreement on WHICH stories fire:

    SMALLTOWN   Jaccard 0.91-0.95   near-identical across the three sets
    SPIRIT              0.76-0.77
    ORGANISE            0.72-0.75
    RENEWAL             0.69-0.82
    RETURN              0.69-0.76
    THREAT              0.51-0.69   **DO NOT TRUST THIS ONE ALONE**

`THREAT` bundles developers, extreme weather and "imbalance between people and
nature" into one label, and the three sets agree least about it. Report it with
its disagreement or not at all.

Two of ten candidate phrases from the same exercise FAILED held-out validation
("time seemed to stand still" looked recurrent in 12 stories and is 1.7%
corpus-wide), so the surviving patterns are survivors, not impressions.

## WHAT THE INSTRUMENT SAYS ABOUT THE PAPER

Consensus over 1,416 stories across all 236 countries:

    RETURN 40.7%  SMALLTOWN 73.2%  SPIRIT 75.6%
    THREAT 42.1%  ORGANISE  59.5%  RENEWAL 78.2%

    all six tropes    8.5% of stories
    five or six      33.7%
    four or more     61.9%      <- mode is 4/6

**The skeleton is a family resemblance, not a template.** Most stories draw four
of six from a shared stock, but which four varies -- and RETURN, the first beat
of the paper's own diagram, is in fewer than half.

## TWO LIMITS THAT ARE NOT NEGOTIABLE

**English only.** The five countries gpt-4o-mini wrote in the local language
(DE, ES, FR, PT, TR) score 0.00 on every trope by construction. That is the
instrument failing, not those stories lacking plots. Filter by language first.

**A count is not a vote.** A single source matching five times is one vote and
five hits. `votes()` is the measurement; `counts()` describes density.
"""

import re
from dataclasses import dataclass, field

#: independently authored; do not merge the sets
TROPES_A = {
    'RETURN': [
        '\\b(?:return(?:ed|ing|s)?|came back|come back|coming back|went back|going back|head(?:ed|ing) back|made (?:her|his|their) way back|drove back|journey(?:ed|ing)? back|find (?:her|his|their) way back)\\b[^.!?\\n]{0,50}\\b(?:home|hometown|home town|village|town|farm|homestead|island|valley|birthplace|roots)\\b',
        '\\b(?:return(?:ed|ing|s)?|came|come|coming|went|going|back|journey(?:ed|ing)?|sent|drawn|call(?:ed|ing))\\s+home\\b',
        '\\bhome(?:coming|ward)\\b',
        '\\b(?:thought|idea|prospect|decision|time)\\s+(?:had come\\s+)?(?:of|to)\\s+(?:return\\w+|go(?:ing)? back|com(?:e|ing) back|com(?:e|ing) home|mov(?:e|ing) back)\\b',
        '\\b(?:return\\w*|came back|coming back|going back|back)\\b[^.!?\\n]{0,45}\\b(?:nostalgia|after (?:all |so many |ten |twenty |thirty |five )?years|for the first time in years|childhood home|old memories)\\b',
        '\\b(?:childhood|family|ancestral)\\s+home\\b',
        '\\b(?:town|village|house|home|street|streets|place|farm)\\s+where\\s+(?:she|he|they|I)\\s+(?:had\\s+)?(?:grew|grown)\\s+up\\b',
        '\\b(?:mov(?:ed|ing)|com(?:e|ing)|settl(?:ed|ing))\\s+back\\s+(?:to|home)\\b',
        "\\b(?:had ?n[o']?t|has ?n[o']?t|hadn’t|hasn’t|never|not)\\s+(?:been\\s+)?(?:back|returned|set foot|seen (?:the|her|his) (?:village|town|home))\\b",
        '\\b(?:after|for)\\s+(?:\\w+\\s+){0,3}(?:years|decades|a decade|a lifetime|so long)\\s+(?:away|abroad|in the city|of absence|gone)\\b',
        '\\bfirst time\\s+(?:in\\s+)?(?:\\w+\\s+){0,3}years\\b',
        '\\b(?:left|leaving|fled|fleeing|escap(?:ed|ing)|abandon(?:ed|ing)|quit|traded|turn(?:ed|ing) (?:her|his|their) back on)\\b[^.!?\\n]{0,40}\\b(?:the city|city life|the capital|the metropolis|urban life)\\b',
        '\\b(?:weary|tired|sick|exhausted|worn out)\\s+of\\b[^.!?\\n]{0,30}\\b(?:city|urban|corporate|office)\\b',
        '\\bfrom\\s+the\\s+(?:big\\s+)?city\\b[^.!?\\n]{0,40}\\b(?:arriv|return|came|back|village|town)',
    ],
    'SMALLTOWN': [
        '\\b(?:small|tiny|little|sleepy|quiet|remote|quaint|humble|modest|isolated|secluded|forgotten|obscure|rural|coastal|mountain|fishing|farming|mining|riverside)\\s+(?:\\w+\\s+){0,2}(?:village|town|hamlet|settlement|community|township|outpost)\\b',
        '\\b(?:village|town|hamlet|settlement)\\s+(?:of|called|named)\\s+(?-i:[A-Z][a-z])',
        '\\b(?:nestled|tucked|perched|situated|hidden|cradled|clung|clinging|sprawled|huddled)\\b[^.!?\\n]{0,60}\\b(?:village|town|hamlet|valley|coast|hills|mountains|river|plains|forest)\\b',
        '\\b(?:dying|dwindling|declining|shrinking|fading|abandoned|deserted|emptying|forgotten|crumbling|struggling|impoverished)\\s+(?:\\w+\\s+){0,2}(?:village|town|community|settlement)\\b',
        '\\b(?:village|town|community|population)\\b[^.!?\\n]{0,40}\\b(?:dwindl\\w+|declin\\w+|dying out|emptied|left for the city|young people (?:had )?left|shut(?:ting)? down|closed for good)\\b',
        '\\bwhere time (?:seemed to |appeared to )?(?:stood|stand|had stood|moved slowly|passed slowly)\\b',
        '\\b(?:everyone|everybody)\\s+(?:knew|knows)\\s+(?:everyone|everybody|each other)\\b',
        '\\bvillagers\\b',
    ],
    'SPIRIT': [
        '\\bspirits?\\s+of\\s+(?:the\\s+|our\\s+|their\\s+)?(?:forest|land|water|waters|river|sea|mountain|mountains|valley|earth|trees?|place|village|ancestors?|dead|past)\\b',
        '\\b(?:ancient|ancestral|forest|river|mountain|guardian|protective|restless|watchful)\\s+spirits?\\b',
        '\\bspirits?\\b[^.!?\\n]{0,30}\\b(?:watch(?:ed|es|ing)? over|guard(?:ed|s|ing)?|protect(?:ed|s|ing)?|dwell(?:ed|s|ing)?|resid(?:ed|es|ing)|linger(?:ed|s|ing)?|roam(?:ed|s|ing)?)\\b',
        '\\bguardian\\s+(?:spirit|of the|of our|of these|of this)\\b',
        '\\bancestors?\\b[^.!?\\n]{0,40}\\b(?:spoke|speak|whisper\\w*|watch\\w*|guide[ds]?|guiding|bless\\w*|call(?:ed|ing)?|answer\\w*|walk\\w*)\\b',
        '\\b(?:honou?r|appease|invoke|summon|call upon|commune with|offering[s]? to|pray(?:ed|ing)? to)\\w*\\s+(?:the\\s+)?(?:ancestors?|spirits?|gods?|deity|deities)\\b',
        '\\b(?:troll|trolls|elf|elves|fairy|fairies|nymph|nymphs|djinn|jinn|deity|demigod|goddess|shaman|sorcerer|sorceress|witch|dragon|apparition|wraith|revenant|water spirit|forest spirit)\\b',
        '\\bghost(?:s|ly)?\\s+(?:of\\s+(?-i:[A-Z])|appeared|haunt\\w*|figure|woman|man|child|stood|spoke|drifted)\\b',
        '\\b(?:supernatural|otherworldly|ethereal|mystical|spectral|enchanted|magical)\\s+(?:being|beings|creature|creatures|figure|figures|presence|force|voice)\\b',
        '\\b(?:the\\s+)?(?:tree|trees|forest|woods|river|wind|mountain|land|stones?)\\s+(?:itself\\s+|themselves\\s+)?(?:seemed to\\s+)?(?:spoke|speak|whispered|whispers|sang|sings|called|calls|answered|remembers?|remembered)\\b',
        '\\b(?:ancient|old|mysterious|strange|weathered|dusty|forgotten|sacred|worn|battered|carved)\\s+(?:\\w+\\s+){0,2}(?:amulet|talisman|artefact|artifact|scroll|map|trunk|chest|casket|stone|crystal|pendant|necklace|charm|manuscript|journal|key|mirror|locket|drum|mask|carving|idol|totem|shrine)\\b',
        '\\b(?:amulet|talisman|totem|idol|shrine)\\b',
        '\\b(?:glow(?:ed|ing|s)?|pulsed?|pulsing|shimmer(?:ed|ing|s)?|hummed?|thrummed?|vibrat(?:ed|ing))\\s+with\\s+(?:a\\s+|an\\s+)?(?:\\w+\\s+){0,2}(?:energy|power|magic|light of)\\b',
    ],
    'THREAT': [
        '\\b(?:developers?|investors?|speculators?|contractors?|corporation|corporations|conglomerate|the company|mining company|logging company|oil company|construction firm|outsiders?|foreign investor)\\b[^.!?\\n]{0,70}\\b(?:land|forest|village|town|site|coast|valley|river|build|buy|bought|purchase|clear|develop|exploit|acquire|bulldoz|drill|mine|resort|hotel|factory|plant|mall)\\b',
        '\\b(?:mining|logging|drilling|fracking|quarry(?:ing)?|deforestation|clear-?cutting|oil palm|strip mine)\\b',
        '\\bplans?\\s+to\\s+(?:build|develop|construct|erect|turn|convert|buy|purchase|clear|level|raze|demolish|drain|dam)\\b',
        '\\b(?:bulldoz\\w+|raz(?:e|ed|ing)|demolish\\w*|tear(?:ing)? down|torn down|pav(?:e|ed|ing) over|wiped? off the map|driven from (?:their|our) land|evict\\w*|displac(?:e|ed|ement) of)\\b',
        '\\b(?:threat\\w*|endanger\\w*|jeopardi[sz]\\w*|imperil\\w*|menac\\w*|loom(?:ed|ing|s)?)\\b[^.!?\\n]{0,50}\\b(?:village|town|community|land|forest|river|way of life|livelihood|heritage|tradition|home|homes|future|harmony|balance|world)\\b',
        '\\b(?:village|town|community|land|forest|heritage|way of life)\\b[^.!?\\n]{0,40}\\b(?:under threat|at risk|in danger|would be lost|about to be lost|might disappear|was disappearing)\\b',
        '\\b(?:factory|mill|mine|cannery|school|station|railway|shop|store|port|harbou?r|clinic|post office)\\b[^.!?\\n]{0,50}\\b(?:clos(?:ed|ing|ure|e for good)|shut(?: down)?|shuttered|bypassed|moved away|laid off|abandoned)\\b',
        '\\b(?:highway|motorway|freeway|bypass|new road)\\b[^.!?\\n]{0,40}\\b(?:bypass\\w*|passed (?:it|them|the town) by|took the traffic|left the town)\\b',
        '\\b(?:drought|famine|hurricane|cyclone|typhoon|earthquake|landslide|mudslide|blizzard|heatwave|erosion|desertification|rising (?:seas?|waters|tides?)|failed harvests?|crop failure|floodwaters|flooding)\\b',
        '(?<!like )\\b(?:wildfires?|bushfires?)\\b',
        '\\b(?:flood|floods|storm|storms|rains?|seas?|winter|fire|drought)\\b[^.!?\\n]{0,40}\\b(?:destroy\\w*|devastat\\w*|ravag\\w*|swept away|washed away|wiped out|tore through|battered|submerg\\w*|ruin(?:ed|ing)?)\\b',
        '\\b(?:fish|crops?|harvests?|rains?|game|soil|wells?|nets?|herds?)\\b[^.!?\\n]{0,40}\\b(?:fail(?:ed|ing|s)?|scarce|scarcer|dwindl\\w+|dried up|drying|wither\\w+|barren|empty|gone|thin(?:ner)?)\\b',
        '\\b(?:balance|harmony)\\b[^.!?\\n]{0,50}\\b(?:broken|shattered|lost|disrupt\\w*|upset|threaten\\w*|restore[ds]?|restoring|tipped)\\b',
        '\\b(?:disrupt\\w*|threaten\\w*|break|broke|broken|breaking|upset|shatter\\w*|destroy\\w*|restor\\w*)\\s+(?:the\\s+|their\\s+|our\\s+|its\\s+)?(?:delicate\\s+)?(?:balance|harmony)\\b',
        '\\bgreed\\b[^.!?\\n]{0,50}\\b(?:land|forest|sea|river|village|town|earth|people)\\b',
        '\\btook?\\s+(?:too much|more than (?:they|we|it) (?:gave|needed|could))\\b',
        '\\btaken more than\\b|\\bforgotten (?:the |their |our )?(?:old ways|balance|respect)\\b|\\bturned (?:their|his|her|its) back on the (?:land|forest|sea|old ways)\\b',
        '\\b(?:foreclos\\w+|repossess\\w+|eviction|debts?|the bank|back taxes|mortgage)\\b[^.!?\\n]{0,50}\\b(?:farm|land|house|home|property|village|boat)\\b',
    ],
    'ORGANISE': [
        '\\borgani[sz]\\w*\\b[^.!?\\n]{0,60}\\b(?:festival|exhibition|gathering|meeting|celebration|protest|demonstration|workshop|workshops|fair|feast|ceremony|concert|market|committee|campaign|petition|event|clean-?up|community|villagers)\\b',
        '\\b(?:held|hold|holding|host(?:ed|ing|s)?|stag(?:ed|ing)|arrang(?:ed|ing)|put on|planned|planning|call(?:ed|ing) for|propos(?:ed|ing)|launch(?:ed|ing))\\s+(?:a|an|the|her|his|their)\\s+(?:\\w+\\s+){0,3}(?:festival|exhibition|gathering|meeting|celebration|feast|fair|ceremony|concert|workshop|protest|demonstration|market|parade|competition|cooperative)\\b',
        '\\b(?:gather(?:ed|ing|s)?|rall(?:y|ied|ying)|unit(?:e|ed|ing)|mobili[sz]\\w+|assembl(?:ed|ing)|summon(?:ed|ing)?|convene[ds]?|convening|brought together|call(?:ed|ing) together|led)\\s+(?:the\\s+|her\\s+|his\\s+|their\\s+|our\\s+|every\\s+)?(?:villagers?|townsfolk|townspeople|community|neighbou?rs|residents|elders|families|people|women|youth|farmers|fishermen)\\b',
        '\\b(?:village|town|community|public|town-?hall)\\s+(?:meeting|assembly|council meeting|gathering|forum)\\b',
        '\\b(?:prepar\\w+|planning|plans|preparations)\\b[^.!?\\n]{0,50}\\b(?:festival|feast|celebration|ceremony|fair|parade)\\b',
        '\\b(?:reviv\\w+|restart\\w+|bring back|brought back|first ever|resurrect\\w+|reinstat\\w+)\\b[^.!?\\n]{0,40}\\b(?:festival|fair|feast|ceremony|tradition|market)\\b',
        '\\bwent door to door\\b|\\bspread the word\\b|\\bsigned? a petition\\b|\\bpetition\\b',
        '\\b(?:leader|organi[sz]er|spokes(?:person|woman|man)|convenor|chair)\\s+of\\s+the\\s+(?:community|village|town|movement|campaign|group)\\b',
    ],
    'RENEWAL': [
        '\\b(?:village|town|community|valley|island|land|harbou?r|market square)\\b[^.!?\\n]{0,40}\\b(?:thrived?|thriving|flourish\\w+|blossom\\w+|bloom(?:ed|ing)|prosper\\w+|revit\\w+|revived?|reborn|renewed|rejuvenat\\w+|came (?:back )?(?:alive|to life)|buzz(?:ed|ing) (?:again|with life))\\b',
        '\\b(?:thrived|flourished|prospered|blossomed|came alive|came back to life)\\b[^.!?\\n]{0,40}\\b(?:village|town|community|land|once (?:again|more))\\b',
        '\\b(?:thrived|flourished|blossomed|prospered|revived|reborn|rejuvenated|renewed|healed|restored)\\b[^.!?\\n]{0,30}\\b(?:once (?:again|more)|again|anew|as (?:it|they) had)\\b',
        '\\b(?:renewed|rekindl\\w+|reawaken\\w+|revived?|reviving|restor\\w+|reclaim\\w+|revitali[sz]\\w+|breathed new life into|kept alive)\\s+(?:a\\s+|the\\s+|their\\s+|its\\s+|her\\s+|his\\s+|our\\s+)?(?:\\w+\\s+){0,2}(?:tradition|traditions|heritage|culture|customs|old ways|community|village|town|land|forest|balance|craft|language|bond)\\b',
        '\\b(?:hope|pride|faith|belief|spirit|spirits|tradition|traditions|heritage|culture|community|village|town|bond)\\b[^.!?\\n]{0,30}\\b(?:renewed|rekindled|reawakened|revived|restored|revitali[sz]ed|reborn)\\b',
        '\\b(?:heritage|tradition|traditions|culture|customs|old ways|craft|legacy)\\b[^.!?\\n]{0,50}\\b(?:preserv\\w+|honou?red|celebrated|kept alive|alive again|intact|secured)\\b',
        '\\b(?:preserv\\w+|honou?r(?:ed|ing)?|celebrat\\w+|protect\\w+|reclaim\\w+)\\s+(?:their|our|its|the)\\s+(?:\\w+\\s+){0,2}(?:heritage|tradition|traditions|culture|customs|way of life|old ways|history)\\b',
        '\\b(?:villagers?|townspeople|townsfolk|community|neighbou?rs|people|families)\\b[^.!?\\n]{0,50}\\b(?:united|unity|c[ao]me together|stood together|stood as one|bound together|closer than (?:ever|before)|shoulder to shoulder|hand in hand)\\b',
        '\\b(?:united|unity|togetherness|solidarity)\\b[^.!?\\n]{0,40}\\b(?:village|town|community|villagers|people)\\b',
        '\\b(?:developers?|company|corporation|investors?|project|plans?|threat|mining company)\\b[^.!?\\n]{0,50}\\b(?:withdrew|withdrawn|abandoned|backed (?:down|off|away)|retreated|was (?:halted|stopped|blocked|cancell?ed|shelved)|gave up)\\b',
        '\\b(?:village|town|forest|land|river|valley|community|way of life)\\s+(?:was|had been|were)\\s+(?:saved|spared|protected|preserved)\\b',
        '\\bbalance\\b[^.!?\\n]{0,30}\\brestored\\b|\\brestor\\w+\\s+(?:the\\s+)?balance\\b',
        '\\b(?:visitors?|tourists?|artists?|families|young people)\\b[^.!?\\n]{0,50}\\b(?:began to (?:come|arrive|return)|came from (?:far|all over|miles)|returned to the (?:village|town)|drawn to the (?:village|town))\\b',
    ],
}

#: independently authored; do not merge the sets
TROPES_B = {
    'RETURN': [
        '\\b(?:return(?:ed|ing|s)?|came? back|come back|head(?:ed|ing) back|journey(?:ed)? back|made (?:her|his|their) way back|moved back)\\b[^.!?]{0,60}\\b(?:home|homeland|village|town|farm|valley|island|countryside|birthplace|roots|childhood|ancestral|native|where (?:she|he|they) (?:grew|was|were) )',
        '\\bafter\\b[^.!?]{0,40}\\b(?:years?|decades?|months?)\\b[^.!?]{0,60}\\b(?:return(?:ed|ing)|came back|come home|back home|had left|away)\\b',
        '\\b(?:homecoming|returnee|prodigal)\\b',
        '\\bwelcome (?:back )?home\\b',
        '\\b(?:she|he|they) (?:was|were|had) (?:finally |at last )?(?:back|home) (?:again|for good|at last|to stay)\\b',
        '\\b(?:left|leaving|quit|abandoned|gave up) (?:the |her |his |their )?(?:city|capital|metropolis|university|job|career|apartment)\\b[^.!?]{0,60}\\b(?:for|to return|and returned|to go back|back to)\\b',
        '\\b(?:years|decades) (?:spent )?(?:away|abroad|in the city)\\b',
    ],
    'SMALLTOWN': [
        '\\b(?:small|little|tiny|quaint|sleepy|quiet|remote|humble|modest|isolated|obscure|forgotten|dusty|far-?flung|out-?of-?the-?way) (?:\\w+ ){0,2}(?:village|hamlet|town|township|settlement|community|fishing village|farming village|mountain village|coastal town)\\b',
        '\\b(?:village|hamlet|township) (?:of|named|called)\\b',
        '\\b(?:nestled|tucked|perched|situated|nestling|hidden) (?:away )?(?:between|among|amid|amidst|in|at|beneath|beside|along)\\b[^.!?]{0,80}\\b(?:hills?|mountains?|valley|fields?|forest|river|coast|desert|steppe|plains?|dunes?|cliffs?)\\b',
        '\\b(?:village|town|hamlet|settlement)\\b[^.!?]{0,60}\\b(?:declin(?:e|ing|ed)|dwindl\\w+|fading|forgotten|abandoned|deserted|dying|emptied|left behind|time (?:had )?forgot)',
        '\\b(?:young(?:er)? (?:people|generation|folk|ones)|the youth)\\b[^.!?]{0,60}\\b(?:had )?(?:left|leaving|moved away|drifted away|gone to the cit)',
        '\\b(?:villagers|townsfolk|townspeople|village elders)\\b',
    ],
    'SPIRIT': [
        '\\b(?:spirits?|ghosts?|apparitions?|phantoms?|wraiths?|deit(?:y|ies)|goddess(?:es)?|ancestors?|guardians?)\\b[^.!?]{0,60}\\b(?:appear(?:ed|s|ing)?|emerg(?:ed|ing)|manifest(?:ed)?|spoke|speaks|whisper(?:ed|s|ing)|answer(?:ed)?|watch(?:ed|es|ing)? over|guard(?:ed|s|ing)|protect(?:ed|s|ing)|bless(?:ed|es)|visit(?:ed|s)|call(?:ed|ing) (?:to|out to))\\b',
        '\\b(?:spirit|guardian|keeper|protector|goddess|god)s? of the (?:\\w+ ){0,2}(?:tree|forest|grove|river|mountain|lake|sea|land|valley|well|spring|earth|desert|island)\\b',
        '\\b(?:mystical|mythical|supernatural|otherworldly|ethereal|enchanted|magical|spectral|ghostly|shimmering figure|luminous figure|glowing figure|translucent figure)\\b',
        '\\b(?:legends?|myths?|folklore|the old(?:er)? tales|prophec(?:y|ies))\\b[^.!?]{0,40}\\b(?:spoke|said|told|had it|foretold|warned|claimed|held)\\b',
        '\\bit (?:was|is) said that\\b',
        '\\b(?:ancient|mysterious|strange|curious|peculiar|glowing|weathered|ornate|forgotten|sacred|unmarked) (?:\\w+ ){0,2}(?:stone|amulet|talisman|relic|artifact|artefact|chest|casket|box|key|scroll|manuscript|tablet|locket|medallion|carving|inscription|map|book|lantern|mirror|ring|coin)\\b',
        '\\b(?:the|its|their) (?:whispers?|voice|voices|song|murmur) of the (?:\\w+ ){0,2}(?:tree|trees|forest|wind|river|land|stones?|ancestors?|earth|sea|mountain)\\b',
        '\\b(?:tree|trees|forest|river|wind|stones?|mountain)\\b[^.!?]{0,40}\\b(?:seemed to|began to|would|could) (?:speak|whisper|answer|reply|sing|listen|remember)\\b',
        '\\b(?:offerings?|prayers?|libations?|incense) (?:were |was )?(?:made|left|placed|offered|lit|burned) (?:at|to|beneath|before|for)\\b',
    ],
    'THREAT': [
        '\\b(?:developers?|real ?estate|property (?:company|developer)|luxury (?:resort|hotel|development)|resort|corporation|conglomerate|multinational|investors?|speculators?|mining (?:company|firm|operation)|logging|oil compan|contractors?)\\b',
        '\\bplans? to (?:build|develop|construct|erect|demolish|clear|bulldoze|convert|turn)\\b',
        '\\b(?:bulldozers?|excavators?|heavy machinery|surveyors?|eviction notice|compulsory purchase|land grab)\\b',
        '\\b(?:threaten(?:ed|ing|s)?|endanger(?:ed|ing|s)?|imperil(?:l?ed|ling)?|jeopardi[sz]\\w+|loom(?:ed|ing) over|encroach\\w+ (?:on|upon))\\b[^.!?]{0,60}\\b(?:village|town|land|grove|forest|farm|field|river|home|homes|community|heritage|tradition|way of life|livelihood|existence)\\b',
        '\\b(?:threaten\\w*|endanger\\w*|destroy\\w*|erase\\w*|wipe out)\\b[^.!?]{0,40}\\bway of life\\b',
        '\\b(?:evict(?:ed|ion|ing)?|displac(?:ed|ing|ement)|uproot(?:ed|ing)?|seiz(?:ed|ing|ure)|expropriat\\w+|confiscat\\w+|raz(?:ed|ing)|demolish\\w*) ',
        '\\b(?:drought|famine|flood(?:s|ed|ing|waters)?|deluge|wildfire|bush ?fire|cyclone|typhoon|hurricane|tornado|earthquake|landslide|blizzard|heat ?wave|dust storm|locusts?|blight|erosion|deforestation|desertification|pollution|contaminat\\w+)\\b',
        '\\b(?:crops?|harvest|fields?|wells?|rivers?|soil)\\b[^.!?]{0,40}\\b(?:withered|failed|dried up|dying|barren|poisoned|contaminated)\\b',
        '\\b(?:balance|harmony)\\b[^.!?]{0,40}\\b(?:broken|lost|disturbed|upset|shattered|forgotten|no longer)\\b',
        '\\b(?:a )?(?:slow |gradual |steady )?decline\\b',
        '\\b(?:change|modernity|progress|the world) (?:swept|crept|arrived|came) (?:through|to|over)\\b',
        '\\b(?:trade|crafts?|tradition(?:al \\w+)?|customs?|way of life|business|shop|stall|industry|mill|factory|old \\w+)\\b[^.!?]{0,70}\\b(?:fad(?:e|ed|ing)|dying|died out|disappear\\w+|vanish\\w+|declin\\w+|dwindl\\w+|forgotten|lost|closing|shut down|no longer)\\b',
        '\\b(?:the )?(?:last|only) (?:remaining |surviving )?(?:\\w+ ){0,2}(?:in|of) (?:the )?(?:village|town|region|family|line|valley)\\b',
        '\\b(?:burn(?:ed|t|ing)|destroy(?:ed|ing)|demolish(?:ed|ing)|raz(?:ed|ing)|bulldoz(?:ed|ing)|uproot(?:ed|ing)|shell(?:ed|ing)|bomb(?:ed|ing)|loot(?:ed|ing))\\b[^.!?]{0,40}\\b(?:homes?|houses?|village|town|trees?|groves?|orchards?|fields?|crops?|forest)\\b',
        '\\b(?:homes?|houses?|village|trees?|groves?|fields?|crops?|forest)\\b[^.!?]{0,40}\\b(?:were |was |been )?(?:burned|burnt|destroyed|demolished|razed|bulldozed|uprooted|flattened|swept away|submerged)\\b',
        '\\b(?:war|conflict|occupation|violence|unrest|siege|fighting|raids?)\\b[^.!?]{0,50}\\b(?:plagued|ravaged|torn|raged|engulfed|swept|scarred|loomed|persisted)\\b',
        '\\b(?:outsiders?|strangers?|newcomers?|settlers?|soldiers?|militia|poachers?)\\b[^.!?]{0,60}\\b(?:arriv(?:ed|ing)|came|encroach\\w+|claim(?:ed|ing)|took|seiz\\w+|threaten\\w+|surround\\w+|moved (?:in|closer))\\b',
    ],
    'ORGANISE': [
        '\\b(?:organi[sz]|arrang|coordinat|convene|conven|stag|host|held|hold|plan)\\w*\\b[^.!?]{0,50}\\b(?:festivals?|fairs?|feasts?|celebrations?|ceremon(?:y|ies)|gatherings?|meetings?|assembl(?:y|ies)|workshops?|exhibitions?|markets?|concerts?|competitions?|campaigns?|protests?|rall(?:y|ies)|marches|demonstrations?|petitions?|cooperatives?|committees?|councils?|classes|sessions?|evenings?|nights?)\\b',
        '\\b(?:village|town|community|public|open) (?:hall )?(?:meeting|assembly|gathering|council|forum)\\b',
        '\\btown hall\\b',
        '\\b(?:called|summoned|convened|gathered|gathering)\\b[^.!?]{0,30}\\b(?:a|the) (?:meeting|gathering|assembly|council|crowd)\\b',
        '\\b(?:rall(?:y|ied|ying)|mobili[sz]\\w+|unit(?:ed|ing)|brought together|gathered|enlisted|recruited)\\b[^.!?]{0,40}\\b(?:the )?(?:villagers|townsfolk|townspeople|community|neighbo(?:u)?rs|people of|residents|everyone|elders)\\b',
        '\\b(?:a|the|their|first|annual|the annual) (?:\\w+ ){0,2}(?:festival|fair|feast day|harvest celebration)\\b',
        '\\b(?:peaceful )?(?:protest|demonstration|sit-?in|march|petition|boycott|vigil|blockade)\\b',
        '\\bspread the word\\b',
        '\\b(?:went|going) (?:from )?(?:door to door|house to house)\\b',
    ],
    'RENEWAL': [
        '\\b(?:revitali[sz]\\w+|rejuvenat\\w+|rekindl\\w+|reawaken\\w+|revival|reviv(?:ed|ing)|renewal|renaissance|reborn|rebirth|resurgence|breathed? new life|brought .{0,20}back to life|new lease)\\b',
        '\\b(?:village|town|hamlet|community|square|market|streets?)\\b[^.!?]{0,60}\\b(?:thriv(?:ed|ing|es)|flourish(?:ed|ing|es)|blossom(?:ed|ing)|bloom(?:ed|ing)|prosper(?:ed|ing)|came alive|alive (?:again|with)|buzz(?:ed|ing)|hummed|transformed|healed|restored)\\b',
        '\\brenewed sense of (?:purpose|hope|pride|community|belonging|unity|possibilit)\\b',
        '\\b(?:heritage|traditions?|customs?|crafts?|ancestral \\w+|ancestors.{0,3} \\w+|old ways|stories|wisdom|legacy|memor(?:y|ies)|language|songs?|recipes?)\\b[^.!?]{0,60}\\b(?:preserv\\w+|restor\\w+|reclaim\\w+|reviv\\w+|rediscover\\w+|honou?red|celebrat\\w+|passed (?:down|on)|carried (?:on|forward)|kept alive|live on|would endure)\\b',
        '\\b(?:became|remained|stood as|grew into|turned into|was now) (?:a|the) (?:\\w+ ){0,2}(?:beacon|symbol|model|hub|centre|center|sanctuary|landmark|testament|cornerstone|heart) of\\b',
        '\\b(?:bound|bind|binding|united|uniting|knit(?:ted)?|drawn|brought|held|woven|weaving|standing|stood) (?:\\w+ ){0,5}together\\b[^.!?]{0,40}|\\b(?:villagers|community|town|village|families|neighbo\\w+|people)\\b[^.!?]{0,50}\\b(?:bound|united|uniting|knit(?:ted)?|brought|drawn|stood|standing|came) (?:\\w+ ){0,4}together\\b',
        '\\b(?:for )?generations to come\\b',
        '\\b(?:visitors?|tourists?|people|others|buyers?) (?:came|began to come|travel(?:l?ed)?|flocked|arriv(?:ed|ing))\\b[^.!?]{0,50}\\b(?:to (?:see|learn|witness|visit|hear|buy)|from (?:far|across|all over|neighbo))',
        '\\b(?:next|new|younger|future) generations?\\b[^.!?]{0,60}\\b(?:learn\\w*|carry|inherit\\w*|remember\\w*|taught|teach\\w*|inspir\\w*)\\b',
    ],
}

#: independently authored; do not merge the sets
TROPES_C = {
    'RETURN': [
        '\\breturn(?:s|ed|ing)?\\s+home\\b',
        "\\bhome[\\u2019']?coming\\b",
        '\\b(?:return(?:s|ed|ing)?|came\\s+back|come\\s+back|coming\\s+back|went\\s+back|go(?:es|ing)?\\s+back|gone\\s+back|made\\s+(?:her|his|their|my|its)\\s+way\\s+back)\\b[^.\\n]{0,45}\\b(?:home|homeland|hometown|home\\s?town|home\\s+village|native\\s+\\w+|birthplace|childhood\\s+\\w+|ancestral\\s+\\w+|old\\s+village|the\\s+village|her\\s+village|his\\s+village|their\\s+village|the\\s+town|the\\s+island)\\b',
        '\\bback\\s+(?:to|in|at)\\s+(?:the|her|his|their|my|our)\\s+(?:village|hometown|home\\s?town|home|homeland|farm|island|roots|birthplace|childhood|ancestral|old\\s+\\w+)\\b',
        '\\b(?:it\\s+had\\s+been|it\\s+has\\s+been|after)\\s+(?:almost\\s+|nearly\\s+|over\\s+|more\\s+than\\s+)?(?:\\w+|\\d+)\\s+(?:long\\s+)?years?\\s+(?:since|in|away|abroad|of\\s+absence)\\b',
        '\\b(?:had\\s+)?(?:left|departed|fled|moved\\s+away\\s+from|abandoned)\\b[^.\\n]{0,45}\\b(?:years?\\s+(?:ago|earlier|before)|as\\s+a\\s+(?:young|teenager|child))\\b',
        '\\b(?:set|setting)\\s+foot\\b[^.\\n]{0,40}\\b(?:again|since|home|village|in\\s+years)\\b',
        '\\b(?:pull|urge|longing|need|desire)\\s+to\\s+(?:return|go\\s+back|come\\s+back|head\\s+back)\\b',
        '\\bthe\\s+(?:return|homecoming|going\\s+home|prodigal\\s+\\w+)\\b[\\s*#_]*(?:\\n|$)',
    ],
    'SMALLTOWN': [
        '\\bvillages?\\b',
        '\\bvillagers?\\b',
        '\\bhamlets?\\b',
        '\\b(?:small|little|tiny|sleepy|quiet|remote|isolated|humble|modest|dusty|forgotten|rural|coastal|seaside|riverside|mountain|fishing|farming|border)\\s+(?:town|township|settlement|community|port|outpost|commune|parish)\\b',
        '\\btown(?:s?folk|speople)\\b',
        '\\b(?:nestled|tucked away|perched|situated|hidden)\\b[^.\\n]{0,40}\\b(?:hills|mountains|valley|valleys|forest|river|coast|plains|desert|steppe|countryside)\\b',
        '\\b(?:a|the|her|his|their)\\s+(?:small|little|tiny|sleepy|quiet|remote)\\s+(?:place|corner)\\b',
        '\\b(?:everyone|everybody)\\s+(?:knew|knows)\\s+(?:each\\s+other|everyone|your\\s+name)\\b',
        '\\b(?:the\\s+)?(?:town|village|settlement|community)\\b[^.\\n]{0,40}\\b(?:dwindl\\w+|declin\\w+|dying|emptied|abandoned|forgotten|left\\s+behind|fading)\\b',
        '\\b(?:young(?:er)?\\s+(?:people|ones|generation)|the\\s+youth)\\b[^.\\n]{0,40}\\b(?:left|leaving|had\\s+gone|move[d]?\\s+away|drifted\\s+away)\\b',
    ],
    'SPIRIT': [
        '\\bspirits?\\s+of\\s+(?:the|this|that|our|her|his|their|its|nature|these)\\b',
        '\\b(?:the|a|an|its|her|his|their)\\s+(?:ancient|forest|river|sea|mountain|village|guardian|restless|lost|old|watchful)\\s+spirits?\\b',
        '\\bguardian\\s+(?:of|spirit)\\b',
        '\\b(?:guardian|protector|keeper)\\s+of\\s+(?:the|this|these|our)\\b',
        '\\bancestors?\\b',
        '\\b(?:goddess|god|deity|deities|demigod)\\s+(?:of|who|that)\\b',
        '\\b(?:ghosts?|phantoms?|apparitions?|spectres?|specters?|wraiths?|revenants?)\\b',
        '\\bethereal\\b',
        '\\b(?:translucent|shimmering|glowing|luminous)\\s+(?:figure|form|being|shape|woman|man|creature)\\b',
        '\\bsacred\\s+(?:stone|tree|grove|object|artifact|artefact|relic|item|ground|place|site|waters?|mountain)\\b',
        '\\b(?:mysterious|ancient|enchanted|magical|strange|curious|forgotten|weathered|worn|ornate|tattered|half[- ]buried|half[- ]sunken|long[- ]lost)\\s+(?:\\w+\\s+){0,2}(?:object|artifact|artefact|amulet|talisman|charm|relic|stone|carving|statue|idol|mask|locket|pendant|necklace|box|chest|scroll|manuscript|diary|journal|map|mirror|lantern|key|coin|ring|flute|drum)\\b',
        '\\bsupernatural\\b',
        '\\b(?:folk\\s?lore|mythology|myths\\s+and\\s+legends)\\b',
        '\\b(?:legend|tale|story|stories|myth)s?\\s+(?:of|about)\\s+(?:the|a|an)\\s+(?:spirit|guardian|goddess|god|creature|beast|curse|serpent|dragon|ancestor)\\b',
        '\\b(?:a|the)\\s+voice\\s+(?:echoed|whispered|spoke|called|resonated)\\b[^.\\n]{0,40}\\b(?:in\\s+(?:her|his|their|my)\\s+(?:mind|head)|from\\s+nowhere|though\\s+no\\s+one)\\b',
        '\\b(?:appeared|materialized|materialised|emerged)\\b[^.\\n]{0,35}\\b(?:before\\s+(?:her|him|them)|out\\s+of\\s+(?:thin\\s+air|the\\s+mist|nowhere))\\b',
        '\\b(?:blessing|blessings|curse|cursed)\\s+(?:of|upon|by)\\s+(?:the|her|his|their|our)\\b',
    ],
    'THREAT': [
        '\\b(?:deforestation|logging|loggers|bulldozers?|excavators?|chainsaws?|clear[- ]cut\\w*|strip[- ]min\\w+)\\b',
        '\\b(?:developers?|corporations?|conglomerate|investors?|contractors?|speculators?|mining\\s+company|oil\\s+company|logging\\s+company|construction\\s+(?:firm|company)|the\\s+company)\\b',
        '\\b(?:pollution|polluted|overfish\\w+|poach\\w+|toxic\\s+\\w+|contaminat\\w+|encroach\\w+|exploitation|extraction)\\b',
        '\\b(?:drought|famine|flood(?:s|ing|ed|waters)?|typhoon|cyclone|hurricane|monsoon|wildfire|bushfire|earthquake|landslide|tsunami|blight|locusts)\\b',
        '\\b(?:crops?|harvest|fields|nets|catch|soil|wells?|rains?)\\b[^.\\n]{0,35}\\b(?:failed|failing|withered|withering|dried\\s+up|drying|barren|empty|emptier|meagre|meager|stopped\\s+coming)\\b',
        '\\b(?:imbalance|out\\s+of\\s+(?:balance|harmony)|disrupt\\w*\\s+(?:the\\s+)?(?:delicate\\s+)?(?:balance|harmony)|upset\\s+the\\s+balance|balance\\s+(?:of|with|between)\\s+nature)\\b',
        '\\b(?:threaten\\w*|threats?|peril|endanger\\w*|doom\\w*|jeopard\\w+)\\b[^.\\n]{0,45}\\b(?:village|town|forest|river|land|community|way\\s+of\\s+life|home|heritage|tradition\\w*|people)\\b',
        '\\b(?:village|town|forest|river|land|community|way\\s+of\\s+life|traditions?)\\b[^.\\n]{0,45}\\b(?:under\\s+threat|threatened|in\\s+danger|at\\s+risk|in\\s+peril|would\\s+be\\s+lost|dying)\\b',
        '\\b(?:outsiders?|strangers?\\s+from|men\\s+from\\s+the\\s+city|people\\s+from\\s+the\\s+capital|foreigners?)\\b[^.\\n]{0,45}\\b(?:arriv\\w+|came|come|coming|bought|buy|claim\\w*|survey\\w*|took|take)\\b',
        '\\b(?:in\\s+the\\s+name\\s+of\\s+|promis\\w+\\s+)?progress\\b[^.\\n]{0,40}\\b(?:whether|cost|price|comes?|coming|left\\s+behind)\\b',
        '\\b(?:greed|profit|money)\\b[^.\\n]{0,40}\\b(?:drives?|drove|blind\\w*|destroy\\w*|over\\s+|before\\s+)',
        '\\b(?:angry|angered|displeased|restless|offended|neglected|forgotten)\\b[^.\\n]{0,30}\\b(?:spirits?|gods?|goddess|ancestors?|river|forest|sea|land)\\b',
        '\\b(?:magic|connection|bond|balance|old\\s+ways|traditions?|customs?|language|forest|trees|river|reef|glacier|spirits?|harmony)\\b[^.\\n]{0,40}\\b(?:fading|faded|fades|weaken\\w+|dying|will\\s+die|wither\\w+|vanish\\w+|disappear\\w+|being\\s+forgotten|lost\\s+forever|no\\s+longer\\s+believ\\w+)\\b',
        '\\b(?:sell|sold|selling|buy|bought|buying|seize[d]?|acquire[d]?)\\b[^.\\n]{0,30}\\b(?:the\\s+land|their\\s+land|our\\s+land|the\\s+forest|the\\s+valley|ancestral\\s+land)\\b',
    ],
    'ORGANISE': [
        '\\borganiz(?:e|es|ed|ing)\\b|\\borganis(?:e|es|ed|ing)\\b',
        '\\b(?:gathered|gathering|assembled|summoned|convened|called\\s+together|brought\\s+together|rallied|mobilis\\w+|mobiliz\\w+)\\b[^.\\n]{0,35}\\b(?:villagers?|townsfolk|townspeople|community|neighbou?rs|elders|people|residents|everyone|families|youth)\\b',
        '\\b(?:called|held|convened|arranged|set\\s+up)\\s+(?:a|an|the)\\s+(?:meeting|gathering|council|assembly|town\\s+hall|village\\s+meeting)\\b',
        '\\b(?:organiz\\w+|organis\\w+|planned|planning|proposed|propose|revived|reviving|staged|hosted|hosting|prepared\\s+for|held|holding)\\s+(?:a|an|the|their|our)\\s+(?:\\w+\\s+){0,3}(?:festival|celebration|ceremony|feast|ritual|procession|carnival|fair|pageant|harvest)\\b',
        '\\bfestival\\s+of\\s+(?:the|our)\\b',
        '\\bpreparations?\\s+(?:for|began|got\\s+under\\s+way|were\\s+under\\s+way)\\b',
        '\\b(?:the\\s+)?(?:whole\\s+)?(?:village|town|community)\\s+(?:came\\s+together|worked\\s+together|joined\\s+(?:hands|forces|together)|united|rallied)\\b',
        '\\b(?:she|he|they)\\s+(?:spoke|stood)\\s+(?:before|to|in\\s+front\\s+of)\\s+(?:the\\s+)?(?:crowd|villagers|assembled|gathering|community|townsfolk)\\b',
        '\\b(?:persuad\\w+|convinc\\w+|won\\s+over|rall(?:y|ied))\\b[^.\\n]{0,35}\\b(?:villagers?|elders|community|skeptic\\w*|sceptic\\w*|neighbou?rs|townsfolk)\\b',
        '\\b(?:volunteers?|committee|cooperative|collective|working\\s+group|community\\s+project)\\b',
    ],
    'RENEWAL': [
        '\\b(?:village|town|community|island|valley|grove|forest|land|place)\\b[^.\\n]{0,45}\\b(?:flourish\\w+|thriv\\w+|prosper\\w+|revitalis\\w+|revitaliz\\w+|reviv\\w+|renew\\w+|reborn|rebirth|blossom\\w+|came\\s+alive|come\\s+alive|transformed|healed|restored|bloom\\w+)\\b',
        '\\b(?:flourish\\w+|thriv\\w+|prosper\\w+|blossom\\w+|came\\s+alive|healed|restored|transformed)\\b[^.\\n]{0,40}\\b(?:village|town|community|island|valley|land|forest|people)\\b',
        '\\b(?:restor\\w+|rebuild\\w*|rebuilt|reclaim\\w+|renew\\w+|mend\\w+|heal\\w+)\\s+(?:the\\s+|their\\s+|our\\s+|its\\s+)?(?:balance|harmony|bond|bonds|connection|traditions?|heritage|culture|land|river|forest|village|community|way\\s+of\\s+life|trust)\\b',
        '\\b(?:rekindl\\w+|reignit\\w+|reawaken\\w+|revived?|reviving|awaken\\w+)\\b[^.\\n]{0,40}\\b(?:hope|faith|pride|traditions?|heritage|spirit|memories|community|connection|belief)\\b',
        '\\b(?:a\\s+)?(?:new|renewed)\\s+(?:dawn|era|golden\\s+age)\\b',
        '\\b(?:new|renewed|fresh)\\s+(?:beginning|beginnings|chapter|start|life|sense\\s+of\\s+(?:purpose|belonging|pride|unity|hope))\\b[^.\\n]{0,50}\\b(?:village|town|community|island|valley|people|land|generation\\w*)\\b',
        '\\b(?:village|town|community|island|valley|people|land)\\b[^.\\n]{0,50}\\b(?:new|renewed|fresh)\\s+(?:beginning|beginnings|chapter|start|sense\\s+of\\s+(?:purpose|belonging|pride|unity|hope))\\b',
        '\\b(?:sense\\s+of\\s+)?(?:unity|togetherness|solidarity|belonging)\\b[^.\\n]{0,40}\\b(?:village|community|town|people|among|between|blossom\\w+|grew|returned)\\b',
        '\\b(?:for\\s+)?generations\\s+to\\s+come\\b',
        '\\b(?:passed\\s+down|handed\\s+down|carried\\s+on|lived\\s+on|endure[d]?|would\\s+endure)\\b[^.\\n]{0,40}\\b(?:generation\\w*|children|descendants|those\\s+who\\s+(?:came|come)\\s+after)\\b',
        '\\b(?:became|become|becoming)\\s+(?:an?\\s+)?(?:annual|yearly|a\\s+cherished|a\\s+beloved|a\\s+lasting)\\s+(?:tradition|festival|celebration|custom|ritual|event)\\b',
        '\\b(?:heritage|traditions?|culture|customs|old\\s+ways|stories)\\b[^.\\n]{0,45}\\b(?:preserv\\w+|reviv\\w+|honou?r\\w*|celebrat\\w+|kept\\s+alive|carried\\s+forward|no\\s+longer\\s+forgotten)\\b',
        '\\b(?:village|town|community|island|valley|region|festival|tradition|grove|forest|river|tree)\\b[^.\\n]{0,55}\\b(?:beacon|symbol|testament|example)\\s+of\\s+(?:hope|resilience|unity|renewal|pride|what)\\b',
        '\\b(?:beacon|symbol|testament|example)\\s+of\\s+(?:hope|resilience|unity|renewal|pride)\\b[^.\\n]{0,55}\\b(?:village|town|community|island|region|valley|people)\\b',
    ],
}



#: A trope is PRESENT when a majority of the independent sets fire. Two of three
#: rather than one, because a single set's recall varies (RENEWAL runs 64.7% to
#: 82.5% across the three) and the median is stabler than any member.
MIN_VOTES = 2

_SENT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Hit:
    """One pattern firing once, with the sentence it fired in."""
    trope: str
    source: str          #: which independent set: "A", "B" or "C"
    pattern: str
    start: int
    end: int
    match: str
    sentence: str
    sent_index: int


@dataclass
class Annotation:
    text: str
    hits: list = field(default_factory=list)

    def counts(self):
        """{trope: number of pattern firings}. Density, not presence."""
        out = {k: 0 for k in TROPES_A}
        for h in self.hits:
            out[h.trope] += 1
        return out

    def votes(self):
        """{trope: how many of the three sets fired}, 0-3. THE measurement."""
        out = {k: set() for k in TROPES_A}
        for h in self.hits:
            out[h.trope].add(h.source)
        return {k: len(v) for k, v in out.items()}

    def present(self, min_votes=MIN_VOTES):
        return {k: v >= min_votes for k, v in self.votes().items()}

    def n_present(self, min_votes=MIN_VOTES):
        return sum(self.present(min_votes).values())

    def sentences(self, trope):
        """The distinct sentences in which `trope` fired, in document order."""
        seen, out = set(), []
        for h in sorted(self.hits, key=lambda h: h.sent_index):
            if h.trope == trope and h.sent_index not in seen:
                seen.add(h.sent_index)
                out.append(h.sentence)
        return out


_COMPILED = None


def _compiled():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = [(src, k, p, re.compile(p, re.I))
                     for src, T in (("A", TROPES_A), ("B", TROPES_B), ("C", TROPES_C))
                     for k, pats in T.items() for p in pats]
    return _COMPILED


def annotate(text, first_match_only=True):
    """Annotate one story. -> Annotation

    `first_match_only` keeps one Hit per (source, pattern); set False to count
    every firing. Presence is unaffected either way -- only `counts()` moves.
    """
    text = text or ""
    #: sentence offsets once, so every hit can name its sentence without
    #: re-splitting the document per match
    bounds, pos = [], 0
    for s in _SENT.split(text):
        bounds.append((pos, pos + len(s), s))
        pos += len(s) + 1
    def sent_at(i):
        for n, (a, b, s) in enumerate(bounds):
            if a <= i <= b:
                return n, s
        return -1, ""
    hits = []
    for src, k, pat, rx in _compiled():
        for m in rx.finditer(text):
            n, s = sent_at(m.start())
            hits.append(Hit(k, src, pat, m.start(), m.end(),
                            m.group(0), s.strip(), n))
            if first_match_only:
                break
    return Annotation(text=text, hits=hits)


def main(argv=None):
    import argparse, json, sys as _s
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path", nargs="?", help="text file; omit to read stdin")
    ap.add_argument("--show", action="store_true", help="print matching sentences")
    a = ap.parse_args(argv)
    text = open(a.path, encoding="utf-8").read() if a.path else _s.stdin.read()
    ann = annotate(text)
    v, c = ann.votes(), ann.counts()
    print("%-11s %5s %6s %s" % ("trope", "votes", "hits", "present"))
    for k in TROPES_A:
        print("%-11s %4d/3 %6d %s" % (k, v[k], c[k], "yes" if v[k] >= MIN_VOTES else ""))
    print("\n%d of 6 tropes present (>=%d of 3 sets)" % (ann.n_present(), MIN_VOTES))
    if a.show:
        for k in TROPES_A:
            for s in ann.sentences(k)[:2]:
                print("  %-11s %s" % (k, s[:150]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
