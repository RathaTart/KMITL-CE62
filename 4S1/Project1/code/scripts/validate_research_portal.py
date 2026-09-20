"""Static presentation checks; never imports an evaluator or runs a model."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

STATIC = Path(__file__).resolve().parents[1] / 'webapp/static'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for field in ('href', 'src'):
            if field in attrs:
                self.links.append(attrs[field])
        self.headings += tag == 'h2'

def main():
    data = json.loads((STATIC/'portal-data.json').read_text(encoding='utf-8'))
    docs = json.loads((STATIC/'documents/index.json').read_text(encoding='utf-8'))
    extra = int('extended' in data)
    assert len(docs) == 7 + extra
    assert [d['progress'] for d in docs] == [2, 2, 3, 3, 3, 3, 3] + [3] * extra
    count = 0
    paths = set()
    for group in ['attribute', 'upgrade', 'training', 'progress2'] + (['extended'] if extra else []):
        sets = data[group]
        if group == 'progress2':
            sets = list(sets.values())
        elif not isinstance(sets, list):
            sets = [sets]
        for dataset in sets:
            assert dataset['items'] and dataset['summary']
            for item in dataset['items']:
                assert item['expression'] and item['case_type']
                paths.update([item['image'], item['gt']])
                for pred in item['predictions'].values():
                    assert 0 <= pred['iou'] <= 1
                    paths.add(pred['src'])
                count += 1
    assert count == 513 + 180 * extra  # Saved request entries; includes reused development cases.
    for path in paths:
        target = (STATIC/path).resolve()
        assert target.is_relative_to(STATIC.resolve()), path
        assert target.is_file() and target.stat().st_size, path
    for doc in docs:
        for lang in ['en', 'th']:
            base = STATIC/'documents'/f'{doc["id"]}.{lang}'
            content = base.with_suffix(f'.{lang}.md').read_text(encoding='utf-8')
            assert content.startswith('# '), str(base)
            if lang == 'th':
                assert sum('\u0e00' <= c <= '\u0e7f' for c in content) > 1000
            page = base.with_suffix(f'.{lang}.html')
            parser = Links()
            parser.feed(page.read_text(encoding='utf-8'))
            assert parser.headings >= 4, page
            for link in parser.links:
                parsed = urlsplit(link)
                if not parsed.scheme and parsed.path:
                    assert (page.parent/unquote(parsed.path)).is_file(), (page, link)
    for filename in ['index.html', 'attribute-research.html', 'model-upgrade.html', 'training-free.html']:
        parser = Links()
        parser.feed((STATIC/filename).read_text(encoding='utf-8'))
        for link in parser.links:
            url = urlsplit(link)
            if not url.scheme and url.path:
                assert (STATIC/unquote(url.path)).is_file(), (filename, link)
    assert round(data['training']['summary']['LISA_proposal_agreement']['positive']['mean_iou']*100, 2) == 77.09
    assert round(data['training']['summary']['LISA']['positive']['mean_iou']*100, 2) == 76.47
    print(f'PASS: {len(docs)} bilingual document pairs, {count} saved request entries, {len(paths)} existing image/mask paths, local document links and headline provenance.')

if __name__ == '__main__':
    main()
