import scrapy
import re
import json
from tourism_data.items import MafengwoCommentItem


class MafengwoSpider(scrapy.Spider):
    name = 'mafengwo'
    allowed_domains = ['mafengwo.cn']

    # 原脚本中的景点POI配置
    scenicSpot_poi_dict = {
        '香港海洋公园': 488, '星光大道': 483, '维多利亚港': 484,
        '太平山': 518, '尖沙咀': 12261, '金紫荆广场': 12259,
        '香港迪士尼乐园': 520, '旺角': 528, '黄鹤楼': 5426285,
        '湖北省博物馆': 6221,
    }

    api_url = 'http://pagelet.mafengwo.cn/poi/pagelet/poiCommentListApi?'

    def start_requests(self):
        for name, poi in self.scenicSpot_poi_dict.items():
            # 原脚本 range(1, 5)
            for page in range(1, 20):
                # 构造 GET 参数，原脚本写法
                params = {
                    'params': '{"poi_id":"%d","page":"%d","just_comment":1}' % (poi, page)
                }
                # 构造 URL
                url = f"{self.api_url}params={params['params']}"

                yield scrapy.Request(
                    url=url,
                    headers={
                        'Referer': f'http://www.mafengwo.cn/poi/{poi}.html',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
                    },
                    callback=self.parse,
                    meta={'scenicSpot': name}
                )

    def parse(self, response):

        html = response.text.encode().decode('unicode-escape').encode('utf-8', 'ignore').decode('utf-8')
        html = html.replace('\\/', '/').replace("<br />", "").replace(" ", "").replace("\n", "").replace("\r", "")

        date_pattern = r'<aclass="btn-comment_j_comment"title="添加评论">评论</a><spanclass="time">(.*?)</span>'
        star_pattern = r'<spanclass="s-stars-star(\d)"></span>'
        comment_pattern = r'<pclass="rev-txt">(.*?)</p>'

        dates = re.compile(date_pattern).findall(html)
        stars = re.compile(star_pattern).findall(html)
        comments = re.compile(comment_pattern).findall(html)

        for i in range(len(dates)):
            item = MafengwoCommentItem()
            item['scenicSpot'] = response.meta['scenicSpot']
            item['date'] = dates[i]
            item['star'] = stars[i]
            item['comment'] = comments[i]
            yield item