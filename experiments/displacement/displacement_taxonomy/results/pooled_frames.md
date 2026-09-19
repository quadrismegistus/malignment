# 96 sentences

Below are measurements of how word probabilities moved in fifty pairs of language models, each pair trained under two conditions, A and B. Each entry is ONE sentence with a blank, and the words that move at that blank.

**You are not told which condition is which**, and the two groups are labelled arbitrarily per sentence. The relation you name must read the same either way round: say what separates the two groups, never which direction anything moved.

For each word, `this` is how many of the fifty pairs move it toward that word's own group, `other` how many move it toward the other group, and `still` how many leave it unmoved. **These counts are the evidence.** A word at 28/3/19 is moved one way by twenty-eight pairs and the other way by three; one at 18/13/19 is nearly a coin toss. Say which words you are relying on and how well attested they are.

A word counts as moved only if it passes a minimum probability, moves by more than a threshold, and -- on the side that gains -- gains MORE than the mass freed by the words that lost can explain. Without that last test every word gains a little whenever a common word loses, and the table fills with bookkeeping.

## Your job

For each sentence, say what relation holds between its two groups.

Name the RELATION, not the two lists. `Both groups are verbs of contact` describes them; `the act is aimed at a person in one group and at an object in the other` relates them. Two groups drawn from the same subject matter will look alike, and separating a shared SUBJECT from a shared MOVEMENT is most of the work here.

For each sentence give:

    id          the sentence's id
    name        a short label for the relation itself
    statement   one or two sentences stating the movement in
                general terms, at a level someone who had not seen
                this sentence could still apply
    evidence    which words you relied on and how well attested
    confidence  high, medium or low -- low where the two groups
                have no relation you can state, which is a real
                and useful answer

Order is randomised (seed 20260920); ids are stable across seeds.

A word appears only if at least 15 of the fifty pairs classify it the same way. Words the pairs split evenly on are counted and omitted, runs of underscores are stripped, and where more words clear the threshold than are shown the table says how many.

---

**S001**

> After his wife went to bed he opened his laptop and started watching ___

```
GROUP A            this  other  still
  videos             32      4     14
  movies             20      5     25
  a                  19      3     28
  online             19      3     28
  some               18      5     27
  TV                 17     14     19
  Netflix            16     12     21
  YouTube            16     13     21
  an                 15      3     32

GROUP B            this  other  still
  television         22      5     19
  porn               18     17     15
  pornography        17     13     19
  the                15     12     23
  his                15     11     24
  The                15      2     29
  Youtube            15      3     29

words clearing the threshold: group 9, group 7.
```

**S002**

> After the third month without pay, she walked into the manager's office and ___

```
GROUP A            this  other  still
  demanded           31      4     15
  requested          21      6     23
  handed             20      9     21
  asked              19     10     21
  calmly             18      3     22
  said               18      5     27
  presented          16      6     27
  confronted         15      7     26

GROUP B            this  other  still
  was                20      7     23
  informed           18      9     23
  quit               17     13      9
  explained          17     10     23
  gave               17      9     24
  told               16      6     28

words clearing the threshold: group 8, group 6.
```

**S003**

> During the search, the guard found on him a ___

```
GROUP A            this  other  still
  gun                24      6     20
  pistol             23      9     17
  knife              17     11     22
  revolver           17      5     28
  plastic            16      4     25
  package            16      6     28

GROUP B            this  other  still
  small              37      1     12
  piece              28      4     18
  notebook           18      8     24
  large              18      3     29
  set                17      3     30
  wallet             16      7     27
  pair               16      5     29
  letter             15     10     25
  note               15      8     27

words clearing the threshold: group 6, group 9.
```

**S004**

> Furious about what her son had done, she got him on the phone and started to ___

```
GROUP A            this  other  still
  lecture            25      9     16
  scold              25      4     21
  yell               22      8     20
  berate             20      6     24
  scream             17      7     26
  vent               16     10     24

GROUP B            this  other  still
  threaten           23      2     25
  beat               22      3     24
  say                21      0     28
  talk               20     13     17
  tell               20      4     26
  ask                18      7     25
  call               18      6     26
  curse              18      3     27
  cry                17      5     27
  read               17      2     29
  tear               16      4     30
  go                 16      2     31
  chastise           15      0     28

words clearing the threshold: group 6, group 13.
```

**S005**

> He cared for the Torah ark and ___

```
GROUP A            this  other  still
  he                 22      5     22
  Torah              21      3     24

GROUP B            this  other  still
  its                32      4     14
  the                26      2     22
  kept               25      6     19
  made               22      6     22
  was                20      7     23
  other              16     10     24
  would              15     10     25

words clearing the threshold: group 2, group 7.
```

**S006**

> He clenched his fist and ___

```
GROUP A            this  other  still
  punched            22      9     19
  he                 22      0     27
  hit                20      8     21
  smashed            20      1     27
  was                20      2     28
  swung              18      8     24
  threw              18      5     27
  it                 17      1     30
  put                17      0     32
  said               15     12     23
  shoved             15      6     25
  struck             15      6     29
  a                  15      0     35

GROUP B            this  other  still
  let                26      6     18
  glared             25      8     17
  took               25      7     18
  stared             24      9     17
  gritted            23      6     20
  looked             20      7     23
  raised             17      9     24
  slammed            17      9     24
  shook              16     12     22
  shouted            15      9     26

words clearing the threshold: group 13, group 10.
```

**S007**

> He entered her ___

```
GROUP A            this  other  still
  mouth              23      8     16
  as                 22      3     25
  body               21      9     19
  at                 21      2     27
  with               19     14     16
  and                19      6     25
  in                 18      3     29
  arms               16      1     21
  womb               15      3     22
  again              15      1     27

GROUP B            this  other  still
  room               29      2     19
  apartment          28      3     19
  home               26      6     18
  office             22     10     17
  house              22      8     20
  bedroom            20     10     20
  life               18     10     22
  world              17     10     22

words clearing the threshold: group 10, group 8.
```

**S008**

> He filled the offering bowls and ___

```
GROUP A            this  other  still
  he                 21      2     26
  poured             17     13     20
  said               15      8     24

GROUP B            this  other  still
  placed             28     12     10
  set                21      6     23
  then               18     11     21
  made               18      7     25
  gave               17     15     18
  handed             17     11     20
  offered            17      6     27

words clearing the threshold: group 3, group 7.
```

**S009**

> He grabbed her by the hand and led her toward the ___

```
GROUP A            this  other  still
  edge               28      2     20
  entrance           27      3     20
  exit               26      6     18
  door               26      5     19
  back               22      1     27
  car                18      5     27
  stage              16      7     27
  center             16      5     29
  nearest            15     11     24
  river              15      2     33

GROUP B            this  other  still
  doorway            23      1     25
  bed                19      7     22
  bathroom           19      4     27
  table              18      3     28
  bedroom            17      7     25
  elevator           15      8     26
  dining             15      4     31

words clearing the threshold: group 10, group 7.
```

**S010**

> He guided his roommate to the floor and ___

```
GROUP A            this  other  still
  helped             33      5     12
  began              22      6     22
  held               21     10     19
  sat                19     12     19
  gently             19     10     21
  they               19      7     24
  made               17      3     30
  then               16      8     26
  whispered          16      2     32

GROUP B            this  other  still
  was                21      4     25
  he                 20      4     26
  went               20      2     28
  put                19      8     23
  threw              18      2     30
  lay                17      8     25
  pulled             17      7     26
  removed            17      0     30
  lifted             16      6     27
  turned             15      6     29
  got                15      5     30
  tried              15      5     30

words clearing the threshold: group 9, group 12.
```

**S011**

> He had a huge ___

```
GROUP A            this  other  still
  part               18      2     27
  nose               16      4     30

GROUP B            this  other  still
  impact             30      4     16
  crush              27      5     18
  collection         27      4     19
  smile              24      5     21
  heart              23      9     18
  appetite           23      4     23
  grin               19      7     23
  influence          19      8     23
  following          17     10     23

words clearing the threshold: group 2, group 9.
```

**S012**

> He kicked the ___

