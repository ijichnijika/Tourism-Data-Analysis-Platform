import scrapy
import json
import time
from tourism_data.items import QyerCityItem, QyerCommentItem


class QyerSpider(scrapy.Spider):
    name = 'qyer'
    allowed_domains = ['qyer.com']
    country_en_dict = {
        '中国': 'china', '美国': 'usa', '英国': 'uk', '俄罗斯': 'russia',
        '法国': 'france', '日本': 'japan', '韩国': 'south-korea'
    }


    city_id_dict = {
        'china': {
            'hong-kong': 50, 'macau': 51, 'taipei': 52, 'taiwan': 11186,
            'beijing': 11593, 'shanghai': 11595, 'chengdu': 11800,
            'guangzhou': 11808, 'hangzhou': 11690, 'nanjing': 12479,
            'xiamen': 12486, 'shenzhen': 12189, 'chongqing': 11596,
            'sanya': 12259, 'suzhou': 12478, 'zhuhai': 12190,
            'xian': 11899, 'wuhan': 11711, 'dalian': 11645, 'kenting': 9820
        },
        'usa': {
            'los-angeles': 71, 'new-york': 69
        }
    }

    def start_requests(self):
        # 1. 启动城市排名爬取
        for key, value in self.country_en_dict.items():
            for page in range(1, 171):
                url = f'https://place.qyer.com/{value}/citylist-0-0-{page}/'
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_city_rank,
                    meta={'country': key}
                )

        # 2. 启动城市评论爬取
        for country_code, cities in self.city_id_dict.items():
            for city_en, city_id in cities.items():
                # 先请求第1页
                yield self.make_comment_request(city_id, city_en, 1)

    def parse_city_rank(self, response):
        lis = response.xpath('//ul[@class="plcCitylist"]/li')
        for li in lis:
            item = QyerCityItem()
            item['country'] = response.meta['country']
            item['city'] = li.xpath('.//h3/a/text()').get().strip()
            item['city_en'] = li.xpath('.//h3/a/span[@class="en"]/text()').get().replace(' ', '-').lower()
            item['peopleNum'] = li.xpath('.//p[@class="beento"]/text()').get()

            hot_spots = li.xpath('.//p[@class="pois"]/a/text()').getall()
            item['hotSpot'] = '|'.join([h.strip() for h in hot_spots])

            item['cityDetail'] = li.xpath('.//h3/a/@href').get()
            item['imgUrl'] = li.xpath('.//p[@class="pics"]/a/img/@src').get()
            yield item

    def make_comment_request(self, city_id, city_en, page):

        url = "https://place.qyer.com/impress.php?"
        formdata = {
            "action": "cityImpress",
            "type_name": "city",
            "parent_id": str(city_id),
            "page": str(page),
            "order": "datetime",
        }
        return scrapy.FormRequest(
            url=url,
            formdata=formdata,
            callback=self.parse_comment,
            meta={'city_id': city_id, 'city_en': city_en, 'page': page},
            headers={'Referer': f'https://place.qyer.com/{city_en}/review/'}
        )

    def parse_comment(self, response):
        """解析评论JSON"""
        try:
            data = json.loads(response.text)
            if data.get('result') == 'ok':
                json_data = data.get('data', {}).get('data', {})
                comment_list = json_data.get('list', [])
                total = int(json_data.get('total', 0))

                for c in comment_list:
                    item = QyerCommentItem()
                    item['cityEn'] = response.meta['city_en']
                    item['userName'] = c.get('username')
                    item['comment'] = c.get('comment')
                    # 时间戳转换
                    ts = int(c.get('datetime'))
                    item['commentTime'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
                    item['praiseNum'] = c.get('useful')
                    yield item

                # 翻页逻辑
                current_page = response.meta['page']
                if current_page == 1:
                    pages = int(total / 20)
                    if total % 20 > 0:
                        pages += 1
                    for p in range(2, pages + 1):
                        yield self.make_comment_request(response.meta['city_id'], response.meta['city_en'], p)
        except Exception as e:
            self.logger.error(f"Error parsing comment: {e}")