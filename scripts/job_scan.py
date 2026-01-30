import os, json, time, re, requests
from urllib.parse import urlencode

API_KEY = os.getenv('BRAVE_API_KEY')
assert API_KEY, 'BRAVE_API_KEY missing'

# --- Search configuration ---
CENTER = 'Frankfurt am Main'
RADIUS_KM = 50
KEYWORDS = [
    'Biochemistry Scientist Frankfurt',
    'Postdoc Biochemistry Frankfurt',
    'Research Scientist Biochemistry Frankfurt'
]
ALLOWED_SITES = ['stepstone.de', 'jobs.', 'career', 'careers']

HEADERS = {
    'Accept': 'application/json',
    'X-Subscription-Token': API_KEY
}

OUT = 'jobs_verified_frankfurt_biochem.json'

# --- Helpers ---
def brave_search(q, count=10):
    params = {
        'q': q,
        'source': 'web',
        'count': count
    }
    url = 'https://api.search.brave.com/res/v1/web/search?' + urlencode(params)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get('web', {}).get('results', [])


def is_relevant(url):
    return any(s in url for s in ALLOWED_SITES)


# --- Main scan ---
results = []
seen = set()

for kw in KEYWORDS:
    items = brave_search(kw, count=10)
    for it in items:
        url = it.get('url')
        title = it.get('title')
        desc = it.get('description', '')
        if not url or not title:
            continue
        if not is_relevant(url):
            continue
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        results.append({
            'company': it.get('siteName', '—'),
            'role': title,
            'location': CENTER,
            'source': 'Brave Search (indexed)',
            'url': url
        })
        time.sleep(0.5)

# Load existing and merge
if os.path.exists(OUT):
    with open(OUT, 'r', encoding='utf-8') as f:
        try:
            existing = json.load(f)
        except json.JSONDecodeError:
            existing = []
else:
    existing = []

merged = { (e['role'], e['url']): e for e in existing }
for r in results:
    merged[(r['role'], r['url'])] = r

final = list(merged.values())

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f'Updated {len(final)} verified job entries')
