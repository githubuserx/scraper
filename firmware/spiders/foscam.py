import json
import urlparse

from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class FoscamSpider(Spider):
    name = "foscam"
    allowed_domains = ["foscam.com", "www.foscam.com"]
    start_urls = [
        "https://www.foscam.com/downloads/firmwareajaxjson.html?count=1000"]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for product in data["row"]:
            url = "https://www.foscam.com/downloads/firmware_details.html?id={}"

            yield Request(
                url=url.format(product["pid"]),
                meta={"product": product["productname"]},
                headers={"Referer": "https://www.foscam.com/downloads/index.html"},
                callback=self.parse_product
            )

    def parse_product(self, response):
        table = response.xpath("//table[@class='down_table']//tr")[1:]

        for row in table:
            item = FirmwareLoader(item=FirmwareImage(), response=response)

            item.add_value("version", row.xpath("td[1]/text()").extract_first())
            item.add_value("date", row.xpath("td[2]/text()").extract_first())
            item.add_value("description", row.xpath("td[4]/text()").extract_first())

            # FIXME: download url contains '.html' which is filtered out by the pipeline
            item.add_value("url", urlparse.urljoin("https://www.foscam.com/",
                                                   row.xpath("td[6]/a/@href").extract_first()))
            item.add_value("product", response.meta["product"])
            item.add_value("vendor", self.name)
            yield item.load_item()
