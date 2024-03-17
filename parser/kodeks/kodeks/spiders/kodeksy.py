import os
import scrapy
import json
import requests
import logging
from bs4 import BeautifulSoup

class KodeksykzSpider(scrapy.Spider):
    # dir_list = os.listdir('./')
    name = "kodeksy"
    start_urls = ["https://kodeksy-kz.com/ka/kodeksy.htm"]
    res = []
    title = ""
    all_zakons = []

    def yield_zakon(self):
        if self.all_zakons:
            url = self.all_zakons.pop(0)
            return scrapy.Request(url, self.parse_zakon)
        else:
            print("all done")

    def parse(self, response):
        logging.info("Parsing main page")
        zakons = response.xpath('//a[@class="nava"]/@href')
        self.all_zakons = list(response.urljoin(zakon.extract()) for zakon in zakons)
        self.all_zakons = self.all_zakons[2:]
        yield self.yield_zakon()

    def parse_zakon(self, response):
        self.title = response.css('h1::text').get()
        # temp = self.title + '.json'
        # if temp in self.dir_list:
        #     logging.info('salkjflkasjflkajflAKJHFKJHKJFSJK')
        #     yield self.yield_zakon()
        #     return

        logging.info("Parsing zakon page")
        law_status = response.xpath('//div[@id="law_status"]/div[@id="law_valid"]/text()').get()
        if law_status:
            pages = response.css('ul.no_dsk li b::text').getall()[-1]
            s = ""
            for i in pages:
                if i >= '0' and i <= '9':
                    s += i
            pages = int(s)
            for page in range(1, pages + 1):
                url = response.url[:-4] + '/' + str(page) + '.htm'
                resp = requests.get(url)
                if resp.status_code == 200:
                    yield response.follow(
                        url,
                        callback=self.parse_article
                    )
            self.to_json()
        yield self.yield_zakon()

    def parse_article(self, response):
        logging.info("Parsing article page")
        text_content = response.xpath('//div[@id="statya"]').get()
        tags = ['h1', 'h3']
        soup = BeautifulSoup(text_content, 'html.parser')

        for t in tags:
            [s.extract() for s in soup(t)]

        text = ''.join([el.text for el in soup.find_all()])
        statya = response.css('div#statya h1::text').getall()
        cleaned_text = ''.join(text).strip()
        data = {
            statya[1]: cleaned_text
        }
        self.res.append(data)
        logging.info("Data appended to res list")

    def to_json(self):
        logging.info('saving to json')
        with open(self.title+'.json', 'w', encoding='utf-8') as f:
            json.dump(self.res, f, ensure_ascii=False, indent=4)
        self.res = []
