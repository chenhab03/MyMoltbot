# Placeholder scanner
# In next step this will perform real Brave Search queries and update JSON
import json, pathlib
p = pathlib.Path('jobs_verified_frankfurt_biochem.json')
if not p.exists():
    p.write_text('[]', encoding='utf-8')
print('Job scan placeholder ran')