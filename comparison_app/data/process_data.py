import json
import re
import pandas as pd
from fuzzywuzzy import fuzz

def clean_name(name):
    """Cleans a product name for fuzzy matching."""
    if not isinstance(name, str): return ""
    name = name.lower()
    name = re.sub(r'[\(\)±]', ' ', name)
    # A comprehensive list of noise words for both categories
    noise_words = [
        'kg', 'gm', 'g', 'ltr', 'l', 'ml', 'pcs', 'each', 'unit', 'bundle', 
        'local', 'imported', 'china', 'india', 'premium', 'regular', 'combo'
    ]
    words = name.split()
    cleaned_words = [word for word in words if word not in noise_words and not word.isnumeric()]
    return " ".join(cleaned_words)

def normalize_units_and_price(product):
    """
    Parses a product to find its weight/volume and calculate a normalized price per base unit (KG/Ltr).
    It handles both weight (kg/gm) and volume (ltr/ml) and ignores combo packs.
    """
    name_str = product.get('name', '').lower()
    quantity_str = str(product.get('quantity', '')).lower()
    price = product.get('price')
    
    if 'combo' in name_str or '&' in name_str:
        return pd.Series([None, None, None])

    price_numeric, unit_price, base_unit_value = None, None, None

    if price:
        try: price_numeric = float(re.sub(r'[^\d,]', '', str(price).replace(',', '')))
        except (ValueError, TypeError): pass

    # A flexible regex that finds all common weight and volume units
    pattern = r'(\d+\.?\d*)\s*(kg|gm|g|ltr|l|ml)'
    
    match = re.search(pattern, quantity_str)
    if not match:
        match = re.search(pattern, name_str)
    
    if match and price_numeric is not None:
        value, unit = float(match.group(1)), match.group(2)
        
        if unit in ['ltr', 'l', 'kg']:
            base_unit_value = value
        elif unit in ['ml', 'gm', 'g']:
            base_unit_value = value / 1000  # Convert ml to Ltr or gm to Kg
        
        if base_unit_value and base_unit_value > 0:
            unit_price = round(price_numeric / base_unit_value, 2)
            
    return pd.Series([price_numeric, base_unit_value, unit_price])


def process_and_match(chaldal_file, shwapno_file, output_file, category_name):
    """
    A reusable function to load, process, match, and save comparison data for a category.
    """
    print(f"--- Processing {category_name.capitalize()} ---")
    try:
        with open(chaldal_file, 'r', encoding='utf-8') as f: chaldal_data = json.load(f)
        with open(shwapno_file, 'r', encoding='utf-8') as f: shwapno_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Could not find '{e.filename}'. Skipping this category.")
        return

    chaldal_data = [p for p in chaldal_data if p.get("name") and "loading" not in p["name"].lower()]
    chaldal_df, shwapno_df = pd.DataFrame(chaldal_data), pd.DataFrame(shwapno_data)

    chaldal_df['cleaned_name'] = chaldal_df['name'].apply(clean_name)
    shwapno_df['cleaned_name'] = shwapno_df['name'].apply(clean_name)

    new_cols = ['price_numeric', 'base_unit_value', 'price_per_unit']
    chaldal_df[new_cols] = chaldal_df.apply(normalize_units_and_price, axis=1)
    shwapno_df[new_cols] = shwapno_df.apply(normalize_units_and_price, axis=1)

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
                'chaldal_price': chaldal_product['price_numeric'],
                'chaldal_price_per_unit': chaldal_product['price_per_unit'],
                'shwapno_name': best_match['name'], 'shwapno_quantity': best_match['quantity'], 'shwapno_url': best_match['url'],
                'shwapno_price': best_match['price_numeric'],
                'shwapno_price_per_unit': best_match['price_per_unit'],
                'match_score': best_score
            })

    comparable_products = [
        item for item in matched_products 
        if item['chaldal_price_per_unit'] is not None 
        and item['shwapno_price_per_unit'] is not None
    ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparable_products, f, indent=4, ensure_ascii=False)

    print(f"✅ Success! Found {len(comparable_products)} comparable matches for {category_name}.")
    print(f"Clean results saved to '{output_file}'\n")


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Process the vegetable files
    process_and_match(
        chaldal_file='chaldal_products.json',
        shwapno_file='shwapno_products.json',
        output_file='comparison_results.json',
        category_name='vegetables'
    )

    # Process the oil files
    process_and_match(
        chaldal_file='chaldal_oil.json',
        shwapno_file='shwapno_oil.json',
        output_file='oil_comparison_results.json',
        category_name='oil'
    )

    #seeejaan
    # Process the fish and meat files
    process_and_match(
        chaldal_file='chaldal_fish_meat.json',
        shwapno_file='shwapno_meat_meat.json',
        output_file='comparison_fish_meat_results.json',
        category_name='fish and meat'
    )