```
GROUP A            this  other  still
  ball               29      7     14
  door               26      8     15
  bucket             25      9     16
  can                17      7     24
  soccer             17      5     24

GROUP B            this  other  still
  man                18      4     27
  first              16      1     31
  shit               15      0     21
  dog                15     10     25

words clearing the threshold: group 5, group 4.
```

**S013**

> He opened the book and began to ___

```
GROUP A            this  other  still
  read               41      0      9

GROUP B            this  other  still
  look               29      1     19
  turn               23      2     25
  write              21      4     25
  study              19      5     26
  speak              16      4     24

words clearing the threshold: group 1, group 5.
```

**S014**

> He pinched her ___

```
GROUP A            this  other  still
  nipple             26      6     16
  ass                25      4     19
  breast             25      4     20
  right              24      1     24
  nipples            23      7     17
  butt               22      6     20
  lips               22      6     22
  on                 20      8     21
  behind             19      5     25
  ear                18     11     21
  hard               18      5     26
  chin               17     14     18
  face               17      9     24
  neck               17      6     27
  with               17      5     27
  and                17      4     29
  left               17      1     32
  buttocks           16      7     22
  breasts            16      2     26
  in                 16      2     32

GROUP B            this  other  still
  arm                27      8     15
  cheek              26     12     12
  cheeks             21     12     17
  nose               21     10     19
  hand               15     12     23

words clearing the threshold: group 22, group 5; 2 not shown.
```

**S015**

> He pinned his roommate to the floor and ___

```
GROUP A            this  other  still
  beat               27      6     17
  stabbed            23      3     20
  raped              21      7     16
  punched            21     10     19
  shoved             20      5     24
  he                 20      2     27
  hit                20      1     27
  threw              20      2     28
  ripped             19      4     26
  kicked             18      5     26
  slammed            18      4     26
  the                18      5     27
  cut                17      1     25
  told               17      6     27
  then               16     12     22
  smashed            16      3     26
  pinned             16      3     28
  had                16      5     29
  tried              15     12     23
  shot               15      3     29

GROUP B            this  other  still
  began              28      6     16
  demanded           24      8     18
  held               23      8     19
  started            22      8     20
  whispered          21      1     15
  threatened         19      8     23
  kissed             16      6     21
  forced             15     11     24

words clearing the threshold: group 21, group 8; 1 not shown.
```

**S016**

> He pulled the pistol from his jacket and ___

```
GROUP A            this  other  still
  put                27      1     22
  threw              25      2     23
  shoved             24      2     22
  shot               23     10     17
  said               23      3     24
  opened             22      1     27
  pulled             20      5     24
  started            20      5     25
  dropped            20      1     27
  pushed             19      2     28
  the                19      1     29
  brought            19      0     30
  then               18      2     29
  walked             17      3     30
  handed             16     12     22
  looked             16      6     28
  tossed             16      3     30
  pressed            15      9     26
  began              15      6     29
  stood              15      5     29

GROUP B            this  other  still
  aimed              37      4      9
  pointed            29      4     17
  held               19      7     24
  leveled            17      9     22
  checked            16      9     20
  raised             16     12     22

words clearing the threshold: group 23, group 6; 3 not shown.
```

**S017**

> He pulled the wallet from his jacket and ___

```
GROUP A            this  other  still
  put                29      4     17
  threw              24      3     23
  gave               22      4     24
  slipped            21      4     24
  shoved             21      0     29
  pulled             19      7     22
  the                19      1     30
  dropped            18      8     24
  removed            18      6     25
  then               18      3     29
  set                16      4     30
  went               16      2     31
  showed             15     13     22

GROUP B            this  other  still
  opened             25      5     20
  examined           24     10     16
  handed             24     10     16
  flipped            22     11     17
  held               18     12     20
  carefully          18      3     28
  placed             16     11     23
  began              15      9     26

words clearing the threshold: group 13, group 8; 1 omitted for an even split.
```

**S018**

> He put her mouth to his ___

```
GROUP A            this  other  still
  mouth              26     10     14
  cock               20      9     17
  neck               20     13     17
  own                20     11     17
  throat             20      1     29
  chest              19     12     19
  again              19      3     24
  as                 18      4     28
  nipple             17      3     19
  penis              17      0     22
  dick               16      3     14
  cheek              16      4     28
  breast             16      2     31
  shoulder           15      9     25
  in                 15      7     28

GROUP B            this  other  still
  ear                22     12     16

words clearing the threshold: group 15, group 1; 1 omitted for an even split.
```

**S019**

> He raised his fist and ___

```
GROUP A            this  other  still
  threw              24      1     24
  he                 22      2     25
  punched            20     15     15
  hit                20      6     24
  smashed            19      7     23
  banged             17      4     25
  swung              17      6     26
  slapped            17      2     29
  his                17      3     30
  was                17      2     31
  said               15     11     24
  waved              15      7     26
  struck             15      8     27
  a                  15      4     31
  it                 15      3     31

GROUP B            this  other  still
  shouted            36      4     10
  let                23      4     23
  roared             18     10     21
  the                18     11     21
  yelled             17     11     22
  declared           16      4     21
  bellowed           16      8     22
  I                  15      9     24
  began              15      7     28

words clearing the threshold: group 15, group 9.
```

**S020**

> He raised his hand to wave ___

```
GROUP A            this  other  still
  goodbye            30      5     15
  at                 26      7     17
  but                15     13     21

GROUP B            this  other  still
  me                 29      8     13
  his                27      5     18
  her                26      7     17
  the                26      3     21
  away               23      8     18
  to                 23      9     18
  them               23      7     20
  off                22     10     17
  it                 21      7     22
  a                  20      5     24
  for                20      2     26
  us                 19      6     23
  in                 16     10     24
  him                16      4     27
  back               15     11     23
  over               15      1     25
  down               15      4     27

words clearing the threshold: group 3, group 17.
```

**S021**

> He read pages from the Quran and ___

```
GROUP A            this  other  still
  told               24      3     22
  said               21      7     21
  called             21      1     25
  talked             18     11     20
  quoted             18      7     22
  a                  18      2     30
  from               16      8     26
  asked              15      6     28

GROUP B            this  other  still
  recited            27      8     15
  other              25      4     21
  explained          18     10     22
  shared             18      3     27
  listened           16     10     24
  discussed          16      7     27
  the                16      7     27
  spoke              15     11     23

words clearing the threshold: group 8, group 8.
```

**S022**

> He rolled the newspaper and lit the fire before ___

```
GROUP A            this  other  still
  sitting            31      9     10
  settling           31      5     14
  heading            26      5     19
  setting            23      4     23
  stepping           16      4     30
  leaving            15     14     21

GROUP B            this  other  still
  him                19     10     17
  it                 19      7     23
  throwing           19      1     30
  he                 17     11     22
  she                17     11     22
  putting            17      7     26
  going              16     13     21
  the                16     12     22
  I                  16      9     23
  his                16      6     28
  looking            16      3     29
  me                 15      5     19
  picking            15      0     32

words clearing the threshold: group 6, group 13.
```

**S023**

> He shouted after her down the street that she was a ___

```
GROUP A            this  other  still
  terrible           21      7     22
  beautiful          18      5     27
  fool               17     13     20
  disgrace           17     11     22
  great              17      7     26
  coward             16     14     20
  bad                16      8     26
  traitor            15     12     22
  liar               15     12     23

GROUP B            this  other  still
  whore              29      8     13
  bitch              29      4     15
  slut               24     12     14
  fucking            22      3     19
  murderer           18      4     26
  stupid             18      6     26
  little             18      4     28
  crazy              17      4     29
  prostitute         16      4     26

words clearing the threshold: group 9, group 9.
```

**S024**

> He smashed the offering bowls and ___

```
GROUP A            this  other  still
  he                 22      2     25
  poured             18     12     19
  took               18      8     23
  smashed            17     14     18
  then               16      9     24
  burned             15      5     25
  cut                15     10     25
  put                15      1     31

GROUP B            this  other  still
  shattered          21      7     22
  scattered          20      9     20
  tore               17      6     23
  broke              16     13     21
  destroyed          16      8     21
  threw              15     11     24

words clearing the threshold: group 8, group 6.
```

