import os
import json
import re
import pandas as pd
from fuzzywuzzy import fuzz

# --- Helper Functions ---
def clean_name(name):
    if not isinstance(name, str):
        return ""
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
        try:
            price_numeric = float(re.sub(r'[^\d.]', '', str(price)))
        except (ValueError, TypeError):
            pass

    pattern = r'(\d+\.?\d*)\s*(kg|gm|g)\b'
    match = re.search(pattern, quantity_str)
    if not match:
        match = re.search(pattern, name_str)

    if match and price_numeric is not None:
        value, unit = float(match.group(1)), match.group(2)
        if unit == 'kg':
            weight_in_kg = value
        elif unit in ['gm', 'g']:
            weight_in_kg = value / 1000
        if weight_in_kg and weight_in_kg > 0:
            price_per_kg = round(price_numeric / weight_in_kg, 2)
            price_per_500gm = round(price_per_kg * 0.5, 2)
            price_per_100gm = round(price_per_kg * 0.1, 2)
    
    return pd.Series([price_numeric, weight_in_kg, price_per_kg, price_per_500gm, price_per_100gm])

def match_category(category_folder, category_name):
    print(f"--- Matching {category_name.upper()} ---")
    
    chaldal_file = os.path.join(category_folder, f"chaldal_{category_name}.json")
    shwapno_file = os.path.join(category_folder, f"shwapno_{category_name}.json")
    output_file = os.path.join(category_folder, f"comparison_{category_name}_results.json")

    # Load JSON files
    try:
        with open(chaldal_file, 'r', encoding='utf-8') as f:
            chaldal_data = json.load(f)
        with open(shwapno_file, 'r', encoding='utf-8') as f:
            shwapno_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e.filename}")
        return

    # Remove invalid products
    chaldal_data = [p for p in chaldal_data if p.get("name") and "loading" not in p["name"].lower()]

    chaldal_df, shwapno_df = pd.DataFrame(chaldal_data), pd.DataFrame(shwapno_data)
    chaldal_df['cleaned_name'] = chaldal_df['name'].apply(clean_name)
    shwapno_df['cleaned_name'] = shwapno_df['name'].apply(clean_name)

    new_cols = ['price_numeric', 'weight_kg', 'price_per_kg', 'price_per_500gm', 'price_per_100gm']
    chaldal_df[new_cols] = chaldal_df.apply(normalize_weight_and_price, axis=1)
    shwapno_df[new_cols] = shwapno_df.apply(normalize_weight_and_price, axis=1)

    # Matching using fuzzy logic
    matched_products = []
    shwapno_list = shwapno_df.to_dict('records')

    for _, chaldal_product in chaldal_df.iterrows():
        best_match, best_score = None, 75
        for shwapno_product in shwapno_list:
            score = fuzz.token_sort_ratio(chaldal_product['cleaned_name'], shwapno_product['cleaned_name'])
            if score > best_score:
                best_score, best_match = score, shwapno_product
        if best_match:
            matched_products.append({
                'chaldal_name': chaldal_product['name'],
                'chaldal_price': chaldal_product['price_numeric'],
                'chaldal_price_per_kg': chaldal_product['price_per_kg'],
                'shwapno_name': best_match['name'],
                'shwapno_price': best_match['price_numeric'],
                'shwapno_price_per_kg': best_match['price_per_kg'],
                'match_score': best_score
            })

    # Keep only products with price_per_kg available
    comparable = [
        item for item in matched_products
        if item['chaldal_price_per_kg'] is not None
        and item['shwapno_price_per_kg'] is not None
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparable, f, indent=4, ensure_ascii=False)

    print(f"✅ Found {len(comparable)} comparable matches. Saved to '{output_file}'\n")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Use current folder as data folder
    data_dir = os.path.dirname(os.path.abspath(__file__))

    categories = ["vegetables", "oil", "fish_meat","snacks"]

    for category in categories:
        folder_path = os.path.join(data_dir, category)
        match_category(folder_path, category)
