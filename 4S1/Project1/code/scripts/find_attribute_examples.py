"""Read-only search for blue-headwear/black-clothing descriptions in gRefCOCO."""
import json
from pathlib import Path

path = Path('/home/osta/lisa-eval/dataset/grefcoco/grefs(unc).json')
matches = []
for ref in json.loads(path.read_text()):
    for sentence in ref['sentences']:
        text = sentence['sent'].lower()
        if 'blue' in text and 'black' in text and ('hat' in text or 'cap' in text):
            matches.append(dict(ref_id=ref['ref_id'], split=ref['split'], image=ref['file_name'], no_target=ref['no_target'], description=sentence['sent']))
print(json.dumps(matches, indent=2))
