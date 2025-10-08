import os
import json
import re
import pandas as pd
from fuzzywuzzy import fuzz

# ---------- Helper functions ----------
def clean_name(name):
    """Clean product name for fuzzy matching"""
    if not isinstance(name, str): 
        return ""
    name = name.lower()
    name = re.sub(r'[\(\)±]', ' ', name)
    noise_words = [
        'kg', 'gm', 'g', 'ltr', 'l', 'ml', 'pcs', 'each', 'unit', 'bundle',
        'local', 'imported', 'china', 'india', 'premium', 'regular', 'combo'
    ]
    words = name.split()
    cleaned_words = [word for word in words if word not in noise_words and not word.isnumeric()]
    return " ".join(cleaned_words)

def normalize_units_and_price(product):
    """
    Normalize price to per-kg (or per-L) and return:
    price_numeric, base_unit_value, price_per_unit
    """
    name_str = product.get('name', '').lower()
    quantity_str = str(product.get('quantity', '')).lower()
    price = product.get('price')

    if 'combo' in name_str or '&' in name_str:
        return pd.Series([None, None, None])

    price_numeric, base_unit_value, unit_price = None, None, None

    # Convert price to numeric
    if price:
        try:
            price_numeric = float(re.sub(r'[^\d.]', '', str(price).replace(',', '')))
        except (ValueError, TypeError):
            pass

    # Detect quantity from name or quantity field
    pattern = r'(\d+\.?\d*)\s*(kg|gm|g|ltr|l|ml)'
    match = re.search(pattern, quantity_str) or re.search(pattern, name_str)

    if match and price_numeric is not None:
        value, unit = float(match.group(1)), match.group(2)
        # Convert everything to kg or L
        if unit in ['kg', 'ltr', 'l']:
            base_unit_value = value
        elif unit in ['g', 'gm', 'ml']:
            base_unit_value = value / 1000  # convert to kg or L

        # Compute price per unit (per kg or L)
        if base_unit_value and base_unit_value > 0:
            unit_price = round(price_numeric / base_unit_value, 2)

    return pd.Series([price_numeric, base_unit_value, unit_price])

def process_and_match(category_folder, category_name):
    print(f"--- Processing {category_name.upper()} ---")

    chaldal_file = os.path.join(category_folder, f"chaldal_{category_name}.json")
    shwapno_file = os.path.join(category_folder, f"shwapno_{category_name}.json")
    output_file = os.path.join(category_folder, f"comparison_{category_name}_results.json")

    try:
        with open(chaldal_file, 'r', encoding='utf-8') as f:
            chaldal_data = json.load(f)
        with open(shwapno_file, 'r', encoding='utf-8') as f:
            shwapno_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading {category_name}: {e}")
        return

    # Filter out placeholders or missing price
    chaldal_data = [p for p in chaldal_data if p.get('name') and p.get('price') and 'loading' not in p['name'].lower()]
    shwapno_data = [p for p in shwapno_data if p.get('name') and p.get('price') and 'loading' not in p['name'].lower()]

    chaldal_df = pd.DataFrame(chaldal_data)
    shwapno_df = pd.DataFrame(shwapno_data)

    chaldal_df['cleaned_name'] = chaldal_df['name'].apply(clean_name)
    shwapno_df['cleaned_name'] = shwapno_df['name'].apply(clean_name)

    new_cols = ['price_numeric', 'base_unit_value', 'price_per_unit']
    chaldal_df[new_cols] = chaldal_df.apply(normalize_units_and_price, axis=1)
    shwapno_df[new_cols] = shwapno_df.apply(normalize_units_and_price, axis=1)

    # ---------- Matching ----------
    matched = []
    shwapno_list = shwapno_df.to_dict('records')

    for _, c in chaldal_df.iterrows():
        if not c['price_per_unit']:
            continue
        best_match = None
        best_score = 75  # minimum fuzzy match threshold
        for s in shwapno_list:
            if not s['price_per_unit']:
                continue
            score = fuzz.token_sort_ratio(c['cleaned_name'], s['cleaned_name'])
            if score > best_score:
                best_score, best_match = score, s
        if best_match:
            matched.append({
                'chaldal_name': c['name'],
                'chaldal_price': c['price_numeric'],
                'chaldal_price_per_unit': c['price_per_unit'],
                'shwapno_name': best_match['name'],
                'shwapno_price': best_match['price_numeric'],
                'shwapno_price_per_unit': best_match['price_per_unit'],
                'match_score': best_score
            })

    # ---------- Remove duplicates per Shwapno product ----------
    seen = {}
    for item in matched:
        key = item['shwapno_name']
        diff = abs(item['chaldal_price_per_unit'] - item['shwapno_price_per_unit'])
        if key not in seen or diff < abs(seen[key]['chaldal_price_per_unit'] - seen[key]['shwapno_price_per_unit']):
            seen[key] = item
    final_matches = list(seen.values())

    # Sort by Chaldal price per unit
    final_matches.sort(key=lambda x: x['chaldal_price_per_unit'])

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_matches, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(final_matches)} cleaned matches saved to {output_file}\n")

# ---------- MAIN ----------
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    categories = ["vegetables", "oil", "fish_meat","snacks"]
    for category in categories:
        folder_path = os.path.join(base_dir, category)
        process_and_match(folder_path, category)
