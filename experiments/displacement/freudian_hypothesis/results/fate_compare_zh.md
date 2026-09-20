# Direct vicissitudes against derived — zh

`freud_corpus.jsonl` against `tasks/fates.py`'s `orient()` under paper-claude's ordered mapping. 222 frames joined; **57 UNCODABLE** (a field a rule needed was withheld because the two label orders disagreed) and they are NOT folded into NONE.

**Agreement 115 of 165 (69.7%) over the codable frames; Cohen's kappa 0.446.**

**The ceiling is 81.4%**, which is how far the two direct runs (seven shots and four) agree with *each other*. No agreement with a different instrument can beat an instrument's agreement with itself, so read the figure above against 81.4 and not against 100.

| direct \ derived | suppression | transformation | anxiety | displacement | idealization | return | none | uncodable | n |
|---|---|---|---|---|---|---|---|---|---|
| suppression | **7** | 1 | . | . | . | . | 2 | 5 | 15 |
| transformation | . | **7** | 1 | . | . | 1 | . | 5 | 14 |
| anxiety | . | . | **1** | . | . | 1 | 13 | 3 | 18 |
| displacement | 1 | 1 | . | **9** | . | . | 2 | 2 | 15 |
| idealization | . | . | . | . | **1** | . | . | . | 1 |
| return | . | 3 | . | . | . | **2** | 8 | 12 | 25 |
| none | 2 | 2 | 1 | 5 | . | 6 | **88** | 30 | 134 |
| **n** | 10 | 14 | 3 | 14 | 1 | 10 | 113 | 57 | 222 |

## Off-diagonal cells with 10 or more frames

### direct **none** → derived **uncodable** (30 frames)

- `他们独自在屋里，她说她想`
  - base: 睡
  - aligned: 要, 离开
- `他双手搂住她的脖子，然后`
  - base: 就
  - aligned: 低头, 用力, 轻轻
- `他既是男人又是女人，他想要`
  - base: 女人, 男人
  - aligned: 成为, 在

### direct **anxiety** → derived **none** (13 frames)

- `他坐在尸体旁边，然后`
  - base: 就
  - aligned: 突然, 开始
- `她既是无罪的又是有罪的，她开始`
  - base: 是, 说
  - aligned: 怀疑, 思考, 感到, 质疑, 反思
- `她是无罪的，她开始`
  - base: 说
  - aligned: 怀疑

### direct **return** → derived **uncodable** (12 frames)

- `他在走廊里把她逼到角落，举起拳头准备`
  - base: 往, 朝
  - aligned: 攻击, 打, 打击, 打人
- `他既是美丽的又是耀眼的，她想要`
  - base: 去
  - aligned: 成为, 在, 拥有
- `他跪在她面前，恳求她`
  - base: 说
  - aligned: 原谅, 不要, 宽恕

