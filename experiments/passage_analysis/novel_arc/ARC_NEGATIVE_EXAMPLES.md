# Negative share: words and passages, history and models (EXPLORATORY)

Producer `arc_negative_examples.py` (method in its docstring). Negative = mapped Warriner valence below 4. Passages with at least 60 scored words.

| group | passages | median negative share | 90th percentile | median, suspect words removed |
|---|---|---|---|---|
| novels 1700s | 1498 | 0.114 | 0.179 | 0.107 |
| novels 1800s | 1498 | 0.101 | 0.169 | 0.092 |
| novels 1900s | 489 | 0.102 | 0.160 | 0.090 |
| models: base | 325 | 0.070 | 0.139 | 0.064 |
| models: aligned, raw | 355 | 0.055 | 0.125 | 0.048 |
| models: aligned, chat, asked | 203 | 0.065 | 0.125 | 0.059 |

Suspect words (removed from both numerator and denominator in the last column): court, cried, cut, distance, late, mean, means, meant, old, weight

## novels 1700s

Negative words carrying the most negative tokens (share of the group's negative tokens): poor 1.4%, cried 1.4%, old 1.2%, means 1.0%, death 1.0%, fear 0.8%, tears 0.7%, mean 0.7%, alone 0.7%, doubt 0.7%, lost 0.6%, suffer 0.6%, unhappy 0.6%, late 0.5%, consequence 0.5%, impossible 0.5%, mistress 0.5%, danger 0.5%, temper 0.5%, distance 0.5%, afraid 0.4%, distress 0.4%, grief 0.4%, affair 0.4%, pity 0.4%, suffered 0.4%, beg 0.4%, cruel 0.4%, interrupted 0.4%, fall 0.4%

- **90th percentile**, negative share 0.179 -- Radcliffe, Ann Ward, 1764&ndash;1823, The Mysteries of Udolpho, A Romance ... (1794)

  > the [enemy 2.2] comes, what a pretty figure they will [cut 3.9], if they are to [fall 3.9] down in fits, all of a row! The [enemy 2.2] won't be so civil, perhaps, as to walk off, like the ghost, and leave them to help one another up, but will [fall 3.9] to, [cutting 3.9] and slashing, till [lie 2.4] makes them all rise up [dead 2.0]

- **90th percentile**, negative share 0.179 -- Lewis, M. G. (Matthew Gregory), 1775&ndash;1818, The Monk: A Romance (1796)

  > my gratitude, boundless as the excellence of my benefactors. Lorenzo! Raymond! names so dear to me! teach me to bear with fortitude this sudden transition from [misery 2.2] to bliss. So lately a [captive 3.3], [oppressed 3.1] with chains, [perishing 2.2] with [hunger 3.2], [suffering 2.0] every [inconvenience 3.0] of cold and want, hidden from the light, [excluded 3.5] from society, [hopeless 2.2], [neglected 2.2], and, as I [feared 2.9], [forgotten 3.7]

- **median**, negative share 0.114 -- Aubin, Penelope, 1679-1731, Lucinda (1739) (1739)

  > accordingly carried to the Merchant's, and the Captain received the Money for which I was purchased. Now began my first Experience in [Slavery 2.0], and I very much lamented my [unfortunate 3.3] Condition. I had heard before of the [Hardships 2.8] and [Severities 3.8] these [poor 3.7] Creatures are obliged to [undergo 3.9], and I represented to my Imagination a Scene of the greatest [Misery 2.2]


## novels 1800s

Negative words carrying the most negative tokens (share of the group's negative tokens): old 3.8%, poor 1.6%, cried 1.0%, death 1.0%, dead 0.8%, alone 0.8%, mean 0.8%, lost 0.7%, fear 0.7%, means 0.7%, tears 0.6%, blood 0.6%, doubt 0.6%, late 0.6%, cut 0.5%, distance 0.4%, bad 0.4%, struck 0.4%, broken 0.4%, war 0.4%, grave 0.4%, wrong 0.4%, die 0.4%, trouble 0.4%, court 0.4%, fall 0.4%, died 0.4%, evil 0.3%, terrible 0.3%, pity 0.3%

- **90th percentile**, negative share 0.169 -- Meredith, George, 1828&ndash;1909, Beauchamp's Career: By George Meredith ... In Three Volumes (1876)

  > behalf of the [poor 3.7] as well as of the country. He appears to me the only public man who looks to the state of the [poor 3.7] -- I [mean 2.4], their interests. They pay for [war 2.2], and if we are to have peace at home and strength for a really national [war 2.2], the only [war 2.2] we can ever call necessary, the [poor 3.7]

- **90th percentile**, negative share 0.169 -- Paulding, James Kirke, 1778-1860, Selim, the Benefactor of Mankind (1832) (1832)

  > The Arabians laughed at these [infidels 3.9], and indulged in some odd mummeries of their own; while the Mussulmans, [despising 3.1] them all, lighted their pipes and quietly [submitted 3.9] to destiny. “Allah is great, and Mahomet is his prophet!” exclaimed they at intervals, and [smoked 3.4] away. The [confusion 3.3] on board, and the [violent 2.3] rolling of the vessel had brought the rich Turk

- **median**, negative share 0.101 -- Austen, Jane, 1775&ndash;1817, Pride and Prejudice: A Novel. (1813)

  > on. “From the very beginning, from the first moment I may almost say, of my acquaintance with you, your manners impressing me with the fullest belief of your [arrogance 2.5], your [conceit 3.8], and your [selfish 3.3] [disdain 3.7] of the feelings of others, were such as to form that ground-work of disapprobation, on which succeeding events have built so immoveable a [dislike 3.2]


## novels 1900s

Negative words carrying the most negative tokens (share of the group's negative tokens): old 3.8%, cried 1.4%, poor 1.4%, mean 1.2%, doubt 0.9%, fear 0.9%, bad 0.9%, lost 0.7%, death 0.7%, cut 0.7%, prison 0.7%, alone 0.6%, means 0.6%, dead 0.6%, died 0.6%, wrong 0.5%, feared 0.5%, blood 0.5%, afraid 0.5%, auld 0.5%, anger 0.5%, meant 0.4%, trouble 0.4%, wrath 0.4%, hated 0.4%, gang 0.4%, angry 0.4%, late 0.4%, fallen 0.4%, lying 0.4%

- **90th percentile**, negative share 0.159 -- Brown, George Douglas, 1869&ndash;1902, The House with the Green Shutters: By George Douglas: Third  (1901)

  > at me frae beyond the [grave 2.4].” Mrs. Gourlay beat her [desperate 3.2] hands. Her [feeble 3.9] remonstrance was a snowflake on a hill, to the [dull 3.4] intensity of this [conviction 3.9]. So colossal was it that it gripped herself, and she glanced dreadfully across her shoulder. But, in spite of her [fears 2.9], she must [plead 3.3] with him to save. “Johnnie dear,” she [wept 2.9]

- **90th percentile**, negative share 0.162 -- Brown, George Douglas, 1869&ndash;1902, The House with the Green Shutters: By George Douglas: Third  (1901)

  > a [terrible 2.1] thing [befell 3.9] him. For a while he swaggered round the [empty 3.8] platform and [smoked 3.4] a [cigarette 3.0]. Milk-cans clanked in a shed, mournfully. Gourlay had a congenital [horror 3.4] of [eerie 3.4] sounds -- he was his mother's son for that -- and he [fled 3.8] to the waiting room, to avoid the hollow clang. It was a June afternoon, of [brooding 3.3]

- **median**, negative share 0.102 -- Butler, Samuel, 1835&ndash;1902, The Way of All Flesh; By Samuel Butler [etc.] (1903)

  > to get it. Nevertheless, what he wanted was in reality so easily to be found that it took a highly educated scholar like himself to be [unable 3.0] to find it. But, however, this may be, he had been [scared 2.8], and now saw lions where there were none, and was [shocked 3.9] and [frightened 2.5], and night after night his courage had [failed 2.3]


## models: base

Negative words carrying the most negative tokens (share of the group's negative tokens): old 5.1%, late 1.1%, war 1.1%, lost 1.1%, alone 1.0%, bad 0.9%, empty 0.9%, dead 0.8%, broken 0.8%, meant 0.8%, mean 0.8%, blood 0.7%, death 0.7%, wrong 0.6%, distance 0.6%, hit 0.6%, problem 0.6%, hospital 0.6%, cut 0.6%, pain 0.6%, fear 0.5%, cried 0.5%, afraid 0.5%, noise 0.5%, bottom 0.5%, died 0.5%, fall 0.5%, cry 0.5%, die 0.5%, trouble 0.5%

- **90th percentile**, negative share 0.139 -- kakaocorp/kanana-1.5-8b-base

  > his soldiers." "Mr. Kramer, that's not true." "It's true, it's the truth." "Oooooooh, even Clara doesn't know this! Okay, the Japanese Supreme Commander [issued 4.0] a directive..." "This true-to-life detail was also true to life." "...to..." "True, it was all a [lie 2.4]." "You [biter 3.6], you [liar 2.4], you [liar 2.4]!" "No Clara, you [lie 2.4]." "You [old 3.2] [liar 2.4]

- **90th percentile**, negative share 0.138 -- EleutherAI/pythia-2.8b

  > strange dream there was a voice, who laughed in [mocking 3.8] laughter, while evoking the intensity of dark passion. The dream [shattered 3.4], and what had once been a most amazing scene became a scene of utter darkness, silence and [shock 3.9]. The speakers and I awoke [sobbing 2.6] loudly, as if my heart had been [ripped 3.3] from my chest. It was a [nightmare 1.8]

- **median**, negative share 0.070 -- Qwen/Qwen2.5-7B

  > not tell what. He must have scratched his face because it [burned 3.7] with [blood 3.5]. His hands moved in the air searching for water. After a while, he recognised his fingers and remembered where he was. On the floor. His clothes were [torn 3.1], [lying 2.4] in tatters around him. He looked up and away from his room. A new, but still [broken 2.8]


## models: aligned, raw

Negative words carrying the most negative tokens (share of the group's negative tokens): old 6.8%, lost 2.3%, alone 1.5%, fear 1.3%, stumbled 1.0%, late 1.0%, wrong 0.9%, difficult 0.9%, forgotten 0.9%, chaos 0.8%, weight 0.7%, distance 0.7%, pain 0.7%, tears 0.6%, loss 0.6%, empty 0.6%, hung 0.6%, hospital 0.5%, meant 0.5%, sadness 0.5%, fears 0.5%, worry 0.5%, hit 0.5%, struck 0.5%, fall 0.4%, shiver 0.4%, struggles 0.4%, cut 0.4%, death 0.4%, trembling 0.4%

- **90th percentile**, negative share 0.126 -- HuggingFaceTB/SmolLM2-360M-Instruct

  > width of his ice-[smothered 2.7] body, his knife was dropped and he fell to the deck, [crying 3.2], "More of that!" He was [lying 2.4] facing west, with the raking evergreen branches curving toward the upper [gun 3.7] deck, so full of ice that there were little squares between his elbows and ankles that made it [impossible 3.5] for him to bear the [weight 3.9]

- **90th percentile**, negative share 0.125 -- ContextualAI/archangel_sft-dpo_pythia2-8b

  > about is something more: humanity. Even when people are doing [terrible 2.1] things, those soldiers are still our friends. We are better than the person they [kill 1.8]. Neela’s family had a [late 3.3] Father, and she felt that the way she was raised could be the reason why he left them. For her, his [death 1.9] was another nail in the [coffin 2.6]

- **median**, negative share 0.055 -- LLM360/AmberSafe

  > he himself felt as an author when describing the characters and world built within the novels he created. These questions [provoked 3.3] intense reflection for the author, as he contemplated on the impact and [weight 3.9] of his authorial presence and intentions. Tolstoy retraced his steps back towards the forest path, [lost 2.5] in deep thought as he pondered his creative process, [aging 3.0]


## models: aligned, chat, asked

Negative words carrying the most negative tokens (share of the group's negative tokens): forgotten 5.4%, old 5.1%, lost 3.5%, stumbled 1.9%, fear 1.5%, curse 1.0%, weight 0.8%, abandoned 0.8%, alone 0.8%, dust 0.8%, treacherous 0.8%, chaos 0.7%, ruins 0.7%, war 0.7%, vanished 0.6%, eerie 0.6%, rumors 0.6%, danger 0.6%, dusty 0.6%, empty 0.6%, battle 0.6%, cryptic 0.6%, fought 0.6%, late 0.5%, pain 0.5%, buried 0.5%, loss 0.5%, threat 0.5%, distance 0.5%, dangers 0.5%

- **90th percentile**, negative share 0.125 -- google/gemma-2-9b-it

  > [forgotten 3.7] memory was trying to surface. She instinctively clutched it, its smooth surface sending a [shiver 3.6] of recognition down her spine. Suddenly, a searing [pain 2.0] pierced her chest, a wave of emotion so powerful it [threatened 2.6] to [drown 2.3] her. Images flashed before her eyes - a storm [raging 3.2], a [shipwreck 3.8], a woman [struggling 3.0] against the waves, her face filled with [terror 2.8]

- **90th percentile**, negative share 0.125 -- m-a-p/neo_7b_instruct_v0.1

  > conducting an experiment that went horribly [wrong 3.2]. His attempt to leap through time resulted in a paradox, causing a sudden and [violent 2.3] shift in the timeline. The inventor, [overwhelmed 2.8] by the [consequences 3.9] of his experiment, [vanished 3.9], leaving behind a piece of machinery that was never recovered. The town, however, never recovered from the [shock 3.9] of what had happened. The [accident 2.5]

- **median**, negative share 0.065 -- m-a-p/neo_7b_instruct_v0.1

  > gain control over all forms of magic, a power that could either save the world or bring about its [destruction 2.5]. Elara, driven by a mix of curiosity and [fear 2.9], decided to seek the Crystal, hoping to understand her parents' fate. The journey to the Crystal's hidden location was filled with challenges, from [treacherous 2.9] terrains to powerful beings that [feared 2.9]