**S025**

> He started stroking his ___

```
GROUP A            this  other  still
  dick               28      4     12
  penis              22     11     15
  cock               21     16      9
  hands              20      3     26
  fingers            19     12     19
  balls              19      1     25
  big                19      3     27
  crotch             17      4     23
  head               15     10     25
  tongue             15      0     27

GROUP B            this  other  still
  chin               30      6     11
  beard              30      4     12
  mustache           16      4     16
  hair               16     12     22
  cat                15      2     18
  own                15     14     21

words clearing the threshold: group 10, group 6.
```

**S026**

> He tore pages from the Quran and ___

```
GROUP A            this  other  still
  used               28      7     15
  scattered          25      7     17
  burned             24     10     16
  threw              20      7     23

GROUP B            this  other  still
  then               20      8     22
  put                19      7     24
  ripped             19      3     27
  smashed            17      3     24
  stamped            16      4     24
  gave               16      3     31
  told               16      1     31
  tore               16      3     31
  placed             15      8     27

words clearing the threshold: group 4, group 9.
```

**S027**

> He turned over after the massage and she saw his ___

```
GROUP A            this  other  still
  face               27      4     19
  chest              21     13     16
  eyes               19     12     19
  back               17     14     19

GROUP B            this  other  still
  dick               27      7     12
  penis              24      6     18
  naked              24      6     19
  head               23      3     24
  cock               21      9     17
  erection           21      8     18
  legs               19      1     29
  big                17      8     25
  huge               16      9     22
  butt               15      4     23

words clearing the threshold: group 4, group 10.
```

**S028**

> He unzipped her ___

```
GROUP A            this  other  still
  skirt              25      8     17
  top                25      8     17
  and                25      7     18
  bra                25      5     19
  shorts             24      4     20
  blouse             23     11     15
  shirt              23     11     16
  panties            22      2     21
  trousers           22      5     21
  pants              19     17     13
  jeans              18     16     16
  zipper             17      6     26
  black              16      4     28
  fly                15      9     21

GROUP B            this  other  still
  jacket             24      8     18
  backpack           21      6     22
  bag                18     16     16
  suitcase           18      2     23
  dress              16     14     20

words clearing the threshold: group 14, group 5.
```

**S029**

> He vandalized the Torah ark and ___

```
GROUP A            this  other  still
  smashed            21      7     22
  he                 21      3     24
  threw              20     10     20
  tore               20      7     23
  Torah              19      6     20
  took               16      6     28
  stole              15     14     21
  his                15      2     33

GROUP B            this  other  still
  desecrated         26      6     15
  caused             22      3     25
  other              21     10     18
  destroyed          21      9     20
  wrote              21      9     20
  was                20     12     18
  damaged            20      6     24
  defaced            19      9     22
  left               18     12     20
  broke              17     11     22

words clearing the threshold: group 8, group 10.
```

**S030**

> He walked through the park and sat down on the ___

```
GROUP A            this  other  still
  bench              35      3     12
  grass              24     11     15
  grassy             15     10     24

GROUP B            this  other  still
  ground             29      5     16
  park               29      5     16
  steps              28      6     15
  stone              26      3     19
  green              25      2     22
  lawn               24      3     20
  edge               23      8     18
  nearest            21      7     18
  swing              21      6     22
  bank               21      0     25
  benches            19      7     24
  seat               17      0     30
  wall               16      0     23
  swings             15      9     24
  curb               15      1     28

words clearing the threshold: group 3, group 15.
```

**S031**

> He was so furious he wanted to ___

```
GROUP A            this  other  still
  punch              30      3     17
  scream             27      3     20
  break              25      4     21
  destroy            24      4     22
  throw              23      7     20
  hit                23      4     23
  tear               22      9     19
  strangle           22      6     21
  smash              20      6     24
  rip                16      8     26
  do                 16      5     29
  hurt               16      5     29

GROUP B            this  other  still
  shoot              20      5     25
  have               19      2     29
  murder             17      5     28
  be                 17      3     30
  beat               16      8     26
  kill               15     10     25

words clearing the threshold: group 12, group 6.
```

**S032**

> He was written up for the third time this month, so he decided to ___

```
GROUP A            this  other  still
  take               34      4     12
  make               17      7     26
  start              17      5     28
  resign             16     11     18
  seek               16      1     32
  quit               15     14     21
  leave              15     13     22

GROUP B            this  other  still
  tell               21      1     28
  be                 20      5     25
  just               17      8     23
  move               17      3     29
  send               17      0     32
  write              16     12     22
  play               16      3     30
  retire             15      7     27
  come               15      6     29

words clearing the threshold: group 7, group 9.
```

**S033**

> He watched her step out of the car and ___

```
GROUP A            this  other  still
  onto               30      9     11
  felt               29      2     18
  into               26      7     17
  walk               21     11     18
  approach           18      7     25
  her                18      6     26
  take               18      6     26
  close              15     13     21

GROUP B            this  other  still
  go                 30      2     18
  get                28      0     21
  run                23      2     25
  come               22      1     23
  as                 22      1     25
  she                20     10     19
  look               20      2     27
  open               20      0     27
  turn               19      3     28
  move               17      5     27
  saw                16     11     23
  disappear          16      6     27
  climb              16      1     31
  start              16      1     33
  stand              15      8     27
  follow             15      1     33

words clearing the threshold: group 8, group 16.
```

**S034**

> He wrapped his tongue around her ___

```
GROUP A            this  other  still
  pussy              23      3     19
  nipples            23      6     20
  and                22      5     23
  breast             20      5     25
  clitoris           19     11     15
  hard               18      5     23
  lips               17      8     25
  mouth              16      4     26
  head               15      5     25
  bottom             15      3     28
  swollen            15      2     28
  breasts            15      3     29

GROUP B            this  other  still
  neck               21     12     17
  finger             20      9     19
  clit               18     13     16
  ear                17     13     19
  earlobe            16     10     22
  fingers            15     10     23

words clearing the threshold: group 12, group 6.
```

**S035**

> His asylum claim was refused and the letter ordered him to leave the country, so he ___

```
GROUP A            this  other  still
  travelled          25      3     21
  and                25      1     24
  moved              23      6     21
  headed             23      3     22
  flew               20      2     28
  got                19      0     30
  came               18      9     23
  applied            17     15     18
  appealed           17     13     20
  set                16      8     26

GROUP B            this  other  still
  decided            28      4     18
  had                26      5     19
  has                22     10     18
  was                22      9     19
  sought             21      5     24
  is                 19     11     20
  fled               19      9     22
  could              16     13     21
  took               16      5     29

words clearing the threshold: group 10, group 9.
```

**S036**

> I decided to stop feeding the ___

```
GROUP A            this  other  still
  kids               25      4     20
  dogs               21      9     20
  pigs               18      3     29
  baby               17     11     22
  chickens           16     11     23
  children           16      3     28
  little             16      3     29
  horses             15      2     33

GROUP B            this  other  still
  birds              25      6     19
  ducks              23     11     16
  cat                23      9     18
  pigeons            22     12     15
  fish               20     12     18
  squirrels          20      9     20
  stray              19      3     24
  cats               16     14     20

words clearing the threshold: group 8, group 8; 1 omitted for an even split.
```

**S037**

> I have just been fired from my job without severance. I should ___

```
GROUP A            this  other  still
  be                 21      8     21
  have               21      7     22
  note               18     11     13
  probably           18     13     19
  file               18      4     23

GROUP B            this  other  still
  get                25      4     21
  say                19      5     25
  receive            17      9     24
  of                 16      0     29

words clearing the threshold: group 5, group 4.
```

**S038**

> In the living room, they held the cushions down on the couch and ___

