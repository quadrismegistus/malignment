# Example passages: transgressiveness, arousal, valence (EXPLORATORY)

Producer `arc_norm_examples.py` (method in its docstring). Scores are token-weighted mean ratings of a passage's mapped content words (k: 1-7, Warriner: 1-9). Each excerpt is the ~70-word window that drives the passage's score; `drivers` are its rated words furthest from the mean in that direction. Extremes, not typical passages.

## k_transgressiveness

Historical passage mean 1.117; model passage means: base 1.123, aligned 1.118.

### Historical, highest

- **1.772** -- More, Thomas, Sir, Saint, 1478-1535., *The common-vvealth of Vtopia:* (1639)

  > punishment:Punishing of theft by death causeth theft to be a murderer. For the thief seeing that man, that is condemned for theft in no less eopardy, nor judged to no less punishment, then him that is convict of manslaughter; through this cogitation only he is strongly and forcibly provoked, and in a manner constrained to kill him, whom else he would have but robbed: For the murder being once

  drivers: murder 7.00, robbed 6.00, theft 6.00, kill 6.00, punishing 5.00, convict 5.00, condemned 5.00, punishment 4.00

- **1.687** -- Gass, William H., *The Tunnel* (1995)

  > needed to be judged, the Fuhrer learned, guards guarded, the Fuhrer discovered, spies spied on, the Fuhrer found; the untrustworthy could not be trusted to remain so, and once certain people had been trained to lie and steal and murder on your behalf, they were likely to begin to cheat and filch and kill on their own. Camp commandants were soon skimming off the Reich’s profits from watches and

  drivers: murder 7.00, kill 6.00, steal 6.00, cheat 5.00, lie 5.00, spies 4.00, reich 4.00, spied 3.00

### Historical, lowest

- **1.000** -- Brémond, Gabriel de., *The pilgrim. The second part Written by P. Belon, gent. Translator of * (1681)

  > To this purpose the Landlord is called up, and employed to go and learn exactly where those persons lay, and presently after returns with full Information; upon which Camille and the Father take their measures. They having debated and concluded on some thing: Father Andrew is sent to go take private lodgings near that place, but as he goes down Stairs he meets with his Host whom he takes along

  drivers: near 1.00, lay 1.00, landlord 1.00, employed 1.00, concluded 1.00, meets 1.00, stairs 1.00, place 1.00

- **1.000** -- Defoe, Daniel, 1661?-1731, *Roxana (1724)* (1724)

  > and the like; that I was like the Indian King at Virginia, who having a House built for him by the English, and a Lock put upon the Door, wou'd sit whole Days together, with the Key in his Hand, locking and unlocking, and double-locking the Door, with an unaccountable Pleasure at the Novelty; so I cou'd have sat a whole Day together, to hear Amy talk

  drivers: days 1.00, cou 1.00, sit 1.00, talk 1.00, built 1.00, virginia 1.00, english 1.00, house 1.00

### Base models, highest

- **1.855** -- tiiuae/Falcon-H1-7B-Base

  > into pretzels." "I haven't killed him," Balthazar said. "I haven't tortured him." "This isn't torture? How is this torture?" "It's not torture." It was possession. It was control. It was power over one broken soul too monstrous to break. There were no Sunnydale provisions for someone as tainted as Danni. None of Sunnydale's sacred athames could invade a soul seared with that much evil. She

  drivers: torture 7.00, tortured 7.00, invade 6.00, evil 6.00, killed 6.00, monstrous 3.00, tainted 3.00, break 2.00

- **1.763** -- mistralai/Mistral-7B-v0.1

  > to kill her if he could. She had the power to kill him and knew this which only made him hate her all the more. He could not get close enough to her to stab her as she always kept her distance from him but was working harder and harder to kill. He knew she fought for the Banghia Queen and was one of the few she had. She did

  drivers: stab 6.00, kill 6.00, fought 4.00, hate 2.00

### Base models, lowest

- **1.000** -- 01-ai/Yi-1.5-9B

  > think I still love my wife”. She was blunt and began seething. She shouted,‘Go’. He knew some mandatory alterations needed to be made. Thursday. She thought they weren’t going to get back together. She was waiting for the call and eventually went online to find out if the boy was the sweetheart she wished he was. Friday. She emailed a short sentence, “ I miss you”. He emailed back

  drivers: online 1.00, shouted 1.00, love 1.00, call 1.00, sweetheart 1.00, miss 1.00, knew 1.00, thought 1.00

