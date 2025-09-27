import json
import re
import pandas as pd
from fuzzywuzzy import fuzz

# The helper functions (clean_name, normalize_weight_and_price) are unchanged.
def clean_name(name):
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'[\(\)±]', ' ', name)
    noise_words = [
        'kg', 'gm', 'pcs', 'each', 'unit', 'bundle', 'local', 'imported',
        'china', 'india', 'premium', 'regular', 'combo', 'fali', 'slice'
    ]
    words = name.split()
    cleaned_words = [word for word in words if word not in noise_words and not word.isnumeric()]
    return " ".join(cleaned_words)

def normalize_weight_and_price(product):
    name_str = product.get('name', '').lower()
    quantity_str = str(product.get('quantity', '')).lower()
    price = product.get('price')
    if 'combo' in name_str or '&' in name_str:
        return pd.Series([None, None, None, None, None])
    weight_in_kg, price_numeric, price_per_kg = None, None, None
    price_per_500gm, price_per_100gm = None, None
    if price:
        try: price_numeric = float(re.sub(r'[^\d.]', '', str(price)))
        except (ValueError, TypeError): pass
    pattern = r'(\d+\.?\d*)\s*(kg|gm|g)\b'
    match = re.search(pattern, quantity_str)
    if not match:
        match = re.search(pattern, name_str)
    if match and price_numeric is not None:
        value, unit = float(match.group(1)), match.group(2)
        if unit == 'kg': weight_in_kg = value
        elif unit in ['gm', 'g']: weight_in_kg = value / 1000
        if weight_in_kg and weight_in_kg > 0:
            price_per_kg = round(price_numeric / weight_in_kg, 2)
            price_per_500gm = round(price_per_kg * 0.5, 2)
            price_per_100gm = round(price_per_kg * 0.1, 2)
    return pd.Series([price_numeric, weight_in_kg, price_per_kg, price_per_500gm, price_per_100gm])

# --- Main Script Logic ---
try:
    with open('chaldal_products.json', 'r', encoding='utf-8') as f: chaldal_data = json.load(f)
    with open('shwapno_products.json', 'r', encoding='utf-8') as f: shwapno_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: Make sure '{e.filename}' is in the same directory.")
    exit()

chaldal_data = [p for p in chaldal_data if p.get("name") and "loading" not in p["name"].lower()]
chaldal_df, shwapno_df = pd.DataFrame(chaldal_data), pd.DataFrame(shwapno_data)
chaldal_df['cleaned_name'] = chaldal_df['name'].apply(clean_name)
shwapno_df['cleaned_name'] = shwapno_df['name'].apply(clean_name)
new_cols = ['price_numeric', 'weight_kg', 'price_per_kg', 'price_per_500gm', 'price_per_100gm']
chaldal_df[new_cols] = chaldal_df.apply(normalize_weight_and_price, axis=1)
shwapno_df[new_cols] = shwapno_df.apply(normalize_weight_and_price, axis=1)

matched_products = []
shwapno_products_list = shwapno_df.to_dict('records')

for index, chaldal_product in chaldal_df.iterrows():
    best_match, best_score = None, 75
    for shwapno_product in shwapno_products_list:
        score = fuzz.token_sort_ratio(chaldal_product['cleaned_name'], shwapno_product['cleaned_name'])
        if score > best_score:
            best_score, best_match = score, shwapno_product
    
    if best_match:
        matched_products.append({
            'chaldal_name': chaldal_product['name'], 'chaldal_quantity': chaldal_product['quantity'], 'chaldal_url': chaldal_product['url'],
            'chaldal_price': chaldal_product['price_numeric'], 'chaldal_weight_kg': chaldal_product['weight_kg'],
            'chaldal_price_per_kg': chaldal_product['price_per_kg'],
            'shwapno_name': best_match['name'], 'shwapno_quantity': best_match['quantity'], 'shwapno_url': best_match['url'],
            'shwapno_price': best_match['price_numeric'], 'shwapno_weight_kg': best_match['weight_kg'],
            'shwapno_price_per_kg': best_match['price_per_kg'],
            'match_score': best_score
        })

# --- DEBUG PRINT ADDED ---
print(f"DEBUG: Found {len(matched_products)} total matches before filtering.")

# Filter out items that could not be compared by weight
comparable_products = [
    item for item in matched_products 
    if item['chaldal_price_per_kg'] is not None 
    and item['shwapno_price_per_kg'] is not None
]

# --- DEBUG PRINT ADDED ---
print(f"DEBUG: Found {len(comparable_products)} comparable matches after filtering.")


# Save the final, clean results
output_filename = 'comparison_results.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(comparable_products, f, indent=4, ensure_ascii=False)

print(f"✅ Success! Found {len(comparable_products)} fully comparable matches.")
print(f"Clean results have been saved to '{output_filename}'")