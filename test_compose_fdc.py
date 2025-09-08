import requests, json
BASE='http://localhost:8000'

# Login (assumes demo user exists)
r = requests.post(
    f'{BASE}/api/v1/auth/login',
    data={'username':'demo@example.com','password':'Passw0rd!'},
    headers={'Content-Type':'application/x-www-form-urlencoded'}
)
open('/tmp/compose_login.json','w').write(r.text)
access = r.json()['data']['access_token']

# Search foods
r = requests.get(
    f'{BASE}/api/v1/nutrition/foods/search',
    params={'q':'apple','page':1,'page_size':5},
    headers={'Authorization': f'Bearer {access}'}
)
open('/tmp/compose_search.json','w').write(r.text)
hits = r.json()['data']
assert isinstance(hits, list) and len(hits) > 0, 'No search hits returned'
first = hits[0]

# Fetch details from local cache by id
r = requests.get(
    f"{BASE}/api/v1/nutrition/foods/{first['id']}",
    headers={'Authorization': f'Bearer {access}'}
)
open('/tmp/compose_details.json','w').write(r.text)
