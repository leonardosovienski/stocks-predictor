import sys
from source_utils import pages

for item in sys.argv[1:]:
    name, *wanted = item.split(':')
    wanted = set(map(int, wanted))
    for p in pages(name):
        if not wanted or p['page'] in wanted:
            print('\nDOCUMENT', name, 'PAGE', p['page'])
            print(p['text'])
