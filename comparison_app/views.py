# comparison_app/views.py
import os
import json
import logging
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages

logger = logging.getLogger(__name__)

def load_comparison_file(filename):
    """
    Load a JSON comparison file and return the list.
    If file is missing or corrupt, return empty list.
    """
    results_file_path = os.path.join(settings.BASE_DIR, 'comparison_app', 'data', filename)
    try:
        with open(results_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {results_file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"JSON decode error in file: {results_file_path}")
        return []

# --- Vegetable comparison view ---
def price_comparison_view(request):
    comparison_results = load_comparison_file('vegetables\comparison_vegetables_results.json')

    if comparison_results:
        messages.success(request, f"Loaded {len(comparison_results)} matched vegetable products.")
    else:
        messages.warning(request, "No vegetable products found. Please run the processing script.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'vegetables'
    }
    return render(request, 'comparison_app/comparison_base.html', context)

# --- snacks comparison view ---
def snacks_comparison_view(request):
    comparison_results = load_comparison_file('snacks\comparison_snacks_results.json')

    if comparison_results:
        messages.success(request, f"Loaded {len(comparison_results)} matched vegetable products.")
    else:
        messages.warning(request, "No Snacks products found. Please run the processing script.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'snacks'
    }
    return render(request, 'comparison_app/comparison_base.html', context)

# --- Oil comparison view ---
def oil_comparison_view(request):
    comparison_results = load_comparison_file('oil\comparison_oil_results.json')

    if comparison_results:
        messages.success(request, f"Loaded {len(comparison_results)} matched oil products.")
    else:
        messages.warning(request, "No oil products found. Please run the processing script.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'oil'
    }
    return render(request, 'comparison_app/comparison_base.html', context)

def fish_meat_comparison_view(request):
    comparison_results = load_comparison_file('fish_meat\comparison_fish_meat_results.json')  # corrected filename

    if comparison_results:
        messages.success(request, f"Loaded {len(comparison_results)} matched fish & meat products.")
    else:
        messages.warning(request, "No fish & meat products found. Please run the processing script.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'fish_meat'
    }
    # Use the common template for all categories
    return render(request, 'comparison_app/comparison_base.html', context)