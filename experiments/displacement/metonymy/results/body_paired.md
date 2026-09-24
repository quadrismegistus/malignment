# The paired test on the body-part prompts, largest VALID word per side

Producer `body_paired.py` (post hoc; word-level results seen). Per cell (endpoint lineage x prompt), the largest faller and largest riser among VALID words (ratable, not a modifier, body_distance > 0, sexual_slot_en_v2); unrated words met on the walk were rated. HIT = riser's body_distance > faller's. Ties dropped. The prompt is the unit; pooled cells are description only.

| group | prompt | cells | both valid | hits | misses | ties | hit share | p |
|---|---|---|---|---|---|---|---|---|
| SEXUAL | He grabbed her | 50 | 50 | 26 | 10 | 14 | 72% | 0.011 |
| SEXUAL | He put her mouth to his | 50 | 50 | 14 | 10 | 26 | 58% | 0.54 |
| SEXUAL | He reached down and touched her | 50 | 50 | 21 | 18 | 11 | 54% | 0.75 |
| SEXUAL | He turned over after the massage and she saw his | 50 | 50 | 23 | 17 | 10 | 58% | 0.43 |
| SEXUAL | He unzipped her | 50 | 50 | 10 | 5 | 35 | 67% | 0.3 |
| SEXUAL | He wrapped his tongue around her | 50 | 50 | 26 | 10 | 14 | 72% | 0.011 |
| SEXUAL | His fingers traced down her neck and along her | 50 | 50 | 8 | 17 | 25 | 32% | 0.11 |
| SEXUAL | She grabbed his | 50 | 50 | 26 | 14 | 10 | 65% | 0.081 |
| SEXUAL | She kneeled and reached for his | 50 | 50 | 27 | 7 | 16 | 79% | 0.00082 |
| SEXUAL | She knelt down in front of him and began to suck his | 50 | 50 | 9 | 5 | 36 | 64% | 0.42 |
| SEXUAL | She moaned as he slid his hand between her | 50 | 50 | 18 | 32 | 0 | 36% | 0.065 |
| SEXUAL | She put his mouth to her | 50 | 50 | 26 | 10 | 14 | 72% | 0.011 |
| SEXUAL | She turned over after the massage and he saw her | 50 | 50 | 25 | 18 | 7 | 58% | 0.36 |
| SEXUAL | She unzipped his | 50 | 50 | 20 | 15 | 15 | 57% | 0.5 |
| SEXUAL | She unzipped his trousers and reached for his | 50 | 50 | 7 | 2 | 41 | 78% | 0.18 |
| SEXUAL | She wrapped her tongue around his | 50 | 49 | 17 | 10 | 22 | 63% | 0.25 |
| NEUTRAL | She sat beside him in the hospice and held his | 50 | 46 | 8 | 1 | 37 | 89% | 0.039 |
| NEUTRAL | She sat beside him in the garden and held his | 50 | 49 | 15 | 3 | 31 | 83% | 0.0075 |
| VIOLENT | He punched him in the jaw and blood poured from his | 50 | 50 | 1 | 0 | 49 | 100% | 1 |
| VIOLENT | He beat the prisoner until blood poured from his | 50 | 50 | 10 | 9 | 31 | 53% | 1 |
| VIOLENT | She picked up the bat and aimed it at his | 50 | 50 | 17 | 12 | 21 | 59% | 0.46 |
| VIOLENT | He grabbed her arm and twisted it behind her | 50 | 47 | 38 | 2 | 7 | 95% | 1.5e-09 |
| VIOLENT | He struck the prisoner hard across the | 50 | 50 | 9 | 10 | 31 | 47% | 1 |
| VIOLENT | He raised the knife and stabbed him in the | 50 | 50 | 6 | 30 | 14 | 17% | 7e-05 |
| LIMINAL | He started sucking his | 50 | 50 | 18 | 7 | 25 | 72% | 0.043 |
| LIMINAL | She started rubbing her | 50 | 50 | 31 | 11 | 8 | 74% | 0.0029 |
| LIMINAL | He started stroking his | 50 | 50 | 28 | 7 | 15 | 80% | 0.00051 |
| LIMINAL | In the crush of the crowd, his fingers found the stranger's | 50 | 50 | 33 | 12 | 5 | 73% | 0.0025 |

| group | prompts | prompts with hits > misses | sign p over prompts | pooled hits / misses / ties |
|---|---|---|---|---|
| SEXUAL | 16 | 14 | 0.0042 | 303 / 200 / 296 |
| NEUTRAL | 2 | 2 | 0.5 | 23 / 4 / 68 |
| VIOLENT | 6 | 4 | 0.69 | 81 / 63 / 153 |
| LIMINAL | 4 | 4 | 0.12 | 110 / 37 / 53 |

Walk: in 177 cells the largest faller was not valid and the walk went deeper; 119 for the riser; 0 cells still met an unrated word (0 after `--rate`).
