import json
import urlparse

from scrapy import Spider, Request, FormRequest

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class NetgearSpider(Spider):
    name = "netgear"
    allowed_domains = ["downloads.netgear.com", "www.netgear.com"]
    start_urls = ["https://www.netgear.com/system/supportModels.json"]
    base_url = "https://www.netgear.com/"

    visited = []

    def parse(self, response):
        yield Request(
            url=urlparse.urljoin(self.base_url, "/support/download/"),
            meta={
                "data": json.loads(response.body_as_unicode())
            },
            callback=self.parse2)

    def parse2(self, response):
        for product in response.meta["data"]:
            yield FormRequest.from_response(
                response,
                meta={
                    "product": product["model"],
                    "version": product["version"],
                    "description": product["title"]},
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; FirmwareBot/1.0 +https://github.com/firmadyne/scraper)"},
                formid="form1",
                formdata={
                    "ctl00$MainContent$clickParameter": product["tcm"],
                    "__ASYNCPOST": "true"},
                callback=self.parse_product)

    def parse_product(self, response):
        for url in response.xpath("//p[contains(text(),'Firmware')]/../@href").extract():
            item = FirmwareLoader(item=FirmwareImage(), response=response)

            if response.meta["version"]:
                item.add_value("version", response.meta["version"])

            item.add_value("url", url)
            item.add_value("description", response.meta["description"])
            item.add_value("product", response.meta["product"])
            item.add_value("vendor", self.name)
            yield item.load_item()