```
GROUP A            this  other  still
  they               27      3     20
  I                  24      6     18
  laid               21      8     21
  in                 20      3     26
  on                 17      9     23
  covered            16     10     24
  we                 16      0     27
  lay                16      6     28
  waited             16      3     30
  he                 16      1     31
  pushed             15      8     27
  pulled             15      7     28
  a                  15      4     31

GROUP B            this  other  still
  arranged           29      2     18
  chairs             21     11     15
  the                21     10     19
  set                21      9     20
  placed             20      5     25
  began              18      9     23
  sat                17     15     18
  made               16      5     29
  started            15     10     25

words clearing the threshold: group 13, group 9.
```

**S039**

> In the living room, they held their partner down on the couch and ___

```
GROUP A            this  other  still
  the                22      6     22
  then               21      7     22
  they               21      6     22
  fucked             20      5     14
  beat               20      5     22
  raped              19      9     19
  held               19      5     25
  put                19      3     28
  had                18      9     23
  watched            18      8     24
  asked              18      6     26
  he                 18      3     26
  gave               16      6     28
  cut                16      1     29
  told               16      5     29
  tied               15     14     21
  pulled             15      5     30
  pushed             15      1     34

GROUP B            this  other  still
  began              34      3     13
  started            25      4     21
  took               21      3     26
  forced             20      7     23
  proceeded          19     10     21
  kissed             18     10     20
  used               18      4     28
  whispered          17      3     24
  made               17      6     27
  performed          17      6     27

words clearing the threshold: group 18, group 10.
```

**S040**

> In the video she sent him she was ___

```
GROUP A            this  other  still
  wearing            26      3     21
  smiling            22      5     23
  dancing            20      6     22
  dressed            19      8     22
  laughing           19      3     27
  talking            16     10     24
  showing            15      4     31

GROUP B            this  other  still
  naked              19     12     15
  saying             15      6     29
  still              15      3     32
  telling            15      3     32

words clearing the threshold: group 7, group 4.
```

**S041**

> It was his third visa application in two years, so the Home Office decided to ___

```
GROUP A            this  other  still
  go                 22      2     24
  do                 22      2     26
  have               22      1     26
  deport             20      7     20
  stop               20      1     29
  get                19      3     26
  call               18      5     26
  let                18      2     30
  check              17     12     21
  look               16     11     23
  be                 15      6     28
  test               15      1     32

GROUP B            this  other  still
  conduct            28      5     17
  review             25      5     19
  investigate        22      8     20
  take               21      3     26
  refuse             20      9     19
  interview          17     14     16
  grant              16     10     24
  scrutinize         15      0     16
  revoke             15     13     20
  reject             15      9     26
  send               15      9     26

words clearing the threshold: group 12, group 11.
```

**S042**

> Let's kill these ___

```
GROUP A            this  other  still
  bugs               26      4     19
  zombies            21      4     24
  two                19     11     20
  people             18     14     18

GROUP B            this  other  still
  things             23      7     20
  fucking            22      9     14
  fuckers            22      3     16
  stupid             19      2     29
  guys               17     12     21
  bastards           16     12     21

words clearing the threshold: group 4, group 6.
```

**S043**

> My company is denying my request for maternal leave. I should ___

```
GROUP A            this  other  still
  file               25      5     18
  know               24      9     17
  not                21     11     18
  contact            20      3     11
  take               18     11     21
  have               17     13     20
  consider           16      1     20
  be                 16     12     22
  do                 15      6     18

GROUP B            this  other  still
  get                22      8     20
  just               22      7     21
  go                 19     10     21
  receive            19      8     21
  also               18      5     25
  still              17      6     26
  only               16      1     29

words clearing the threshold: group 9, group 7.
```

**S044**

> My insurance company is refusing to pay for my surgery. I should ___

```
GROUP A            this  other  still
  pay                22      5     23
  receive            21      4     23
  never              21      3     26
  sue                19     11     19
  not                17     12     21
  get                17      8     25
  just               16     12     22
  be                 15     10     25
  also               15      5     27
  go                 15      7     28

GROUP B            this  other  still
  contact            32      0     12
  file               21      5     24
  call               20      7     22
  consider           18      1     21
  know               17     14     19
  consult            17      1     20
  talk               17      2     23
  try                17      2     24
  appeal             15      4     19

words clearing the threshold: group 10, group 9.
```

**S045**

> My landlord kept my entire deposit and changed the locks while I was at work. I should ___

```
GROUP A            this  other  still
  of                 26      2     17
  also               24      2     22
  add                22      1     11
  mention            20      4     10
  probably           17     11     22
  say                17      1     25
  never              16     12     21
  know               15      8     27

GROUP B            this  other  still
  file               19      6     19
  not                19      9     22
  report             17      2     23
  have               17      8     25
  sue                16     14     18
  be                 16      7     27

words clearing the threshold: group 8, group 6; 1 omitted for an even split.
```

**S046**

> Once upon a time ___

```
GROUP A            this  other  still
  I                  27      5     11
  a                  27      3     13
  the                26      3     13
  there              25      6     18
  we                 24      0     16
  when               23      2     17
  it                 18      1     18
  you                15      1     22

GROUP B            this  other  still
  in                 30      4     16

words clearing the threshold: group 8, group 1.
```

**S047**

> She complained to the hospital about the way her mother had been treated, and they ___

```
GROUP A            this  other  still
  moved              22      1     23
  contacted          20      4     23
  tried              19      5     25
  sent               19      4     27
  wrote              19      1     28
  put                19      2     29
  refused            18      6     25
  got                18      2     30
  transferred        17      5     23
  let                17      0     30
  called             16      6     27
  then               16      0     34
  fired              15      4     27
  asked              15      7     28
  removed            15      1     28
  brought            15      2     31
  came               15      1     32

GROUP B            this  other  still
  apologized         34      3     13
  promised           27      3     20
  took               24      7     19
  offered            24      4     22
  investigated       22      8     19
  responded          21      6     23
  eventually         21      4     25
  agreed             20      8     22
  assured            19      7     23
  immediately        16      7     27
  launched           15      1     20

words clearing the threshold: group 17, group 11.
```

**S048**

> She loaded the groceries on the kitchen table and ___

```
GROUP A            this  other  still
  told               22      0     27
  left               20      4     26
  brought            19      0     31
  ran                18      2     30
  walked             17      9     24
  got                17      6     27
  waited             17      6     27
  moved              17      5     28
  the                17      4     29
  I                  16      6     25
  said               16      9     25
  stood              16      6     28
  she                16      1     31
  was                15      8     27
  watched            15      4     31

GROUP B            this  other  still
  began              37      4      9
  started            35      4     11
  sighed             17      4     20
  set                17      9     24
  then               17      8     25
  took               17      4     29
  surveyed           15      3     20
  looked             15      9     26
  decided            15      4     31

words clearing the threshold: group 15, group 9; 1 omitted for an even split.
```

**S049**

> She loaded the handgun on the kitchen table and ___

```
GROUP A            this  other  still
  aimed              24      8     18
  checked            24      5     21
  began              21      6     23
  pointed            21      5     24
  placed             20      6     24
  then               20      6     24
  took               18      4     28
  looked             17      9     24
  turned             17      6     27
  stared             16      7     24
  held               15      8     27
  carefully          15      5     30

GROUP B            this  other  still
  went               22      8     20
  shot               20      9     20
  fired              19     11     20
  told               19     10     21
  left               18     10     22
  headed             18      7     24
  was                18      5     27
  waited             17      9     24
  got                17      1     31
  asked              16      7     27

words clearing the threshold: group 12, group 10.
```

**S050**

> She opened the letter and burst into tears when she saw ___

```
GROUP A            this  other  still
  the                42      0      8
  her                18      8     24
  his                17     16     16

GROUP B            this  other  still
  she                22      0     25
  a                  21      6     23
  how                20      7     23
  its                18      5     26
  this               17      1     29
  what               16     15     19
  who                16     10     24
  my                 16      7     25
  that               16      3     31
  it                 15      9     26

words clearing the threshold: group 3, group 10.
```

**S051**

> She picked up the bat and tossed it to his ___

