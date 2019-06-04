# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class YouminItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PhoneGameItem(scrapy.Item):
    search_key = scrapy.Field()  # 搜索关键字
    app_name = scrapy.Field()   # APP名称
    detail_url = scrapy.Field()     # 详情页链接
    pic_url = scrapy.Field()    # 图片链接
