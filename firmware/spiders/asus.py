import json

from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class AsusSpider(Spider):
    name = "asus"
    region = "global"
    allowed_domains = ["asus.com"]
    start_urls = [
        "https://www.asus.com/support/api/product.asmx/GetPDLevel"
        "?website=global"
        "&type=1"
        "&typeid=0"
        "&productflag=0"
    ]

    visited = []

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        if "category" not in response.meta:
            categories = []

            for _, level in data["Result"]["ProductLevel"].items():
                categories += level["Items"]

            for category in categories:
                url = "https://www.asus.com/support/api/product.asmx/GetPDLevel" \
                      "?website=global" \
                      "&type=1" \
                      "&typeid={}" \
                      "&productflag=1"

                yield Request(
                    url=url.format(category["Id"]),
                    meta={"category": category["Name"]},
                    headers={"Referer": response.url,
                             "X-Requested-With": "XMLHttpRequest"},
                    callback=self.parse)

        elif "product" not in response.meta:
            for product in data["Result"]["Product"]:
                url = "https://www.asus.com/support/api/product.asmx/GetPDBIOS" \
                      "?website=global" \
                      "&pdhashedid={}"

                yield Request(
                    url=url.format(product["PDHashedId"]),
                    meta={
                        "category": response.meta["category"],
                        "product": product["PDName"]
                    },
                    headers={"Referer": response.url,
                             "X-Requested-With": "XMLHttpRequest"},
                    callback=self.parse_product)

    def parse_product(self, response):
        data = json.loads(response.body_as_unicode())

        if data["Status"] != "SUCCESS":
            return

        for obj in data["Result"]["Obj"]:
            if "firmware" not in obj["Name"].lower():
                continue

            for entry in obj["Files"]:
                item = FirmwareLoader(item=FirmwareImage(),
                                      response=response, date_fmt=["%Y/%m/%d"])

                item.add_value("version", entry["Version"])
                item.add_value("date", entry["ReleaseDate"])
                item.add_value("description", entry["Description"])
                item.add_value("url", entry["DownloadUrl"]["Global"])
                item.add_value("product", response.meta["product"])
                item.add_value("vendor", self.name)
                yield item.load_item()