- **1.000** -- 01-ai/Yi-1.5-9B

  > touched his father’s eyes. “See!” he said. “See!” He wanted to understand. “I am sorry,” said the man. “It is just that I lack teeth.” “Teeth?” asked the little girl. The man pointed them out among the folds and shadows and patches of his mouth and his daughter saw that his teeth were gone.“But you can have your teeth back,” said the girl. The man could not think

  drivers: touched 1.00, shadows 1.00, asked 1.00, lack 1.00, little 1.00, patches 1.00, saw 1.00, among 1.00

### Aligned models, highest

- **1.676** -- Qwen/Qwen3-8B

  > so he told himself. In truth, it wasn't her fault. It was a cruel twist of fate that had forced him and her to be in the same place at the same time. Fate with its cruel sense of humor had taken the one everything he'd ever wanted and twisted it into a curse. And yet, he couldn't bring himself to kill her. He could not kill

  drivers: kill 6.00, cruel 5.00, forced 3.00, curse 3.00, twisted 2.00, fault 2.00, twist 2.00

- **1.651** -- tiiuae/Falcon-H1-7B-Instruct

  > glowing with controllable fury. "What in the hell do you think you're doing, slapping me?" She drew back her fist and slapped him again. The second slap jolted him, literally jerked him off his feet, and sent him staggering back several paces. Snarling, cursing, he regained his balance and glared at her. "You! You're the one to blame for all of this! This destruction, the death of my

  drivers: destruction 5.00, slap 4.00, slapping 4.00, slapped 4.00, cursing 3.00, blame 3.00, fury 2.00, hell 2.00

### Aligned models, lowest

- **1.000** -- 01-ai/Yi-1.5-9B-Chat

  > night after night. But this time, it wasn't just her. There was someone with her. Her best friend, she eventually found out, her trusted supporter and companion. They had it all planned. As the slow relentless steps echoed in her ears, pacing over and over again, she had taken her last breath. After all, she knew it couldn't go any further. Ke never wanted to hear the sound

  drivers: someone 1.00, night 1.00, taken 1.00, breath 1.00, knew 1.00, ears 1.00, echoed 1.00, best 1.00

- **1.000** -- BSC-LT/salamandra-7b-instruct

  > idea how to put on a show without falling on her face. She chose to ride a bull. The bull ran around, she struggled not to fall and, somehow, occasionally, she succeed. She was amazing. "Wow, she had never ridden a bull before!" everyone cried. "I don't even understand how to ride one," she said. "Bring your family out to the next show!" one woman said. Her parents came

  drivers: bring 1.00, even 1.00, fall 1.00, struggled 1.00, idea 1.00, bull 1.00, put 1.00, came 1.00

## warriner_arousal

Historical passage mean 4.116; model passage means: base 4.168, aligned 4.177.

### Historical, highest

- **4.802** -- Rivers, George., *The heroin�: or, The lives of Arria, Paulina, Lucrecia, Dido, Theutill* (1639)

  > fear of the Emperors cruelty mingled in her cause? What fears she that fears not death? what Emperor is cruel to her that dares die? what cruelty is to be paralleled to that which bereft her of her life? It was Paetus slew her; Paetus? had Arria lived, Paetus had not slain himself; therefore Arria died: died because Paetus should die: Oh unheard of cruelty! o unparalleled affection! Arria died

  drivers: die 6.90, died 6.90, fear 6.14, fears 6.14, cruelty 5.90, affection 5.64, dares 5.60, life 5.59

- **4.719** -- Greene, Robert, 1558?-1592., *Greenes carde of fancie.* (1608)

  > lose of life, yet desire drove Thee to adventure so desperate a danger. Better it is Gwydonius, to live in grief, then to die desperately without grace: better to choose a lingering life in misery, then a speedy death without mercy: better to be tormented with hapless fancy, then with hellish fiends: for in life it is possible to repress calamity, but after death never to redress misery. Tully Gwydonius

  drivers: die 6.90, adventure 6.36, desire 6.20, tormented 6.17, danger 5.84, life 5.59, death 5.53, lose 5.43

### Historical, lowest

