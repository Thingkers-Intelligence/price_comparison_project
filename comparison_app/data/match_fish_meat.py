import json
import re
import pandas as pd
from fuzzywuzzy import fuzz

# --- Helper Functions ---
def clean_name(name):
    """Cleans product names by removing noise words and punctuation."""
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r'[\(\)±]', ' ', name)
    noise_words = [
        'kg', 'gm', 'g', 'pcs', 'piece', 'each', 'unit', 'bundle', 
        'local', 'imported', 'frozen', 'fresh', 'boneless', 
        'regular', 'premium', 'cut', 'slice', 'pack'
    ]
    words = name.split()
    cleaned_words = [word for word in words if word not in noise_words and not word.isnumeric()]
    return " ".join(cleaned_words)

def normalize_weight_and_price(product):
    """
    Extracts numeric price and weight info, calculates price per kg if weight is available.
    Handles kg, gm, and pcs/pack units.
    """
    name_str = str(product.get('name', '')).lower()
    quantity_str = str(product.get('quantity', '')).lower()
    price = product.get('price')
    
    weight_in_kg, price_numeric, price_per_kg = None, None, None
    price_per_500gm, price_per_100gm = None, None

    if price:
        try:
            price_numeric = float(re.sub(r'[^\d.]', '', str(price)))
        except (ValueError, TypeError):
            pass

    pattern = r'(\d+\.?\d*)\s*(kg|gm|g|pcs|piece|pack)\b'
    match = re.search(pattern, quantity_str) or re.search(pattern, name_str)
    
    if match and price_numeric is not None:
        value, unit = float(match.group(1)), match.group(2)
        if unit == 'kg':
            weight_in_kg = value
        elif unit in ['gm', 'g']:
            weight_in_kg = value / 1000
        elif unit in ['pcs', 'piece', 'pack']:
            weight_in_kg = None  # cannot calculate per kg for per piece

        if weight_in_kg and weight_in_kg > 0:
            price_per_kg = round(price_numeric / weight_in_kg, 2)
            price_per_500gm = round(price_per_kg * 0.5, 2)
            price_per_100gm = round(price_per_kg * 0.1, 2)
    
    return pd.Series([price_numeric, weight_in_kg, price_per_kg, price_per_500gm, price_per_100gm])

# --- Main Script ---
try:
    with open('chaldal_fish_meat.json', 'r', encoding='utf-8') as f:
        chaldal_data = json.load(f)
    with open('shwapno_fish_meat.json', 'r', encoding='utf-8') as f:
        shwapno_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: Make sure '{e.filename}' is in the same directory.")
    exit()

# Filter out invalid entries
chaldal_data = [p for p in chaldal_data if p.get("name")]

# Convert to DataFrame
chaldal_df = pd.DataFrame(chaldal_data)
shwapno_df = pd.DataFrame(shwapno_data)

# Clean names
chaldal_df['cleaned_name'] = chaldal_df['name'].apply(clean_name)
shwapno_df['cleaned_name'] = shwapno_df['name'].apply(clean_name)

# Normalize weights and prices
new_cols = ['price_numeric', 'weight_kg', 'price_per_kg', 'price_per_500gm', 'price_per_100gm']
chaldal_df[new_cols] = chaldal_df.apply(normalize_weight_and_price, axis=1)
shwapno_df[new_cols] = shwapno_df.apply(normalize_weight_and_price, axis=1)

# --- Matching Logic ---
matched_products = []
shwapno_products_list = shwapno_df.to_dict('records')

for _, chaldal_product in chaldal_df.iterrows():
    best_match, best_score = None, 70  # lower threshold for fish/meat names
    for shwapno_product in shwapno_products_list:
        score = fuzz.token_sort_ratio(chaldal_product['cleaned_name'], shwapno_product['cleaned_name'])
        if score > best_score:
            best_score, best_match = score, shwapno_product
    
    if best_match:
        matched_products.append({
            'chaldal_name': chaldal_product['name'],
            'chaldal_quantity': chaldal_product['quantity'],
            'chaldal_url': chaldal_product.get('url'),
            'chaldal_price': chaldal_product['price_numeric'],
            'chaldal_weight_kg': chaldal_product['weight_kg'],
            'chaldal_price_per_kg': chaldal_product['price_per_kg'],
            'shwapno_name': best_match['name'],
            'shwapno_quantity': best_match['quantity'],
            'shwapno_url': best_match.get('url'),
            'shwapno_price': best_match['price_numeric'],
            'shwapno_weight_kg': best_match['weight_kg'],
            'shwapno_price_per_kg': best_match['price_per_kg'],
            'match_score': best_score
        })

print(f"DEBUG: Found {len(matched_products)} total matches.")

# Optional: filter products where price_per_kg exists (skip if many per piece)
# comparable_products = [item for item in matched_products if item['chaldal_price_per_kg'] and item['shwapno_price_per_kg']]
comparable_products = matched_products

# --- Save Results ---
output_filename = 'comparison_fish_meat_results.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(comparable_products, f, indent=4, ensure_ascii=False)

print(f"✅ Success! Comparison completed. Results saved to '{output_filename}'.")
