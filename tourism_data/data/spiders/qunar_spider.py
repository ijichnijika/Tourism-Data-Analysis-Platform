import scrapy
from tourism_data.items import QunarScenicItem


class QunarSpider(scrapy.Spider):
    name = 'qunar'
    allowed_domains = ['qunar.com']

    city_url_dict = {
        '香港': 'p-cs300027-xianggang', '澳门': 'p-cs300028-aomen',
        '台北': 'p-cs300002-taibei', '北京': 'p-cs299914-beijing',
        '上海': 'p-cs299878-shanghai', '成都': 'p-cs300085-chengdu',
        '广州': 'p-cs300132-guangzhou'
    }

    raw_cookies = 'QN1=dXrgj14+tmYQhFxKE9ekAg==; QN205=organic; QN277=organic; QN269=506F28C14A7611EAA0BEFA163E244083; _i=RBTKSRDqFhTQT5KRlx-P1H78agxx; fid=7cc3c3d9-3f6c-45e1-8cef-3384cd5da577; Hm_lvt_c56a2b5278263aa647778d304009eafc=1581168271,1581220912; viewpoi=7564992|709275; viewdist=299878-7; uld=1-299878-8-1581221233|1-1062172-1-1581168529; QN267=1679639433d5aedfc8; Hm_lpvt_c56a2b5278263aa647778d304009eafc=1581221236; QN25=cb06bfbd-d687-4072-98c5-73266b637a6a-9f992f90; QN42=nvxp8441; _q=U.qunar_lbs_428305502; _t=26463150; csrfToken=oXYBnhSoGAGxggRkzmAjbxxGrpgsjUqQ; _s=s_ZBWFJO3EEGZISWS35EBIS5NQYA; _v=YTRjW_H5L47nGNVabvTLt1mlh7j8R7t4UNDVRrJUz0wScfLMWgSvkwQbzMLHlFbsvTU-2kJrBK74NUyOi3MX_3obY94Hhhugt8bv8ILxwsWDv4s_ANNiM8qRdg6HlBrrCEnGYr8lxS9uv78zDCNKz9pFbN8JPYy-AKJP6xILIsT7; _vi=4ONQzvfOOhwJECN5R-4rfWZDzlQ5-qv2xi_jsp1INPEpy9iKHa5gV0gHc35fDfTDe3TjcKteU7ZWk1vd6MsIqTfXYyUh3gTwZJ_9z3PEpkXZReeeIjaVE4HwLTkOATLIzIxg92s-QCWKE1RdNlaZsxPnfN7NHPGAZz5rsmxvpNDY; QN44=qunar_lbs_428305502; QN48=tc_a7fe4861b2d918df_17028369fc8_67ab; QN271=1749d44a-1a11-4886-be27-c3e3bfdadb0c'


    def start_requests(self):
        # 解析 Cookies
        cookies = {}
        cookie_str = 'QN1=dXrgj14+tmYQhFxKE9ekAg==; QN205=organic; QN277=organic; QN269=506F28C14A7611EAA0BEFA163E244083; _i=RBTKSRDqFhTQT5KRlx-P1H78agxx; fid=7cc3c3d9-3f6c-45e1-8cef-3384cd5da577; Hm_lvt_c56a2b5278263aa647778d304009eafc=1581168271,1581220912; viewpoi=7564992|709275; viewdist=299878-7; uld=1-299878-8-1581221233|1-1062172-1-1581168529; QN267=1679639433d5aedfc8; Hm_lpvt_c56a2b5278263aa647778d304009eafc=1581221236; QN25=cb06bfbd-d687-4072-98c5-73266b637a6a-9f992f90; QN42=nvxp8441; _q=U.qunar_lbs_428305502; _t=26463150; csrfToken=oXYBnhSoGAGxggRkzmAjbxxGrpgsjUqQ; _s=s_ZBWFJO3EEGZISWS35EBIS5NQYA; _v=YTRjW_H5L47nGNVabvTLt1mlh7j8R7t4UNDVRrJUz0wScfLMWgSvkwQbzMLHlFbsvTU-2kJrBK74NUyOi3MX_3obY94Hhhugt8bv8ILxwsWDv4s_ANNiM8qRdg6HlBrrCEnGYr8lxS9uv78zDCNKz9pFbN8JPYy-AKJP6xILIsT7; _vi=4ONQzvfOOhwJECN5R-4rfWZDzlQ5-qv2xi_jsp1INPEpy9iKHa5gV0gHc35fDfTDe3TjcKteU7ZWk1vd6MsIqTfXYyUh3gTwZJ_9z3PEpkXZReeeIjaVE4HwLTkOATLIzIxg92s-QCWKE1RdNlaZsxPnfN7NHPGAZz5rsmxvpNDY; QN44=qunar_lbs_428305502; QN48=tc_a7fe4861b2d918df_17028369fc8_67ab; QN271=1749d44a-1a11-4886-be27-c3e3bfdadb0c'
        for line in cookie_str.split('; '):
            if '=' in line:
                name, value = line.split('=', 1)
                cookies[name] = value

        for city, code in self.city_url_dict.items():
            for i in range(1, 30):
                url = f"https://travel.qunar.com/{code}-jingdian-1-{i}"
                yield scrapy.Request(
                    url=url,
                    cookies=cookies,
                    callback=self.parse,
                    meta={'city': city}
                )

    def parse(self, response):
        lis = response.css('ul.list_item.clrfix > li')
        for li in lis:
            item = QunarScenicItem()
            item['city'] = response.meta['city']
            item['spot_name'] = li.css('span.cn_tit::text').get()
            item['strategy_sum'] = li.css('div.strategy_sum::text').get()
            item['star'] = li.css('span.total_star span::attr(style)').get()  # style="width: 100%"
            item['intro'] = li.css('div.desbox::text').get()
            item['rank'] = li.css('span.ranking_sum::text').get()
            item['lng'] = li.attrib.get('data-lng')
            item['lat'] = li.attrib.get('data-lat')
            item['comment_sum'] = li.css('div.comment_sum::text').get()
            item['visitors'] = li.css('span.comment_sum span::text').get()
            yield item