import json, urllib.request

BASE = 'http://127.0.0.1:8001'

def req(path, payload=None, key=None):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {'Content-Type': 'application/json'}
    if key:
        h['Authorization'] = 'Bearer ' + key
    r = urllib.request.Request(BASE + path, data=data, headers=h)
    return json.loads(urllib.request.urlopen(r, timeout=60).read())

ANSWERS = {
 'business_name': 'Northstar General Store',
 'vertical': 'Groceries or food',
 'locations': 'One place',
 'selling': 'Customers pick items, we ring them up at the counter, they pay by card or cash.',
 'buying': 'I reorder when stock runs low. I approve each purchase myself and check every delivery against the supplier bill.',
 'stock_pain': 'Running out',
 'credit_behavior': 'Only suppliers give us credit',
 'discounts': 'Only the owner gives discounts. Refunds always need the owner.',
 'returns': 'Within seven days with a receipt we refund or exchange. Unused items go back on the shelf.',
 'staff': 'Two cashiers can ring up sales but cannot change prices. The owner manages everything else.',
 'money_view': ['Sales', 'Low stock', 'Money I owe suppliers'],
 'country': 'Registered in the United States. We sell locally in one city.',
 'selling_locations': ['Near my registered business'],
 'buying_locations': ['Nearby suppliers'],
 'price_display': 'Tax is added at checkout',
 'customer_type': 'Households',
 'product_tax_facts': 'No special tax treatment that our accountant flags.',
 'existing_records': 'Spreadsheets',
 'exceptions': 'Partial deliveries from suppliers cause the most confusion.',
 'brand_style': 'Clean and professional',
 'brand_colors': 'Deep green and warm white',
 'logo': 'No, use the business name for now',
 'screen_preference': 'Today’s manager checklist',
 'goal': 'Know what to reorder each morning without digging through spreadsheets.',
}

w = req('/api/workspaces', {'name': 'Northstar General Store'})
wid, key = w['workspace_id'], w['api_key']
s = req('/api/onboarding/start', {}, key)
sid = s['id']
for k, v in ANSWERS.items():
    req('/api/onboarding/answer', {'id': sid, 'key': k, 'value': v}, key)
req('/api/onboarding/apply', {'id': sid}, key)
json.dump({'wid': wid, 'key': key, 'name': 'Northstar General Store'}, open('/tmp/demo_creds.json', 'w'))
print('seeded workspace', wid)