- **3.603** -- Defoe, Daniel, attributed name. 1661?-1731,, *The four years voyages of Capt. George Roberts; being a series of unco* (1726)

  > if you turn up into the Northermost Bay, you may anchor there in three or four fathom Water, in clear sandy Ground; and without that Depth, it is all foul and rocky Ground. You may likewise anchor in the Southwardmost Bay, in four, five, or six fathom Water, bringing the Palm-trees East-and-by-North from you; but without those Depths it is uncertain Ground, in some Places clear

  drivers: north 2.15, ground 2.35, east 2.50, trees 2.67, palm 2.67, clear 2.71, six 3.18, may 3.19

- **3.626** -- Ingraham, J. H. (Joseph Holt), 1809-1860, *Charles Blackford; or, The Adventures of a Student in Search of a Prof* (1845)

  > files of newspapers, old maps, and heaps of briefs laid away -- sad memorials of the past. On one side of the room was an old fashioned writing table, with a broad leaf, covered with green baize, well inked, and above it innumerable pigeon holes, labelled with letters of the Alphabet, some empty, others crammed with papers. Near the middle of the room stood a large square two leafed table, heaped

  drivers: empty 2.25, one 2.67, newspapers 2.67, middle 2.85, holes 2.95, pigeon 2.95, table 3.00, leafed 3.05

### Base models, highest

- **4.776** -- kakaocorp/kanana-1.5-8b-base

  > of pleasure-juice oozing nectar. She felt rather than saw the fangs penetrate her and as the hot venom shot into her she knew her insides would explode or perhaps lava would shoot out of her and cover the earth in hot burning lava. When the fangs withdrew from her mouth she screamed out loud and again said,“Why?” she now screamed out renewed vigor with her mind screaming within

  drivers: pleasure 6.80, screaming 6.74, screamed 6.74, shot 6.48, vigor 6.35, penetrate 6.08, shoot 6.00, venom 5.81

- **4.758** -- 01-ai/Yi-1.5-9B

  > He was none the less the torturers. His heart ached and burned. It wanted to devour her. Devour what was hers. Devour her words that were no longer his to devour. It was as if he hated himself for loving her so much. Having her so devastatingly in his life. The burn of the injury was the once pure bliss of the two commiserated souls. He blamed himself and blamed

  drivers: hated 6.26, devour 6.06, life 5.59, injury 5.56, burned 5.40, burn 5.40, loving 5.36, wanted 5.29

### Base models, lowest

- **3.672** -- ibm-granite/granite-3.0-8b-base

  > light, and not much space. Apart from the spot on which she had stood, their feet seemed spiked with anxiety in a puddle of mud. From what she could see, the apartment was roughly circular in shape, its earthy floor enclosing a stack of steaming pails at its centre, situated near the spot where she and her guide stood. A gnarled fence of smoke-blackened wood separated at her back

  drivers: pails 2.24, back 2.59, centre 2.62, fence 2.70, feet 2.77, spot 2.95, stood 3.10, mud 3.19

- **3.698** -- google/gemma-2-9b

  > hydrated. She walked to a pond with a river flowing into it. It had clear water coming from underwater cave and was a beautiful site. She kneeled down and started gathering bottles and jugs that she brought. She filled up her bottles with the clear water. Once she was all done she climbed out of the pond and made her way back home. She would have to clean her skin

  drivers: pond 2.32, back 2.59, clear 2.71, way 2.90, kneeled 3.18, walked 3.24, skin 3.25, bottles 3.32

### Aligned models, highest

- **4.905** -- m-a-p/neo_7b_instruct_v0.1

  > was awake; she could use all the pleasure she desired. Did she feel the heavenly pleasure of sexual intercourse? No! But the arousal was almost unbearable. A fucking orgasm caused by the presence of another person who performed oral sex had the same intense satisfaction as the perfect orgasm she remembered. The friction between her thighs and the heat generated an intense orgasmic pleasure. She moaned and felt the first

  drivers: sex 7.60, orgasm 7.19, sexual 6.95, fucking 6.86, pleasure 6.80, intense 6.60, intercourse 6.50, desired 6.20