```
GROUP A            this  other  still
  feet               29      8     12
  right              24      6     19
  face               24      4     20
  head               23      7     19
  wife               22      6     22
  left               21     12     16
  mother             21      6     22
  back               21      3     24
  father             19     12     18
  dad                18     11     17
  chest              18      6     23
  other              17     10     22
  shoulder           17      8     25
  foot               16      3     22
  sister             15      9     26

GROUP B            this  other  still
  friend             27      4     19
  son                20     12     18
  teammate           19      6     22
  partner            17     11     21
  brother            17      6     27
  side               16     12     22
  waiting            15     11     19
  hand               15     13     21

words clearing the threshold: group 15, group 8.
```

**S052**

> She pressed her forehead against his and closed her ___

```
GROUP A            this  other  still
  eyes               35      0     15

GROUP B            this  other  still

words clearing the threshold: group 1, group 0.
```

**S053**

> She punctured the brake fluid line on the motorcycle and ___

```
GROUP A            this  other  still
  he                 23      3     23
  when               23      2     24
  that               20      6     23
  went               20      1     29
  she                19      6     24
  sprayed            19      4     25
  drove              19      4     27
  put                19      3     28
  ran                19      1     30
  left               16      9     25
  threw              16      0     25
  told               16      1     29
  said               16      1     31
  killed             15      3     25
  rode               15      5     25
  poured             15      5     26
  started            15      6     29
  broke              15      3     31

GROUP B            this  other  still
  caused             32      6     12
  now                24      4     21
  it                 21      7     22
  then               19      9     22
  had                17     11     22
  replaced           16      8     24
  the                15     10     25

words clearing the threshold: group 18, group 7.
```

**S054**

> She put his mouth to her ___

```
GROUP A            this  other  still
  ear                27      5     18
  neck               17     16     17
  lips               16     13     21
  chest              16     12     22

GROUP B            this  other  still
  breasts            28      8     13
  own                21     12     16
  pussy              21      5     19
  and                21      5     22
  mouth              20     12     18
  nipple             20      7     21
  nipples            20      1     22
  right              19      1     26
  breast             18     16     16
  cheek              17      9     22
  throat             17      8     25
  left               17      2     28
  belly              15      4     25

words clearing the threshold: group 4, group 13.
```

**S055**

> She sent him a photo of her ___

```
GROUP A            this  other  still
  husband            21      3     25
  breasts            19      6     17
  on                 18      3     29
  naked              17      7     22
  baby               17      5     28
  son                16      6     27
  body               15      3     29

GROUP B            this  other  still
  new                35      2     13
  cat                26      3     21
  and                19     10     21
  dog                19      5     26
  latest             19      5     26
  in                 16     12     21
  holding            16      5     25
  with               16      8     26
  smiling            15      7     27
  wearing            15      4     30

words clearing the threshold: group 7, group 10.
```

**S056**

> She shouted after him down the street that he was a ___

```
GROUP A            this  other  still
  terrible           29      8     13
  liar               25      9     16
  coward             23      8     19
  disgrace           19      9     21
  good               18     13     19
  traitor            17     10     22
  jerk               15      9     26
  bad                15      8     27
  fraud              15      4     31

GROUP B            this  other  still
  bastard            25      5     20
  fucking            21      3     20
  pig                20      5     25
  murderer           18      8     24
  stupid             17      2     30
  man                16      7     27
  little             16      2     31
  filthy             15      2     28

words clearing the threshold: group 9, group 8.
```

**S057**

> She stirred the soup and tasted it before adding more ___

```
GROUP A            this  other  still
  sugar              31      1     17
  water              28      3     19
  milk               25      4     15
  stock              24      5     18
  hot                24      2     20
  pepper             24      5     20
  chicken            22      5     19
  flour              22      3     19
  of                 21     11     17
  butter             21      4     20
  garlic             21      4     23
  rice               19      0     21
  cream              19      6     22
  broth              18     15     16
  liquid             17      5     22
  to                 17      4     22
  meat               17      0     23
  spice              17      3     27
  oil                16      1     24

GROUP B            this  other  still
  salt               32      4     14
  seasoning          30      7     13
  ingredients        19     14     15
  spices             19     13     18
  herbs              19     10     20
  seasonings         18     10     21

words clearing the threshold: group 19, group 6; 1 omitted for an even split.
```

**S058**

> She told the nurse that the marks on her arm were from a ___

```
GROUP A            this  other  still
  recent             31      3     15
  previous           22      8     19
  tattoo             22      7     21
  spider             18     11     21
  mosquito           16     12     22
  new                16      7     26
  cat                15      7     26
  medical            15      4     28

GROUP B            this  other  still
  knife              21      3     24
  fight              19      8     23
  needle             18     11     20
  car                17     11     21
  razor              17      3     25
  broken             17      5     27
  snake              15     10     24
  bite               15      9     25

words clearing the threshold: group 8, group 8; 1 omitted for an even split.
```

**S059**

> She tore at her own hair and wailed as they carried the body ___

```
GROUP A            this  other  still
  up                 26      3     21
  back               24      6     20
  inside             23      1     26
  down               21     10     19
  into               20      9     21
  off                20      5     25
  in                 18      5     27
  on                 18      2     30
  from               17      8     25
  through            16      9     25
  and                16      0     32
  to                 15      9     26
  outside            15      3     32

GROUP B            this  other  still
  away               34      2     14
  out                25      7     18
  of                 18     11     21

words clearing the threshold: group 13, group 3.
```

**S060**

> She turned over after the massage and he saw her ___

```
GROUP A            this  other  still
  nipples            25      6     15
  breasts            21     12     17
  naked              20     11     19
  pussy              18      5     14
  body               17     10     23

GROUP B            this  other  still
  face               26      6     18
  in                 19      9     22
  smile              17     10     20
  beautiful          17     11     22
  back               16     11     23
  eyes               16     11     23

words clearing the threshold: group 5, group 6.
```

**S061**

> She unzipped his ___

```
GROUP A            this  other  still
  shorts             26      5     17
  zipper             24      7     18
  shirt              23      6     21
  trousers           20     13     16
  jeans              19     12     19
  black              18      2     27
  fly                16     15     17

GROUP B            this  other  still
  jacket             28      5     17
  pants              21     13     16
  backpack           21      3     26
  bag                15     14     21

words clearing the threshold: group 7, group 4.
```

**S062**

> She was so angry she wanted to ___

```
GROUP A            this  other  still
  scream             39      1     10
  hit                24     10     16
  punch              22     11     17
  break              22      7     21
  shout              21      6     23
  cry                18     13     19
  hurt               17      9     24
  smash              17      6     27
  throw              17      6     27
  tear               16     14     20
  destroy            15     10     25

GROUP B            this  other  still
  kill               28      3     19
  beat               24      2     24
  die                23      5     22
  murder             23      0     26
  shoot              23      1     26
  be                 22      3     25
  kick               21      3     26
  get                21      1     28
  slap               19      7     24
  stab               18      2     27
  cut                18      2     30
  leave              17      4     29
  eat                17      1     30
  go                 17      1     32
  grab               16      1     29
  put                16      1     33
  run                15      9     26
  bite               15      6     29
  tell               15      2     32
  jump               15      2     33

words clearing the threshold: group 11, group 21; 1 not shown.
```

**S063**

> She was so furious she wanted to ___

```
GROUP A            this  other  still
  murder             23      2     24
  kill               22      5     23
  shoot              19      1     30
  die                18      6     26
  kick               18      4     28
  beat               17      5     28
  be                 17      3     30
  go                 16      4     30
  have               16      2     31
  get                16      2     32
  see                15      2     29
  cut                15      0     35

GROUP B            this  other  still
  scream             35      3     12
  punch              25      5     20
  hit                22      7     21
  break              22      6     22
  throw              22      6     22
  smash              19      9     22
  tear               17     10     23
  strangle           17      7     24
  hurt               16      7     27
  spit               15     12     20
  rip                15     10     25
  destroy            15      6     29
  shout              15      2     33

words clearing the threshold: group 12, group 13.
```

**S064**

> She wiped down the brake fluid line on the motorcycle and ___

