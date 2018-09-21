import urlparse

from scrapy import Spider
from scrapy.http import Request

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class BelkinSpider(Spider):
    name = "belkin"
    allowed_domains = ["belkin.com", "belkin.force.com", "update.havaremoteserver.com"]
    start_urls = ["https://www.belkin.com/us/search?text=firmware&type=support_downloads"]

    def parse(self, response):
        for product in response.xpath("//ul[@class='support-list']/li/a"):
            if "firmware" in product.xpath("text()").extract_first().lower():
                yield Request(
                    url=urlparse.urljoin("https://www.belkin.com/us/",
                                         product.xpath("@href").extract_first()),
                    headers={"Referer": response.url},
                    callback=self.parse_product)

    def parse_product(self, response):
        article = response.xpath("//div[@class='support-article']")
        product = article.xpath("@data-article-title").extract_first() \
            .replace(u"\u2013", "-") \
            .rsplit("-", 1)[0] \
            .strip()

        # model number
        model = product.rsplit(",", 1)
        if len(model) > 1:
            product = model[1].strip()

        text = article.xpath("//text()").extract()
        href = article.xpath("//a[(.|node())//text()='Download']/@href").extract_first()
        vers = article.xpath("//node()[contains(text(),'Version')]/text()").extract_first()
        vers_href = href.rsplit("_", 1)[-1].rsplit(".", 1)[0]

        version = None

        if len(vers_href) <= 8 and any(c.isdigit() for c in vers_href):
            version = vers_href
        elif len(vers) <= 8:
            version = vers.split(" ", 1)[-1]

        item = FirmwareLoader(item=FirmwareImage(),
                              response=response,
                              date_fmt=["%b %d, %Y", "%B %d, %Y",
                                        "%m/%d/%Y"])
        if version:
            item.add_value("version", version)

        item.add_value("date", item.find_date(text))
        item.add_value("url", href)
        item.add_value("product", product)
        item.add_value("vendor", self.name)
        yield item.load_item()
