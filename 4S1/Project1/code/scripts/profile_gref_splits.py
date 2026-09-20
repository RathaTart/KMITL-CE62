import json
from collections import Counter
from pathlib import Path
r=json.loads(Path('/home/osta/lisa-eval/dataset/grefcoco/grefs(unc).json').read_text())
c=Counter()
for i in r:
    cats=i['category_id'] if isinstance(i['category_id'],list) else [i['category_id']]
    if i['ann_id']==[-1]:kind='negative'
    elif set(cats)=={1}:kind='person_multi' if len(i['ann_id'])>1 else 'person_single'
    else:kind='other'
    c[i['split'],kind]+=1
print(dict(c))