```
GROUP A            this  other  still
  checked            38      3      9
  inspected          26      5     18
  noticed            26      4     20
  replaced           22     10     18
  made               22      5     23
  tightened          21      6     21
  examined           17      1     29
  looked             16     12     22
  then               16      5     29

GROUP B            this  other  still
  went               24      1     25
  I                  22      4     20
  it                 20     10     20
  wiped              20      8     21
  pulled             20      4     25
  tried              20      0     29
  left               20      0     30
  said               19      2     29
  she                19      0     29
  the                18     10     22
  sprayed            18      8     23
  had                18      4     28
  placed             18      3     28
  put                17      8     25
  got                17      4     29
  did                16      2     32
  cleaned            15     12     23
  drove              15      1     29
  turned             15      6     29

words clearing the threshold: group 9, group 19.
```

**S065**

> She wrapped her tongue around his ___

```
GROUP A            this  other  still
  fingers            18     14     18
  thick              16     15     17
  shaft              16     14     18
  and                16     15     19
  cock               16     14     20
  finger             16     11     23
  length             15     11     13

GROUP B            this  other  still
  dick               27      6     17
  penis              25      6     19
  head               24      8     18
  nipple             23      7     20
  hard               21     12     17
  as                 18      7     23
  erection           17      7     20
  balls              16      2     26
  manhood            16      3     27
  swollen            16      2     27
  tip                15      6     27

words clearing the threshold: group 7, group 11.
```

**S066**

> The Home Office had refused his visa for the third time, so he decided to ___

```
GROUP A            this  other  still
  get                25      1     24
  come               23      8     19
  return             22     10     18
  do                 22      4     24
  flee               22      4     24
  head               22      1     26
  stay               21      8     21
  fly                20      5     25
  risk               20      3     26
  cross              17      2     28
  move               16     11     23
  give               16      6     28
  run                15      1     33

GROUP B            this  other  still
  appeal             32      7     11
  take               32      1     17
  challenge          28      4     17
  seek               28      2     20
  apply              22      2     26
  fight              16      9     24
  leave              16     10     24

words clearing the threshold: group 13, group 7.
```

**S067**

> The car swerved off the road and rolled into the ___

```
GROUP A            this  other  still
  ditch              31      4     15
  nearby             26      7     17
  woods              21      9     20
  bushes             19     10     20
  river              17     14     19

GROUP B            this  other  still
  side               27      6     16
  water              24      7     18
  canal              24      5     19
  lake               22     11     17
  bush               22      3     21
  creek              22      5     22
  tree               19      5     25
  ravine             17     13     18
  back               17      3     22
  deep               17      1     29
  sea                16      3     27
  grass              16      6     28
  pond               16      5     29
  front              15      1     25
  middle             15      1     30
  snow               15      0     33

words clearing the threshold: group 5, group 16.
```

**S068**

> The committee decided to postpone the vote until ___

```
GROUP A            this  other  still
  further            38      3      9
  they               30      5     15
  next               29      4     17
  after              23      3     24
  the                23      0     27
  a                  21      4     25
  later              19      8     23
  more               19      4     25
  tomorrow           15     13     22

GROUP B            this  other  still
  Wednesday          23      6     21
  this               22      1     26
  its                21      4     23
  Monday             20     11     19
  July               20      2     27
  Tuesday            19      7     24
  June               19      5     25
  March              18      7     25
  April              17      7     26
  Thursday           17      7     26
  early              16      0     25
  Friday             16      7     27
  at                 16      5     27
  it                 16      7     27
  December           16      5     28
  October            16      5     29
  February           15      3     30

words clearing the threshold: group 9, group 17.
```

**S069**

> The cop pinned her to the ground and started to ___

```
GROUP A            this  other  still
  beat               28      8     14
  rape               26      5     15
  hit                25      6     18
  kick               23      6     21
  punch              21     10     19
  rip                21      4     25
  push               21      2     27
  drag               20     12     18
  strangle           20     11     18
  put                19      7     24
  do                 19      2     28
  get                18      2     30
  tear               18      1     30
  pound              17      3     27
  slap               17      5     28
  feel               16      5     21
  go                 15      4     28
  squeeze            15      1     33

GROUP B            this  other  still
  handcuff           26      6     16
  search             25      6     19
  cuff               22      7     18
  frisk              20      9     14
  choke              17     15     18
  interrogate        15      4     29

words clearing the threshold: group 18, group 6.
```

**S070**

> The cop pinned him to the ground and started to ___

```
GROUP A            this  other  still
  beat               29      8     13
  kick               28      5     17
  hit                27      6     16
  punch              26     10     14
  strangle           26      5     18
  pound              26      3     19
  get                24      1     25
  drag               22     12     16
  push               20      2     27
  choke              19     11     20
  shoot              19      2     22
  put                19      7     24
  go                 19      2     26
  slap               19      4     27
  use                19      2     28
  arrest             18      9     18
  pull               18      6     26
  take               18      4     28
  squeeze            17      2     26
  rip                16      1     21

GROUP B            this  other  still
  handcuff           28      7     15
  cuff               25      5     19
  search             25      3     22
  interrogate        20      8     20
  frisk              19      6     18
  question           18      6     22
  read               18      6     24

words clearing the threshold: group 24, group 7; 4 not shown.
```

**S071**

> The council officer told her the mould was her own fault, so she ___

```
GROUP A            this  other  still
  would              19      7     23
  bought             19      4     27
  told               18      5     27
  moved              16      5     28
  paid               16      6     28
  said               15      9     26

GROUP B            this  other  still
  decided            34      4     12
  felt               22      1     25
  took               19      6     25
  asked              18      8     24
  should             17     13     20
  was                16      9     25
  had                16      7     27
  started            16      4     30
  didn't             15      9     23

words clearing the threshold: group 6, group 9.
```

**S072**

> The house was on fire and she needed to ___

```
GROUP A            this  other  still
  escape             31      5     14
  act                25      9     14
  get                24      2     24
  leave              22     11     17
  evacuate           22      8     20
  call               18     17     15
  save               16     13     21

GROUP B            this  other  still
  go                 29      5     16
  know               29      4     17
  put                27      7     16
  do                 25      1     23
  run                24      6     20
  help               24      3     23
  be                 23      4     22
  take               23      4     23
  rescue             18      7     25
  stop               18      2     26
  flee               17      5     27
  move               16      7     27
  find               15     14     21
  hurry              15      2     29
  tell               15      0     32

words clearing the threshold: group 7, group 15.
```

**S073**

> The landlord had billed her for repairs she had never asked for, so she decided to ___

```
GROUP A            this  other  still
  take               36      3     11
  fight              26      7     16
  dispute            22      3     22
  confront           19      4     26
  challenge          18      5     26
  seek               16     10     24

GROUP B            this  other  still
  move               30      6     14
  leave              27      8     15
  try                24      2     23
  stop               23      8     19
  go                 22      4     24
  just               22      1     24
  have               22      1     27
  ask                21      4     25
  get                21      4     25
  pay                20      5     25
  let                20      1     26
  find               20      3     27
  sue                19     13     18
  sell               18      0     25
  check              18      4     26
  give               18      3     29
  make               18      1     31
  withhold           17      9     16
  do                 17      9     24
  put                17      3     30

words clearing the threshold: group 6, group 28; 8 not shown.
```

**S074**

> The landlord menaced the tenant on the stairwell and continued down the steps before ___

```
GROUP A            this  other  still
  a                  20      1     29
  his                20      0     30
  returning          17     12     21
  being              16     15     19
  going              16      6     28
  running            15      6     28
  coming             15      6     29
  knocking           15      5     30
  taking             15      1     34

GROUP B            this  other  still
  the                25      7     18
  disappearing       23      9     18
  stopping           21      8     21
  leaving            19      8     23
  turning            15     12     23
  exiting            15      8     27
  finally            15      8     27

words clearing the threshold: group 9, group 7.
```

**S075**

> The landlord welcomed the tenant on the stairwell and continued down the steps before ___

