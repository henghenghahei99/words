#!/usr/bin/env python3
"""为边界词补全「变形」字段标签。

模型对专有形容词（german/italian）、物质名词（cotton/metal）、
情态动词（might/would）、屈折形词头（bent/born）等不会主动给
比较级/复数/时态标签，这里用确定性规则补齐，避免反复重生成。
"""
import re

PATH = '../data/entries.jsonl'

# 动词：补时态
VFIX = {
    'bent':  '动词 → 原形：bend；过去式：bent；过去分词：bent；现在分词：bending',
    'born':  '动词 → 原形：bear；过去分词：born；过去式：bore（主要用于 be born）',
    'might': '情态动词 → 无第三人称单数、过去分词、现在分词变化；过去式：might（表推测或虚拟）',
    'would': '情态动词 → 原形：will；过去式：would；无过去分词、现在分词变化',
}

# 名词：补复数
NFIX = {
    'bacteria': '名词 → 复数：bacteria（单数：bacterium）',
    'bid':      '名词 → 复数：bids',
    'bent':     '名词 → 复数：bents',
    'best':     '名词 → 不可数（抽象名词，一般无复数）；复数：bests（书面语，指最佳者）',
    'cease':    '名词 → 不可数（without cease 不停）',
    'move':     '名词 → 复数：moves',
    'neglect':  '名词 → 不可数',
    'nurture':  '名词 → 不可数',
    'offer':    '名词 → 复数：offers',
    'preserve': '名词 → 复数：preserves',
}

# 形容词：可分级（有比较级）的，用 more/most
A_GRAD = {'adolescent', 'beloved', 'magnificent', 'magnetic',
          'mobile', 'moral', 'mortal', 'imperative', 'invalid'}

# 形容词：关系/专有/物质形容词，不用于比较
A_NO = {
    'adjective', 'agricultural', 'arch', 'assistant', 'cardinal',
    'chocolate', 'cocktail', 'composite', 'constituent', 'continent',
    'cotton', 'dairy', 'designate', 'downtown', 'fahrenheit', 'fellow',
    'female', 'folk', 'former', 'german', 'heating', 'household',
    'infant', 'immigrant', 'italian', 'ivory', 'liquid', 'made', 'magic',
    'marxist', 'material', 'mediterranean', 'metal', 'metallic',
    'metropolitan', 'migrant', 'military', 'mineral', 'miniature',
    'minimum', 'missionary', 'mock', 'monster', 'motor', 'neighbor',
    'one', 'semi-final', 'spanish', 'specialty', 'subordinate',
    'surrounding', 'total', 'vegetable', 'what', 'whatever', 'which',
}


def patch(w, form):
    add = []
    if w in VFIX:
        add.append(VFIX[w])
    if w in NFIX:
        add.append(NFIX[w])
    if w in A_GRAD:
        add.append('形容词 → 比较级：more %s；最高级：most %s' % (w, w))
    if w in A_NO:
        add.append('形容词 → 无比较级（关系/专有形容词，不作比较）')
    return add


def main():
    targets = set(VFIX) | set(NFIX) | A_GRAD | A_NO
    out, patched = [], 0
    for line in open(PATH, encoding='utf-8'):
        line = line.rstrip('\n')
        if '\t' not in line:
            continue
        w, b = line.split('\t', 1)
        b = b.replace('\\n', '\n')
        lines = b.split('\n')
        for i, l in enumerate(lines):
            if l.startswith('- **变形**'):
                add = [a for a in patch(w, l) if a.split(' → ')[-1] not in l]
                if add:
                    lines[i] = l + '；' + '；'.join(add)
                    patched += 1
                break
        else:
            add = patch(w, '')
            if add:
                lines.append('- **变形**：' + '；'.join(add))
                patched += 1
        out.append(w + '\t' + '\n'.join(lines).replace('\n', '\\n'))
    open(PATH, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('patched', patched, 'targets', len(targets))


if __name__ == '__main__':
    main()
