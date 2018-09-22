import json

from scrapy import Spider, FormRequest, Selector

from firmware.items import FirmwareImage
from firmware.loader import FirmwareLoader


class ZyXELSpider(Spider):
    name = "zyxel_new"
    allowed_domains = ["accounts.myzyxel.com", "portal.myzyxel.com"]
    start_urls = ["https://accounts.myzyxel.com/users/sign_in"]
    base_url = "https://portal.myzyxel.com"

    # http://bugmenot.com/view/myzyxel.com
    username = ""
    password = ""

    def parse(self, response):
        return FormRequest.from_response(
            response,
            formid="new_user",
            formdata={
                "user[email]": self.username,
                "user[password]": self.password
            },
            callback=self.after_login,
            dont_filter=True,
        )

    def after_login(self, response):
        # check if login succeeded before continuing
        if response.xpath("//div[@class='flash-wrapper']/node()"):
            self.logger.error("Login failed!")
            return

        csrf_token = response.xpath("//meta[@name='csrf-token']/@content").extract_first()

        return FormRequest(url="https://portal.myzyxel.com/my/firmwares/datatable.json",
                           headers={"X-CSRF-Token": csrf_token},
                           formdata={"fw_version": "the_latest", },
                           callback=self.parse_product)

    def parse_product(self, response):
        data = json.loads(response.body_as_unicode())

        if not data:
            self.logger.error("Error!")
            return

        for entry in data["data"]:
            item = FirmwareLoader(item=FirmwareImage(),
                                  response=response, date_fmt=["%B %d, %Y"])

            date = Selector(text=entry[3]).xpath("//span/text()").extract_first()

            item.add_value("version", entry[2])
            item.add_value("date", date)
            item.add_value("url", entry[0])
            item.add_value("product", entry[1])
            item.add_value("vendor", self.name)
            yield item.load_item()
