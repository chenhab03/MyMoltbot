import os, json, time, requests
from urllib.parse import urlencode

API_KEY = os.getenv('BRAVE_API_KEY')
assert API_KEY, 'BRAVE_API_KEY missing'

CENTER = 'Frankfurt am Main'
KEYWORDS = [
    'Biochemistry Scientist Frankfurt',
    'Postdoc Biochemistry Frankfurt',
    'Research Scientist Biochemistry Frankfurt',
    'Life Science Scientist Frankfurt'
]
ALLOWED_SITES = [
    'stepstone.de',
    'indeed.com', 'indeed.de',
    'glassdoor.com',
    'linkedin.com/jobs',
    'careers.', 'career.', 'jobs.'
]

HEADERS = {
    'Accept': 'application/json',
    'X-Subscription-Token': API_KEY
}

OUT = 'jobs_verified_frankfurt_biochem.json'

# ---- Brave search ----
def brave_search(q, count=12):
    params = {'q': q, 'source': 'web', 'count': count}
    url = 'https://api.search.brave.com/res/v1/web/search?' + urlencode(params)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get('web', {}).get('results', [])


def is_relevant(url):
    return any(s in url for s in ALLOWED_SITES)


# ---- still-open heuristic (no extra deps) ----
def still_open(url):
    try:
        r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code >= 400:
            return False
        html = r.text.lower()
        closed_signals = [
            'position has been filled', 'no longer available', 'job expired',
            'stellenangebot ist nicht mehr', 'job is closed', 'nicht mehr verfügbar'
        ]
        return not any(s in html for s in closed_signals)
    except Exception:
        return False


results = []
seen = set()

for kw in KEYWORDS:
    for it in brave_search(kw, count=12):
        url = it.get('url')
        title = it.get('title')
        if not url or not title:
            continue
        if not is_relevant(url):
            continue
        key = (title, url)
        if key in seen:
            continue
        # verify still open
        if not still_open(url):
            continue
        seen.add(key)
        results.append({
            'company': it.get('siteName', '—'),
            'role': title,
            'location': CENTER,
            'source': 'Brave Search (verified open)',
            'url': url
        })
        time.sleep(0.6)

# merge with existing
if os.path.exists(OUT):
    try:
        existing = json.load(open(OUT, 'r', encoding='utf-8'))
    except Exception:
        existing = []
else:
    existing = []

merged = {(e['role'], e['url']): e for e in existing}
for r in results:
    merged[(r['role'], r['url'])] = r

final = list(merged.values())
json.dump(final, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'Updated {len(final)} verified job entries')
