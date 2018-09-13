import json
import re

from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class CanonSpider(Spider):
    name = "canon"
    allowed_domains = ["www.canon-europe.com"]
    start_urls = ["https://www.canon-europe.com/search/productselector/"]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for product in data["support_consumer_products"]:
            url = "https://www.canon-europe.com/supportproduct/gettabcontent/" \
                  "?type=firmware" \
                  "&productTcmUri={}"

            yield Request(
                url=url.format(product["id"]),
                meta={"product": product["name"]},
                headers={"Referer": response.url},
                callback=self.parse_download)

    def parse_download(self, response):
        for entry in response.xpath("//a[text()='Download']/@onclick").extract():

            keys = ["hasLicenseAgreement", "downloadUrl", "licenseAgreementTcmUri", "isPDF", "isSN",
                    "supportContentType", "bundle", "contentType", "contentTitle", "contentId", "enTitle",
                    "contentDate"]

            entry = re.search(r"\((.+)\)", entry).group(1).replace("'", "")
            entry = [x.strip() for x in entry.split(",")]

            entry = dict(zip(keys, entry))

            if "false" in entry["isSN"].lower():
                item = FirmwareLoader(item=FirmwareImage(),
                                      response=response, date_fmt=["%Y.%m.%d"])

                item.add_value("version", FirmwareLoader.find_version(entry["contentId"]))
                item.add_value("date", entry["contentDate"])
                item.add_value("description", entry["contentTitle"])
                item.add_value("url", entry["downloadUrl"])
                item.add_value("product", response.meta["product"])
                item.add_value("vendor", self.name)
                yield item.load_item()
