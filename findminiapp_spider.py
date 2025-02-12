import os
import time
import scrapy
import re
import emoji
from google_sheets_manager import GoogleSheetsManager

timestamp = time.strftime("%Y%m%d_%H%M%S")

class FindMiniAppSpider(scrapy.Spider):
    name = "findminiapp"
    start_urls = ["https://www.findmini.app/category/"]
    base_url = "https://www.findmini.app"

    custom_settings = {
        "LOG_STDOUT": True,
        "LOG_FILE": f"logs/findminiapp_{timestamp}.log",
        "AUTOTHROTTLE_ENABLED": True,
        "DOWNLOAD_TIMEOUT": 15,
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 8,
        "RETRY_TIMES": 5,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.sheet_manager = GoogleSheetsManager()

    def parse(self, response):
        if not self.sheet_manager.spreadsheet_id:
            self.logger.error(
                "No valid spreadsheet ID. Stopping the scraping process.")
            return

        category_links = {response.urljoin(link) for link in
                          response.xpath('/html/body/div[1]/main/div[1]/a/@href').getall() if
                          "/category/" in link}
        for link in category_links:
            yield scrapy.Request(url=link, callback=self.parse_category,
                                 meta={'category_link': link, 'page': 1})

    def parse_category(self, response):
        category_name = response.xpath('/html/body/div[1]/main/h1/text()').get(
            default="Unknown").strip()

        for app_link in map(response.urljoin,
                            response.xpath('/html/body/div[1]/main/div[3]//a/@href').getall()):
            yield scrapy.Request(url=app_link, callback=self.parse_app,
                                 meta={'category': category_name})

        next_page = f"{response.meta['category_link']}{response.meta['page'] + 1}"
        yield scrapy.Request(url=next_page, callback=self.parse_category,
                             meta={'category_link': response.meta[
                                 'category_link'],
                                   'page': response.meta['page'] + 1},
                             errback=self.handle_error, dont_filter=True)

    def handle_error(self, failure):
        """Handle errors (e.g., 404) to stop pagination gracefully."""
        if failure.value.response and failure.value.response.status == 404:
            self.logger.info(
                f"Stopping pagination: {failure.request.url} returned 404.")

    def parse_app(self, response):
        app_name = response.xpath(
            '/html/body/div[1]/main/div/div[2]/div[1]/div/div[1]/h1/text()').get(
            default="Unknown").strip()
        description = " ".join(response.xpath(
            '/html/body/div[1]/main/div/div[4]/div[1]/div[1]/span/text()').getall()).strip()
        language = self.remove_emojis(", ".join(response.xpath(
            '//h3[contains(text(), "Interface languages")]/following-sibling::span/text()').getall())).strip()
        useful_links = ", ".join(response.xpath(
            '//h3[contains(text(), "More links")]/following-sibling::ul//a/@href').getall())
        user_count = self.remove_emojis(response.xpath(
            '/html/body/div[1]/main/div/div[2]/div[1]/div/div[2]/span[2]/span/text()').get(
            default="Unknown")).strip()
        category = response.meta['category']
        app_link = self.extract_telegram_link(response)
        images = [f'=IMAGE("{response.urljoin(img)}"; 4; 200; 100)' for img in
                  response.xpath(
                      '/html/body/div[1]/main/div/div[3]/div//img/@src').getall()]

        self.data.append(
            [app_name, description, app_link, response.url, category,
             user_count, language, useful_links] + images)

    def extract_telegram_link(self, response):
        """Extract Telegram app link from onclick attribute."""
        onclick_value = response.xpath(
            '//button[contains(@onclick, "window.open")]/@onclick').get(
            "Unknown").strip()
        match = re.search(r"window\.open\('([^']+)',?\s*'[^']*'\)",
                          onclick_value)
        return match.group(1) if match else "Unknown"

    def remove_emojis(self, text):
        """Remove emojis from text."""
        return emoji.replace_emoji(text, replace="")

    def closed(self, reason):
        """Send all data to Google Sheets at once when Scrapy finishes."""
        self.sheet_manager.store_data(self.data)


if __name__ == "__main__":
    from scrapy.cmdline import execute
    os.makedirs("logs", exist_ok=True)
    execute(["scrapy", "runspider", "findminiapp_spider.py"])
