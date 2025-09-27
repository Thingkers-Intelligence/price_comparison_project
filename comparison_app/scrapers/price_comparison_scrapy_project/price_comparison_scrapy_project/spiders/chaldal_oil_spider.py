import scrapy

# MODIFIED: Changed the class name for clarity
class ChaldalOilSpider(scrapy.Spider):
    # MODIFIED: Gave the spider a new, unique name
    name = 'chaldal_oil'
    
    # MODIFIED: Updated the URL to the 'oil' category
    start_urls = ['https://chaldal.com/oil']

    # The User-Agent can remain the same
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    }

    def parse(self, response):
        """
        This function parses the Chaldal product category page.
        The logic here is identical to the vegetable spider because the
        website structure is the same.
        """
        products = response.css('div.product')

        for product in products:
            is_discounted = product.css('.discountedPrice').get()
            
            if is_discounted:
                price_original = product.css('.price span:last-child::text').get()
                price_current = product.css('.discountedPrice span:last-child::text').get()
            else:
                price_original = None
                price_current = product.css('.price span:last-child::text').get()

            yield {
                'source': 'chaldal', # You can keep this or change it if you like
                'name': product.css('.name::text').get(),
                'quantity': product.css('.subText::text').get(),
                'price_original': price_original,
                'price': price_current,
                'url': response.urljoin(product.css('a.btnShowDetails::attr(href)').get()),
            }