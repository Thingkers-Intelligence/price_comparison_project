# comparison_app/views.py
# import os
# import json
# import logging
# from django.shortcuts import render
# from django.conf import settings
# from django.contrib import messages

# logger = logging.getLogger(__name__)

# def price_comparison_view(request):
#     results_file_path = os.path.join(settings.BASE_DIR, 'comparison_app', 'data', 'comparison_results.json')
#     comparison_results = []

#     try:
#         with open(results_file_path, 'r', encoding='utf-8') as f:
#             comparison_results = json.load(f)
#         messages.success(request, f"Loaded {len(comparison_results)} matched products.")
    
#     except FileNotFoundError:
#         logger.error(f"The file {results_file_path} was not found.")
#         messages.error(request, "The comparison data file was not found. Please run the processing script.")
#     except json.JSONDecodeError:
#         logger.error(f"Error decoding JSON from {results_file_path}.")
#         messages.error(request, "The comparison data file is corrupt or empty.")

#     context = {
#         'comparison_results': comparison_results
#     }
#     return render(request, 'comparison_app/price_comparison.html', context)


# def oil_comparison_view(request):
#     # 1. Point to the new oil results file
#     results_file_path = os.path.join(settings.BASE_DIR, 'comparison_app', 'data', 'oil_comparison_results.json')
#     oil_comparison_results = []

#     try:
#         with open(results_file_path, 'r', encoding='utf-8') as f:
#             oil_comparison_results = json.load(f)
#         messages.success(request, f"Loaded {len(oil_comparison_results)} matched oil products.")
    
#     except FileNotFoundError:
#         logger.error(f"The file {results_file_path} was not found.")
#         messages.error(request, "The oil comparison data file was not found. Please run the processing script.")
#     except json.JSONDecodeError:
#         logger.error(f"Error decoding JSON from {results_file_path}.")
#         messages.error(request, "The oil comparison data file is corrupt or empty.")

#     context = {
#         # 2. Use a clear context variable name
#         'comparison_results': oil_comparison_results
#     }
#     # 3. Render the new oil-specific template
#     return render(request, 'comparison_app/oil_comparison.html', context)



import os
import json
import logging
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages

logger = logging.getLogger(__name__)

def price_comparison_view(request):
    """
    Handles the view for Vegetable products.
    """
    results_file_path = os.path.join(settings.BASE_DIR, 'comparison_app', 'data', 'comparison_results.json')
    comparison_results = []
    try:
        with open(results_file_path, 'r', encoding='utf-8') as f:
            comparison_results = json.load(f)
        messages.success(request, f"Loaded {len(comparison_results)} matched vegetable products.")
    except FileNotFoundError:
        messages.error(request, "Vegetable data file not found. Please run the processing script.")
    except json.JSONDecodeError:
        messages.error(request, "Vegetable data file is corrupt or empty.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'vegetables'  # Tell the template this is the active tab
    }
    # Render the new common base template
    return render(request, 'comparison_app/comparison_base.html', context)


def oil_comparison_view(request):
    """
    Handles the view for Oil products.
    """
    results_file_path = os.path.join(settings.BASE_DIR, 'comparison_app', 'data', 'oil_comparison_results.json')
    comparison_results = []
    try:
        with open(results_file_path, 'r', encoding='utf-8') as f:
            comparison_results = json.load(f)
        messages.success(request, f"Loaded {len(comparison_results)} matched oil products.")
    except FileNotFoundError:
        messages.error(request, "Oil data file not found. Please run the processing script.")
    except json.JSONDecodeError:
        messages.error(request, "Oil data file is corrupt or empty.")

    context = {
        'comparison_results': comparison_results,
        'active_tab': 'oil'  # Tell the template this is the active tab
    }
    # Render the new common base template
    return render(request, 'comparison_app/comparison_base.html', context)
