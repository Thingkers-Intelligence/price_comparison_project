import scrapy
from scrapy_playwright.page import PageMethod

# 1. New class name
class ShwapnoOilSpider(scrapy.Spider):
    # 2. New unique name
    name = 'shwapno_oil'

    custom_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }
    
    def start_requests(self):
        yield scrapy.Request(
            # 3. New URL
            'https://www.shwapno.com/oil',
            headers=self.custom_headers,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div#product-grid", timeout=60000),
                    PageMethod("wait_for_timeout", 5000) 
                ],
            }
        )

    def parse(self, response):
        # This parsing logic is still correct for the oil page
        products = response.css('div.product-box')

        for product in products:
            price_text = product.css('.product-price .active-price::text').get()
            
            quantity_text = None
            quantity_text = product.css('button.product-box-quantity::text').get()
            if not quantity_text:
                quantity_text = product.css('select.product-box-quantity option::text').get()
            if not quantity_text:
                quantity_text = product.css('.product-price span:last-child::text').get()
            
            cleaned_quantity = quantity_text.strip() if quantity_text else None

            yield {
                'source': 'shwapno',
                'name': product.css('.product-box-title a::text').get(),
                'price': price_text.strip() if price_text else None,
                'quantity': cleaned_quantity, 
                'url': response.urljoin(product.css('.product-box-title a::attr(href)').get()),
                'image_url': product.css('.product-box-gallery img::attr(src)').get(),
            }