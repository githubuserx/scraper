import json
import urlparse

from scrapy import Spider, Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class NetgearSpider(Spider):
    name = "netgear_alt"
    allowed_domains = ["netgear.com", "www.netgear.com"]
    start_urls = ["https://www.netgear.com/system/supportModels.json"]
    base_url = "https://www.netgear.com/"

    visited = []

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        if not data:
            return

        for product in data:
            yield Request(
                url=urlparse.urljoin(self.base_url, product["url"]),
                meta={
                    "product": product["model"],
                    "version": product["version"],
                    "description": product["title"],
                },
                callback=self.parse_product)

    def parse_product(self, response):
        urls = response \
            .xpath("//h3[contains(text(),'Firmware')]/following-sibling::section//a[@class='btn']/@href") \
            .extract()

        for url in urls:
            item = FirmwareLoader(item=FirmwareImage(),
                                  response=response, date_fmt=["%Y.%m.%d"])

            if response.meta["version"]:
                item.add_value("version", response.meta["version"])

            item.add_value("url", url)
            item.add_value("description", response.meta["description"])
            item.add_value("product", response.meta["product"])
            item.add_value("vendor", self.name)
            yield item.load_item()