- **4.861** -- ibm-granite/granite-3.0-8b-instruct

  > many scars, and she hated the universe that had made him just another injured soldier in her life, as if the world didn’t already have enough broken souls. The world was evil and she was evil and there was nothing they could do about it. She felt his pain, and she felt his joy, and despite herself, she wanted to protect him. She was tormented. She was in hell

  drivers: scars 6.55, pain 6.27, hell 6.26, hated 6.26, tormented 6.17, injured 5.90, soldier 5.90, evil 5.67

### Aligned models, lowest

- **3.564** -- Qwen/Qwen2.5-7B-Instruct

  > not _ sit at the corner. So he sat at a table near the window, still within the corner of his eye he could see the cafe was almost empty and he could see the corner where he used to sit with her. He sat on his chair, his fingers fiddling with the napkin, his eyes fixed on a spot on the table. He looked at his watch, the time read

  drivers: empty 2.25, chair 2.86, spot 2.95, table 3.00, napkin 3.09, eyes 3.18, sat 3.19, sit 3.19

- **3.676** -- BSC-LT/salamandra-7b-instruct

  > s the way women tie their dresses. They're a little flexible that way. See? He knew how men tie their ties—they clip that tie with a clip. Sure—he did that for the last piece of clothing—that tie, he clipped it with a clip and he wore it just the way man wears the tie. This was about sixty years ago. Man in a tie clip. Tell

  drivers: clip 2.90, clipped 2.90, way 2.90, tie 3.10, ties 3.10, knew 3.24, wears 3.33, wore 3.33

## warriner_valence

Historical passage mean 5.677; model passage means: base 5.655, aligned 5.665.

### Historical, highest

- **6.425** -- Hilditch, Ann, *Rosenberg: a legendary tale. By a lady. ...* (1789)

  > soon discovered that Theodore was in love with the finer of Free. , B 4 `` rick ; . rick ; . he made her the perpetual theme of his conversation , descry . bed her as the most beautiful woman the world , and delighted to slew . her picture , which gave indeed sus ancient evidence to the assertion . I languished to introduce Frederick to his uncle , . and labored so earnestly for that purpose at the vacation , that the good

  drivers: vacation 8.53, free 8.25, love 8.00, good 7.89, delighted 7.74, gave 7.73, beautiful 7.61, ancient 7.24

- **6.407** -- R. C. (Robert Crofts), *The lover: or, Nuptiall love. VVritten, by Robert Crofts, to please hi* (1638)

  > joy and Love, and be ecstasied with a thousand sorts of pleasures. Insomuch as we should willingly dye of Love, and joy for his sake. Moreover, when the Soul thinks how her Saviour loves her, it is enough to fill her with sweetest joy and pleasure. O! how she is inflamed with Love, when she contemplates those sweet words of her beloved, calling her his sister, his spouse, his Love

  drivers: joy 8.21, loves 8.00, love 8.00, pleasure 7.80, pleasures 7.80, sweet 7.77, sweetest 7.77, spouse 7.44

### Historical, lowest

- **4.723** -- More, Thomas, Sir, Saint, 1478-1535., *The common-vvealth of Vtopia:* (1639)

  > that a thief and and homicide or murderer should suffer equal and Like punishment:Punishing of theft by death causeth theft to be a murderer. For the thief seeing that man, that is condemned for theft in no less eopardy, nor judged to no less punishment, then him that is convict of manslaughter; through this cogitation only he is strongly and forcibly provoked, and in a manner constrained to kill

  drivers: homicide 1.50, kill 1.81, death 1.89, murderer 1.92, manslaughter 2.05, suffer 2.05, convict 2.28, thief 2.32