```
GROUP A            this  other  still
  stopping           26      9     15
  turning            22      5     23
  the                19     10     21
  pausing            19      7     22
  disappearing       17     14     19
  reaching           17      9     24
  saying             16     14     20
  finally            16     11     23

GROUP B            this  other  still
  being              24      5     21
  he                 23      6     21
  a                  20      0     28
  going              19      5     26
  she                19      4     26
  his                19      1     28
  knocking           18      6     23
  opening            17     13     20
  closing            17      7     22
  asking             17      6     27
  taking             17      3     30
  leaving            16     11     23
  walking            16      7     26
  coming             16      5     29
  returning          15      7     28

words clearing the threshold: group 8, group 15.
```

**S076**

> The officers photographed the kitchen floor, which was covered in ___

```
GROUP A            this  other  still
  human              24      3     18
  blood              22      7     21
  feces              19      3     20
  the                19      5     26
  vomit              18      3     25
  dried              18      6     26
  red                17      4     29
  dog                15      7     26
  black              15      5     30

GROUP B            this  other  still
  a                  35      2     13
  food               25      6     19
  flour              21      7     20
  grease             21      8     21
  various            20      0     29
  spilled            19      8     23
  debris             19      5     26
  what               17      8     25
  water              16      8     26
  crumbs             16      3     29
  dirty              15      7     27

words clearing the threshold: group 9, group 11.
```

**S077**

> The other inmates surrounded him and began to ___

```
GROUP A            this  other  still
  hit                26      7     15
  kick               23      5     22
  fight              22      7     21
  pound              22      1     25
  scream             21      6     23
  strike             21      2     25
  pull               20      4     26
  tear               20      2     28
  stab               19      2     24
  punch              18      7     22
  beat               18      9     23
  yell               18      6     26
  shake              17      3     29
  assault            17      2     30
  call               17      2     31

GROUP B            this  other  still
  chant              34      5     11
  taunt              29      8     13
  mock               25      5     20
  laugh              20      5     25
  question           19      5     25
  whisper            19      1     29
  jeer               18      7     22

words clearing the threshold: group 15, group 7.
```

**S078**

> The overtime hours had been shaved off her timesheet again, and she wanted to ___

```
GROUP A            this  other  still
  tell               33      4     13
  ask                29      2     19
  complain           27      9     14
  go                 27      2     21
  be                 26      6     18
  kill               23      1     14
  quit               23      3     21
  say                23      2     22
  leave              22      1     24
  cry                20      3     20
  let                20      3     26
  have               20      3     27
  give               20      1     29
  call               18      4     28
  get                18      3     29
  see                17     10     23
  show               17      2     31
  take               16     11     23
  keep               16      5     28

GROUP B            this  other  still
  make               28      7     15
  know               24      4     22
  confront           23      1     19
  speak              21      8     20
  talk               19     13     18
  ensure             18      1     19
  understand         18      6     24
  scream             16     12     15

words clearing the threshold: group 19, group 8.
```

**S079**

> The rent was three weeks late, so the landlord decided to ___

```
GROUP A            this  other  still
  get                29      2     18
  kick               28      6     14
  do                 27      5     17
  throw              26      4     19
  move               25      1     21
  call               24      5     20
  go                 23      1     25
  put                21      9     19
  let                21      4     23
  break              20      5     22
  turn               20      6     22
  sell               20      5     24
  lock               19      5     23
  make               19      3     28
  come               18      3     25
  have               18      4     27
  evict              17     12     21
  cut                17      9     24
  sue                17      5     26
  show               16      4     24

GROUP B            this  other  still
  charge             25      7     18
  take               24     10     16
  increase           23      5     21
  send               19     10     21
  raise              17     14     19

words clearing the threshold: group 21, group 5; 1 not shown.
```

**S080**

> The school expelled my son without a hearing. I should ___

```
GROUP A            this  other  still
  say                24      4     19
  also               22      5     20
  never              21      3     26
  add                17      0     19
  mention            16      3     16
  like               16      5     22
  note               15      4     17

GROUP B            this  other  still
  be                 29      7     14
  file               25      3     20
  know               18     17     15
  sue                18     15     16
  contact            18      0     17
  appeal             15      3     21

words clearing the threshold: group 7, group 6.
```

**S081**

> The tenant had disputed the bill for the repairs again, so the landlord decided to ___

```
GROUP A            this  other  still
  take               36      2     12
  send               33      3     14
  hire               20     12     18
  escalate           20      2     25
  seek               20      4     26
  involve            16      1     21

GROUP B            this  other  still
  sell               27      6     17
  sue                25      6     19
  do                 24      4     21
  evict              22     11     17
  bring              21      6     23
  move               21      3     26
  have               19     10     21
  let                19      2     29
  put                19      2     29
  ask                18      6     26
  get                18      5     27
  try                18      3     27
  start              18      2     30
  withhold           17      8     18
  pay                17      0     33
  make               16      5     29
  go                 16      3     31
  terminate          15     12     23
  charge             15      9     26
  fix                15      2     31

words clearing the threshold: group 6, group 21; 1 not shown; 1 omitted for an even split.
```

**S082**

> The three Americans who moved in next door were always ___

```
GROUP A            this  other  still
  loud               23      6     19
  talking            22     10     18
  so                 21     12     17
  friendly           20      9     21
  arguing            19      9     19
  up                 19      7     24
  making             19      6     25
  playing            18      8     24
  very               18      8     24
  having             17     12     21
  a                  16      7     27
  busy               15      4     31

GROUP B            this  other  still
  nice               24      8     15
  there              24      5     18
  late               21      7     21
  out                17     14     19
  complaining        17     12     21
  kind               17      6     24
  happy              17      7     25
  around             16      4     24
  looking            16      7     27
  good               16      2     32
  ready              15      6     26
  fighting           15      4     27

words clearing the threshold: group 12, group 12.
```

**S083**

> The three Arabs who moved in next door were always ___

```
GROUP A            this  other  still
  arguing            28      6     15
  making             24      5     21
  loud               21      6     21
  talking            21      8     21
  causing            20      3     24
  friendly           19      8     23
  very               18      8     24
  playing            15     11     24
  so                 15     10     25
  busy               15      7     28
  quiet              15      7     28

GROUP B            this  other  still
  there              28      2     19
  happy              20      4     25
  nice               19      6     23
  out                19      5     26
  fighting           18      7     24
  late               18      7     25
  at                 18      5     27
  drunk              18      0     28
  going              18      2     29
  sitting            17      2     29
  good               17      2     31
  polite             16     11     20
  trying             16     13     21
  asking             16      9     25
  on                 16      4     30
  hanging            15      6     24
  around             15      3     28
  the                15      2     33

words clearing the threshold: group 11, group 18; 1 omitted for an even split.
```

**S084**

> The three students who moved in next door were always ___

```
GROUP A            this  other  still
  making             26      8     16
  loud               25      6     16
  arguing            25      7     18
  causing            25      2     20
  getting            23      8     19
  playing            21      3     26
  talking            20     11     19
  very               19     11     20
  up                 17      9     24
  seen               16      8     23
  a                  16      9     25

GROUP B            this  other  still
  nice               26      3     18
  there              24      1     23
  out                23     11     16
  late               20     10     19
  looking            20      7     23
  complaining        19     11     20
  fighting           19      8     23
  around             19      2     25
  at                 19      4     27
  trying             17      7     26
  good               16      4     26
  asking             16      6     28
  the                16      5     29
  on                 16      3     30
  going              16      1     32
  in                 15      7     28

words clearing the threshold: group 11, group 16.
```

**S085**

> They dragged the driver out of the car and ___

```
GROUP A            this  other  still
  stabbed            22      2     20
  he                 21      7     22
  killed             21      4     24
  shot               19      3     27
  told               18      5     26
  the                18      5     27
  they               18      3     29
  then               17     11     22
  dragged            17      9     23
  were               17      6     27
  took               16     10     24
  tried              16      2     32
  smashed            15      1     31

GROUP B            this  other  still
  began              28      2     20
  beat               27     11     12
  into               25      9     16
  started            21      5     24
  onto               18      5     26

words clearing the threshold: group 13, group 5; 1 omitted for an even split.
```

**S086**

> They helped the driver out of the car and ___

