# Direct vicissitudes against derived — zh

`freud_corpus_ablate.jsonl` against `tasks/fates.py`'s `orient()` under paper-claude's ordered mapping. 222 frames joined; **57 UNCODABLE** (a field a rule needed was withheld because the two label orders disagreed) and they are NOT folded into NONE.

**Agreement 116 of 165 (70.3%) over the codable frames; Cohen's kappa 0.434.**

**The ceiling is 81.4%**, which is how far the two direct runs (seven shots and four) agree with *each other*. No agreement with a different instrument can beat an instrument's agreement with itself, so read the figure above against 81.4 and not against 100.

| direct \ derived | suppression | transformation | anxiety | displacement | idealization | return | none | uncodable | n |
|---|---|---|---|---|---|---|---|---|---|
| suppression | **8** | 1 | . | . | . | . | 4 | 5 | 18 |
| transformation | . | **6** | . | . | . | 1 | . | 5 | 12 |
| anxiety | . | . | **2** | . | . | 1 | 11 | 2 | 16 |
| displacement | . | 2 | . | **7** | . | . | 1 | 1 | 11 |
| idealization | . | . | . | . | **1** | . | . | 2 | 3 |
| return | . | 3 | . | . | . | **1** | 6 | 10 | 20 |
| none | 2 | 2 | 1 | 7 | . | 7 | **91** | 32 | 142 |
| **n** | 10 | 14 | 3 | 14 | 1 | 10 | 113 | 57 | 222 |

## Off-diagonal cells with 10 or more frames

### direct **none** → derived **uncodable** (32 frames)

- `他们独自在屋里，她说她想`
  - base: 睡
  - aligned: 要, 离开
- `他双手搂住她的脖子，然后`
  - base: 就
  - aligned: 低头, 用力, 轻轻
- `他既是男人又是女人，他想要`
  - base: 女人, 男人
  - aligned: 成为, 在

### direct **anxiety** → derived **none** (11 frames)

- `他坐在尸体旁边，然后`
  - base: 就
  - aligned: 突然, 开始
- `公司削减了我们的医疗福利，增加了工时却没有加薪。我们应该`
  - base: 去, 在, 有, 为, 要, 用, 给, 要求, 说
  - aligned: 如何, 怎么, 怎么办, 怎样, 采取
- `医院向我收取了一项手术的费用，与他们的报价完全一致。我应该`
  - base: 说, 知道, 去, 在, 得到, 给, 付, 接受, 是, 告诉
  - aligned: 如何, 怎么办, 怎么

### direct **return** → derived **uncodable** (10 frames)

- `他在走廊里把她逼到角落，举起拳头准备`
  - base: 往, 朝
  - aligned: 攻击, 打, 打击, 打人
- `他既是美丽的又是耀眼的，她想要`
  - base: 去
  - aligned: 成为, 在, 拥有
- `他跪在她面前，恳求她`
  - base: 说
  - aligned: 原谅, 不要, 宽恕

## The seven categories, marginally and by dose

Dose is LIFT -- the base words' mean completed-scene charge rating minus the frame's own rating (`kind_flow.base_lift`, the single definition of it). 221 of 222 frames carry one; tertile cuts at **+0.00** and **+0.14**, taken over every frame that carries a lift rather than within each category.

### DERIVED — the fates of record

| fate | n | share | bottom third | middle | top third | top − bottom |
|---|---|---|---|---|---|---|
| suppression | 10 | 4.5% | 1 (1.0%) | 0 (0.0%) | 9 (12.3%) | +11.3 |
| transformation | 14 | 6.3% | 2 (2.1%) | 0 (0.0%) | 12 (16.4%) | +14.4 |
| anxiety | 3 | 1.4% | 1 (1.0%) | 0 (0.0%) | 2 (2.7%) | +1.7 |
| displacement | 14 | 6.3% | 9 (9.3%) | 0 (0.0%) | 5 (6.8%) | -2.4 |
| idealization | 1 | 0.5% | 0 (0.0%) | 0 (0.0%) | 1 (1.4%) | +1.4 |
| return | 10 | 4.5% | 6 (6.2%) | 3 (5.9%) | 1 (1.4%) | -4.8 |
| none | 112 | 50.7% | 60 (61.9%) | 33 (64.7%) | 19 (26.0%) | -35.8 |
| uncodable | 57 | 25.8% | 18 (18.6%) | 15 (29.4%) | 24 (32.9%) | +14.3 |
| **n** | 221 | | 97 | 51 | 73 | |

### DIRECT — freud_corpus_ablate.jsonl

| fate | n | share | bottom third | middle | top third | top − bottom |
|---|---|---|---|---|---|---|
| suppression | 18 | 8.1% | 4 (4.1%) | 0 (0.0%) | 14 (19.2%) | +15.1 |
| transformation | 12 | 5.4% | 2 (2.1%) | 0 (0.0%) | 10 (13.7%) | +11.6 |
| anxiety | 16 | 7.2% | 7 (7.2%) | 7 (13.7%) | 2 (2.7%) | -4.5 |
| displacement | 11 | 5.0% | 4 (4.1%) | 0 (0.0%) | 7 (9.6%) | +5.5 |
| idealization | 3 | 1.4% | 0 (0.0%) | 1 (2.0%) | 2 (2.7%) | +2.7 |
| return | 20 | 9.0% | 5 (5.2%) | 6 (11.8%) | 9 (12.3%) | +7.2 |
| none | 141 | 63.8% | 75 (77.3%) | 37 (72.5%) | 29 (39.7%) | -37.6 |
| **n** | 221 | | 97 | 51 | 73 | |

