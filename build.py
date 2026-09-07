#!/usr/bin/env python3
"""Inject shrimp_data.json into template.html -> index.html."""
import json
data = json.load(open('shrimp_data.json'))
tpl = open('template.html').read()
assert '__SHRIMP_DATA__' in tpl
open('index.html', 'w').write(tpl.replace('__SHRIMP_DATA__', json.dumps(data)))
print('index.html written')