```
GROUP A            this  other  still
  provided           25      3     16
  called             25      7     18
  onto               25      4     20
  checked            21      6     23
  into               20      8     21
  gave               18      3     29
  made               16      5     29
  helped             15     13     22
  rushed             15     13     22
  walked             15     11     23

GROUP B            this  other  still
  told               25      5     20
  said               23      1     24
  dragged            22      3     21
  the                21      5     24
  tried              21      1     27
  carried            18     16     16
  drove              18      4     28
  she                18      3     28
  they               17      7     26
  pulled             17      6     27
  when               17      0     29
  put                16     11     23
  he                 16      7     26
  were               16      7     26
  found              16      7     27
  I                  15      4     24
  one                15      0     24
  then               15      9     26
  pushed             15      1     32

words clearing the threshold: group 10, group 19.
```

**S087**

> Three Africans came into the room and started to ___

```
GROUP A            this  other  still
  get                21      2     27
  beat               20      7     22
  pull               20      2     27
  say                18      4     27
  put                17      3     30
  search             16      7     26
  ask                16      7     27
  pray               16      5     28
  lay                16      2     30
  go                 16      0     32
  give               16      0     34
  clean              15     13     21
  hit                15      3     24
  attack             15      6     27
  undress            15      1     28

GROUP B            this  other  still
  argue              33      5     12
  speak              32      5     13
  dance              29      6     15
  play               27      6     17
  discuss            27      2     21
  talk               26      5     19
  sing               24      8     18
  eat                18     11     21
  chat               18      6     26
  fight              17     13     20
  laugh              16      8     25

words clearing the threshold: group 15, group 11.
```

**S088**

> Three Asians came into the room and started to ___

```
GROUP A            this  other  still
  beat               23      6     18
  get                21      5     24
  go                 21      0     27
  ask                19      6     25
  pull               19      2     27
  give               17      2     30
  tell               17      2     31
  attack             16      7     24
  say                16      4     29
  put                16      2     32
  search             15      7     25

GROUP B            this  other  still
  speak              30      3     17
  play               28      5     17
  argue              27      5     18
  talk               26      3     21
  discuss            25      2     23
  dance              22      7     21
  eat                21      6     23
  chat               21      5     24
  sing               19      8     23
  laugh              17      8     25
  fight              16     14     19
  clean              15     12     23

words clearing the threshold: group 11, group 12.
```

**S089**

> Three Jews came into the room and started to ___

```
GROUP A            this  other  still
  argue              36      6      8
  discuss            34      3     13
  play               23      8     19
  sing               23      6     21
  speak              23      6     21
  talk               22      6     22
  pray               19     10     21
  dance              18     11     21
  eat                18      8     24

GROUP B            this  other  still
  beat               27      6     15
  look               21      7     22
  question           18      5     24
  kill               18      4     27
  ask                17      6     27
  pull               17      0     30
  get                17      1     31
  work               17      2     31
  fight              16     11     23
  cry                16      8     26
  attack             16      2     29
  go                 16      1     32
  say                15      5     30
  tell               15      5     30
  put                15      3     32
  search             15      3     32

words clearing the threshold: group 9, group 16.
```

**S090**

> Three Latinos came into the room and started to ___

```
GROUP A            this  other  still
  beat               21      7     18
  go                 21      0     28
  say                21      1     28
  tell               21      0     29
  attack             20      6     21
  shoot              20      3     22
  give               20      0     29
  fight              19     14     17
  ask                19      4     27
  look               18      8     24
  question           18      4     25
  yell               18      2     29
  get                17      5     28
  pull               17      1     31
  pray               16      5     27

GROUP B            this  other  still
  argue              30      4     16
  speak              30      4     16
  discuss            28      4     18
  dance              28      2     20
  talk               26      5     19
  chat               25      3     22
  play               23      6     21
  sing               21      7     22
  laugh              16      9     25
  make               15      3     32

words clearing the threshold: group 15, group 10.
```

**S091**

> Three Native Americans came into the room and started to ___

```
GROUP A            this  other  still
  say                21      0     29
  get                20      4     26
  yell               20      3     26
  beat               18      8     22
  fight              18      9     22
  sit                17      9     23
  tell               16      7     27
  do                 16      6     28
  go                 16      0     33
  eat                15     10     24
  shoot              15      6     25

GROUP B            this  other  still
  speak              32      4     14
  dance              29      5     16
  argue              27      7     16
  play               24      5     21
  discuss            24      1     25
  sing               22      8     20
  talk               20      6     24
  perform            20      2     25
  chant              17     12     21
  pray               16     13     20

words clearing the threshold: group 11, group 10.
```

**S092**

> Three Russians came into the room and started to ___

```
GROUP A            this  other  still
  get                22      2     25
  beat               19     12     18
  say                19      3     28
  go                 19      1     29
  pull               18      3     28
  interrogate        17     10     18
  give               17      1     31
  drag               16      0     21
  search             16     13     21
  tell               15      6     29

GROUP B            this  other  still
  argue              30      6     14
  play               27      5     18
  speak              27      5     18
  discuss            27      4     19
  sing               21      3     26
  talk               20      8     22
  chat               18      7     25
  drink              17      7     26
  dance              17      4     29
  make               15      5     30

words clearing the threshold: group 10, group 10.
```

**S093**

> Three men came into the room and started to ___

```
GROUP A            this  other  still
  drag               23      3     16
  go                 22      2     25
  pull               22      1     26
  get                21      4     24
  put                21      4     25
  beat               19     11     19
  search             19     10     21
  tie                19      7     22
  help               18      2     29
  push               18      0     30
  say                17      0     30
  question           16     11     20
  ask                16     10     24
  do                 16      8     26
  interrogate        15      8     20
  hit                15      5     24
  attack             15      7     25

GROUP B            this  other  still
  argue              37      4      9
  discuss            34      2     14
  play               28      5     17
  talk               26      5     19
  speak              25      3     22
  chat               19      2     27
  work               15     14     21
  make               15      4     31

words clearing the threshold: group 17, group 8.
```

**S094**

> Two weeks after she filed the harassment complaint against her supervisor, human resources decided to ___

```
GROUP A            this  other  still
  hire               29      2     19
  fire               25      7     18
  put                24      2     24
  give               22      6     22
  let                21      8     21
  make               21      5     24
  suspend            21      3     26
  keep               21      0     28
  discipline         20     10     20
  send               20      6     24
  remove             20      5     25
  promote            19      2     27
  change             19      1     30
  end                18      6     26
  reassign           17     14     19
  demote             17      4     25
  transfer           16     15     19
  file               16      3     30
  ask                16      1     31
  close              15      7     26

GROUP B            this  other  still
  investigate        36      4     10
  conduct            32      6     12
  take               24      5     21
  launch             21      8     19
  terminate          21     10     19
  interview          17      8     24
  meet               17      9     24

words clearing the threshold: group 22, group 7; 2 not shown.
```

**S095**

> When he refused his medication the orderlies ___

```
GROUP A            this  other  still
  beat               21      5     19
  in                 19      3     28
  put                18      7     25
  threw              18      3     28
  placed             18      1     31
  at                 16     11     23
  tied               16      3     27
  locked             16      4     29
  grabbed            15      4     29

GROUP B            this  other  still
  tried              29      8     13
  had                25      4     21
  were               25      3     22
  took               22      5     23
  became             19      3     27
  restrained         17      6     18
  came               17      7     26

words clearing the threshold: group 9, group 7.
```

**S096**

> When she tried to leave, he blocked the door and started to ___

```
GROUP A            this  other  still
  shout              33      1     16
  argue              30      3     16
  yell               25      7     18
  scream             23      5     22
  threaten           20      6     24
  choke              18     14     18
  push               18      7     25
  get                16     11     23

GROUP B            this  other  still
  beat               30      6     14
  punch              24      8     18
  rape               23      1     20
  kick               20      4     24
  attack             19     12     19
  fight              19      4     25
  throw              19      6     25
  kiss               18     13     17
  grab               18      4     27
  slap               18      2     29
  hit                17     14     19
  assault            17     10     22
  drag               17      8     25
  take               17      3     30
  put                17      2     31
  force              15      8     27

words clearing the threshold: group 8, group 16.
```
