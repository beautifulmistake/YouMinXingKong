import json
import os

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.signals import spider_closed
from YouMin.items import PhoneGameItem


class YouMinSpider(scrapy.Spider):
    name = "youMin"

    def __init__(self, settings):
        super().__init__()
        self.record_file = open(os.path.join(settings.get("JSON_PATH"), f'{self.name}.json'), "w+", encoding="utf8")
        self.record_file.write('[')
        self.keyword_file_list = os.listdir(settings.get("KEYWORD_PATH"))
        # 游戏专区
        self.url_base_1 = "http://so.gamersky.com/all/z?s={}&type=hot&sort=des"
        # 众评区
        self.url_base_2 = "http://so.gamersky.com/all/ku?s={}&type=hot&sort=des"
        # 综合区
        # self.url_base_3 = "http://so.gamersky.com/?s={}&type=hot&sort=des"
        # 单独请求这个结果下面的地址，可以获取搜索的结果
        self.url_base_4 = "http://so.gamersky.com/part/snav2/105/?s={}&type=hot&sort=des"

    def start_requests(self):
        # 判断关键字文件是否存在
        if not self.keyword_file_list:
            # 抛出异常并关闭爬虫
            raise CloseSpider("需要关键字文件")
        # 遍历关键字文件路径
        for keyword_file in self.keyword_file_list:
            # 获取关键字文件路径
            file_path = os.path.join(self.settings.get("KEYWORD_PATH"), keyword_file)
            # 读取关键字文件
            with open(file_path, 'r', encoding='utf-8') as f:
                # 测试代码
                # for keyword in f.readlines()[121:122]:
                for keyword in f.readlines():
                    # 消除末尾的空格
                    keyword = keyword.strip()
                    # 发起请求
                    yield scrapy.Request(url=self.url_base_4.format(keyword), meta={'search_key': keyword})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 获取配置信息
        settings = crawler.settings
        # 爬虫
        spider = super(YouMinSpider, cls).from_crawler(crawler, settings, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=spider_closed)
        return spider

    def spider_closed(self, spider):
        # 输出日志：关闭爬虫
        self.logger.info('Spider closed: %s', spider.name)
        spider.record_file.write("]")
        spider.record_file.close()

    def parse(self, response):
        # 获取搜索关键字
        search_key = response.meta['search_key']
        # 查看获取的响应
        print(response.text)
        # 专区的搜索结果
        count_1 = response.xpath('//div[@class="snav2"]/a[2]/span/text()').extract_first()
        # 众评的搜索结果
        count_2 = response.xpath('//div[@class="snav2"]/a[3]/span/text()').extract_first()
        # 总的搜索结果
        counts = int(count_1) + int(count_2)
        # 分别判断搜索结果
        if count_1 != "0":
            # 发起请求，获取专区的结果
            yield scrapy.Request(url=self.url_base_1.format(search_key), callback=self.list_parse,
                                 meta={'search_key': search_key})
        if count_2 != "0":
            # 发起请求，获取众评区域结果
            yield scrapy.Request(url=self.url_base_2.format(search_key), callback=self.list_parse,
                                 meta={'search_key': search_key})
        # 将索索结果写入文件
        self.record_file.write(json.dumps({"search_key": search_key, "counts": counts}, ensure_ascii=False))
        self.record_file.write(",\n")
        self.record_file.flush()

    def list_parse(self, response):
        # 查看响应内容
        # print(response.text)
        # 搜索关键字
        search_key = response.meta['search_key']
        # 创建item对象
        item = PhoneGameItem()
        item['search_key'] = search_key
        # 获取详情页的链接
        detail_urls = response.xpath('//div[@class="Mid2_L"]/ul[@class="ImgY contentpaging"]/li/a/@href').extract()
        # 获取图片的链接
        pic_urls = response.xpath('//div[@class="Mid2_L"]/ul[@class="ImgY contentpaging"]/'
                                  'li/a/div[@class="img"]/img/@src').extract()
        # APP名称
        app_names = response.xpath('//div[@class="Mid2_L"]/ul[@class="ImgY contentpaging"]/'
                                   'li/a/div[@class="img"]/img/@title').extract()
        # 获取最后一个a标签，用于判断时否有下一页
        next_page = response.xpath('//span[@id="pe100_page_pic_tu"]/a[last()]/@href').extract_first()
        print("查看下一页的请求：", next_page)
        for detail_url in detail_urls:
            item['detail_url'] = detail_url
        for pic_url in pic_urls:
            item['pic_url'] = pic_url
        for app_name in app_names:
            item['app_name'] = app_name
        yield item
        # 判断是否有下一页
        if next_page != "javascript:void(0)":
            url = "http://so.gamersky.com/all/z" + next_page[0]
            # 发起下一页的请求
            yield scrapy.Request(url=url, callback=self.list_parse, meta={'search_key': search_key})
