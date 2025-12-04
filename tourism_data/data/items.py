import scrapy

class QyerCityItem(scrapy.Item):
    country = scrapy.Field()
    city = scrapy.Field()
    city_en = scrapy.Field()
    peopleNum = scrapy.Field()
    hotSpot = scrapy.Field()
    cityDetail = scrapy.Field()
    imgUrl = scrapy.Field()

class QyerCommentItem(scrapy.Item):
    cityEn = scrapy.Field()
    userName = scrapy.Field()
    comment = scrapy.Field()
    commentTime = scrapy.Field()
    praiseNum = scrapy.Field()

class MafengwoCommentItem(scrapy.Item):
    scenicSpot = scrapy.Field()
    date = scrapy.Field()
    star = scrapy.Field()
    comment = scrapy.Field()

class QunarScenicItem(scrapy.Item):
    city = scrapy.Field()
    spot_name = scrapy.Field()      # 景点名称
    strategy_sum = scrapy.Field()   # 攻略数量
    star = scrapy.Field()           # 评分
    intro = scrapy.Field()          # 简介
    rank = scrapy.Field()           # 排名
    lng = scrapy.Field()            # 经度
    lat = scrapy.Field()            # 纬度
    comment_sum = scrapy.Field()    # 点评数量
    visitors = scrapy.Field()       # 多少驴友来过