# shwapno_meat_fish_spider.py
import scrapy
from scrapy_playwright.page import PageMethod

class ShwapnoMeatFishSpider(scrapy.Spider):
    name = "shwapno_meat_fish"

    custom_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 ..."
    }

    def start_requests(self):
        yield scrapy.Request(
            "https://www.shwapno.com/meat-and-fish",
            headers=self.custom_headers,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div#product-grid", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),
                ],
            }
        )

    def parse(self, response):
        for product in response.css("div.product-box"):
            price_text = product.css(".product-price .active-price::text").get()
            quantity_text = (
                product.css("button.product-box-quantity::text").get()
                or product.css("select.product-box-quantity option::text").get()
                or product.css(".product-price span:last-child::text").get()
            )
            yield {
                "source": "shwapno",
                "name": product.css(".product-box-title a::text").get(),
                "price": price_text.strip() if price_text else None,
                "quantity": quantity_text.strip() if quantity_text else None,
                "url": response.urljoin(product.css(".product-box-title a::attr(href)").get()),
                "image_url": product.css(".product-box-gallery img::attr(src)").get(),
            }