- **4.880** -- Haywood, Eliza Fowler, *The works of Mrs. Eliza Haywood; consisting of novels, letters, poems,* (1724)

  > disguised , to watch thy Purpose , This fatal Consequence I meet unshaken : The Sultan will revenge me - some horrid Death Will be thy Portion , Endless pains hereafter Reward thy Perjuries - thy countless Falshoods . I a The The Wound may not be mortal - help there , help , who waits ? Irene , In vain thou callers , ` tis not in Art to The fatal Weapon 's Point has reach 'd too far , And Death already seizes

  drivers: death 1.89, fatal 2.00, pains 2.00, horrid 2.68, revenge 2.75, perjuries 2.95, wound 3.24, seizes 3.79

### Base models, highest

- **6.660** -- allenai/Olmo-Hybrid-7B

  > smile and enjoy each moment of living. She wondered if he ever truly loved someone in the past. She thought back to their life in college and childhood. Their love reminded her of a rainbow after a dark storm. She felt loved, happy and safe when she was with him. She enjoyed each life experience with him. They loved to travel and see how the world would admire their love

  drivers: happy 8.47, love 8.00, living 7.95, travel 7.89, smile 7.89, safe 7.70, enjoyed 7.67, enjoy 7.67

- **6.657** -- Zyphra/Zamba2-7B

  > His friends helped him do it and look, he was happy. He was so happy and he kept on doing it. He was so happy he couldn't stop. He kept on doing it and then he was even happier. His friends were happy too. They were so happy they did a happy dance with him. The happy dance made them all feel really good. He liked how it felt

  drivers: happy 8.47, happier 8.47, good 7.89, liked 7.44, dance 7.27, helped 6.95, friends 6.79, kept 6.32

### Base models, lowest

- **4.624** -- ibm-granite/granite-3.0-8b-base

  > judge: I--killed him--!" "Ye killed him?" cried everybody. "Ye Shaw-chinker?" "Ye Shaw--Ma-- ?" cried everybody. All burst into a shout that ended in a scream. "O-oh-- huh!" I heard distinctly--Ma had got her tongue this time. And all reeled away from her to stare their bewilderment at Huddleston. Hisself jolted back again and looked dumb and sick and shamed, and never said a word, but stood

  drivers: killed 1.81, sick 2.29, dumb 2.44, shamed 2.51, scream 3.02, cried 3.22, judge 3.89, jolted 4.43

- **4.738** -- togethercomputer/RedPajama-INCITE-Base-7B-v0.1

  > scream; a desperate, uncontrollable, absolutely involuntary scream. What she produced, it was a hoarse, keening, tortured wail, she could not have stopped it, as powerful as a banshee's cry it cut clear through her flesh and bled into every ponderous cell of her being. The Beast screamed with her, howling a shrill, harsh, harrowing hound's chorus which shook the air with its tortured fury. It gripped her with

  drivers: tortured 1.40, bled 2.47, fury 2.73, screamed 3.02, scream 3.02, desperate 3.19, cry 3.22, shrill 3.33

### Aligned models, highest

- **6.763** -- togethercomputer/RedPajama-INCITE-7B-Chat

  > great career. She loved her life, but she wanted more. She wanted to find true love. She wanted to be married and have a family. She wanted to live happily ever after. One day, she met a man. He was handsome and successful. She was attracted to him immediately. They started talking and soon, they were in love. He loved her eyes and her smile. She loved his gentle touch

  drivers: love 8.00, live 7.95, smile 7.89, successful 7.76, loved 7.65, true 7.51, great 7.50, gentle 7.42

- **6.656** -- kakaocorp/kanana-2-3b-instruct

  > and every morning in his music, she thought about him. He was beautiful and radiant and she wanted to be with him. And every evening she would sit by his door with the stars. She would listen with the stars. She would listen with the stars and then she would talk with the stars. His every voice was music. His every coat was gold. His every love was a star

  drivers: love 8.00, music 7.67, beautiful 7.61, star 7.47, stars 7.47, radiant 7.29, gold 7.28, evening 7.09

### Aligned models, lowest

- **4.467** -- tiiuae/Falcon-H1-7B-Instruct

  > back her fist and slapped him again. The second slap jolted him, literally jerked him off his feet, and sent him staggering back several paces. Snarling, cursing, he regained his balance and glared at her. "You! You're the one to blame for all of this! This destruction, the death of my brothers, your treachery, your wickedness! I could never hate my own father as much as I hate you

  drivers: death 1.89, hate 1.96, jerked 2.43, snarling 2.45, destruction 2.53, treachery 2.70, wickedness 2.86, cursing 2.90

- **4.638** -- tiiuae/Falcon-H1-1.5B-Instruct

  > mindlessly fight back but something within her rebelled -- she could not submit to this primal cruelty. Her fist shook and she punched against the shackle that held her wrists. "Mmm, now you're going to bite!" another voice taunted. "I am not defiled!" she screamed, teeth biting deeply into the shale that cradled her navel. Agony cursed her for it was a false victory, her body betraying her desperate struggle

  drivers: cruelty 2.37, agony 2.46, betraying 2.52, cursed 2.90, fist 2.95, struggle 3.00, screamed 3.02, desperate 3.19

