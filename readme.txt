#project Directoory
price_comparison_project

#Activate virtual environemnt
source ./priceComparisonVenv/bin/activate

# Runserver
python3 manage.py runserver  


#run scrapy to collect daily data
# cd price_comparison_project/comparison_app/scrapers/price_comparison_scrapy_project
scrapy crawl chaldal_oil -o chaldal_oil.json
scrapy crawl shwapno_oil -o shwapno_oil.json