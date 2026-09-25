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

loc = req('/api/retail/locations', {'code':'MAIN','name':'Main store','kind':'store'}, key)
PRODS = [('RICE-5KG','Basmati Rice 5kg',1299,650),('FLOUR-2KG','Whole Wheat Flour 2kg',549,280),
 ('OIL-1L','Olive Oil 1L',1199,720),('HONEY-500','Organic Honey 500g',899,540),('OATS-1KG','Rolled Oats 1kg',449,210),
 ('TEA-250','Black Tea 250g',649,320),('ALMOND-500','Almonds 500g',1099,690),('TOWEL-6PK','Paper Towels 6pk',799,430)]
prods={}
for sku,name,sell,cost in PRODS:
    p=req('/api/retail/products', {'sku':sku,'name':name,'selling_price_minor':sell,'cost_minor':cost}, key); prods[sku]=p['id']
v1=req('/api/accounting/parties', {'kind':'vendor','name':'Fresh Farms Wholesale'}, key)
v2=req('/api/accounting/parties', {'kind':'vendor','name':'Golden Grains Co.'}, key)
def po(vendor, lines, approve=True, receive=True):
    r=req('/api/retail/purchases', {'vendor_id':vendor,'location_id':loc['id'],'ordered_on':'2026-09-24','lines':lines,'currency':'USD'}, key)
    if approve:
        req('/api/retail/purchases/approve', {'purchase_order_id':r['id']}, key)
    if receive:
        exp=req('/api/retail/export', None, key)
        recv={l['id']:l['quantity'] for l in exp['purchase_order_lines'] if l['purchase_order_id']==r['id']}
        req('/api/retail/purchases/receive', {'purchase_order_id':r['id'],'received':recv}, key)
    return r
po1=po(v1['id'], [{'product_id':prods['RICE-5KG'],'quantity':'40','unit_cost_minor':650},{'product_id':prods['FLOUR-2KG'],'quantity':'60','unit_cost_minor':280},{'product_id':prods['OIL-1L'],'quantity':'30','unit_cost_minor':720},{'product_id':prods['HONEY-500'],'quantity':'25','unit_cost_minor':540}])
po2=po(v2['id'], [{'product_id':prods['OATS-1KG'],'quantity':'45','unit_cost_minor':210},{'product_id':prods['TEA-250'],'quantity':'30','unit_cost_minor':320},{'product_id':prods['ALMOND-500'],'quantity':'20','unit_cost_minor':690},{'product_id':prods['TOWEL-6PK'],'quantity':'50','unit_cost_minor':430}])
bill=req('/api/accounting/documents', {'kind':'purchase_bill','issue_date':'2026-09-24','party_id':v1['id'],'lines':[{'description':'Basmati Rice 5kg','quantity':'40','unit_price_minor':650},{'description':'Whole Wheat Flour 2kg','quantity':'60','unit_price_minor':280},{'description':'Olive Oil 1L','quantity':'30','unit_price_minor':720},{'description':'Organic Honey 500g','quantity':'25','unit_price_minor':540}]}, key)
req('/api/accounting/documents/approve', {'document_id':bill['id']}, key)
req('/api/accounting/documents/post', {'document_id':bill['id']}, key)
req('/api/retail/three-way-match', {'purchase_order_id':po1['id'],'bill_id':bill['id']}, key)
po(v2['id'], [{'product_id':prods['OATS-1KG'],'quantity':'25','unit_cost_minor':210},{'product_id':prods['TOWEL-6PK'],'quantity':'30','unit_cost_minor':430}], approve=True, receive=False)
po(v1['id'], [{'product_id':prods['RICE-5KG'],'quantity':'20','unit_cost_minor':650},{'product_id':prods['TEA-250'],'quantity':'15','unit_cost_minor':320}], approve=False, receive=False)
req('/api/retail/cash/open', {'location_id':loc['id'],'opening_minor':10000}, key)
def sale(sku, qty, amount):
    req('/api/retail/sales', {'location_id':loc['id'],'lines':[{'product_id':prods[sku],'quantity':str(qty)}],'tenders':[{'kind':'cash','amount_minor':amount}],'currency':'USD'}, key)
sale('RICE-5KG',2,2598); sale('OIL-1L',1,1199); sale('TEA-250',3,1947); sale('HONEY-500',1,899)
# Pending Build review draft: a supplier-bill report drafted from a photo
# extraction and left at the review step so visitors see a real draft state.
req('/api/build/draft-from-extraction', {
 'target': 'report',
 'extraction': {
   'document_type': 'supplier bill',
   'summary': 'Supplier bill from Golden Grains Co. for oats, tea and almonds',
   'fields': [{'name': 'vendor', 'value': 'Golden Grains Co.'}]
 },
 'hint': 'payables aging report for this supplier'
}, key)
json.dump({'wid': wid, 'key': key, 'name': 'Northstar General Store'}, open('/tmp/demo_creds.json', 'w'))
print('seeded workspace', wid)
