# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import csv
import os
# 注意这里导入的是 tourism_data.items，对应您的新项目名
from tourism_data.items import QyerCityItem, QyerCommentItem, MafengwoCommentItem, QunarScenicItem


class MultiCsvPipeline:
    def open_spider(self, spider):
        # 在爬虫启动时初始化文件字典
        self.files = {}
        self.writers = {}

    def process_item(self, item, spider):
        # 根据 Item 类型决定保存的文件名
        filename = 'data.csv'  # 默认文件名

        if isinstance(item, QyerCityItem):
            # 比如 qyer_city_rank_china.csv
            country = item.get('country', 'unknown')
            filename = f'qyer_city_rank_{country}.csv'
        elif isinstance(item, QyerCommentItem):
            filename = 'qyer_comments.csv'
        elif isinstance(item, MafengwoCommentItem):
            filename = 'mafengwo_comments.csv'
        elif isinstance(item, QunarScenicItem):
            filename = 'qunar_scenic.csv'
        else:
            return item  # 未知类型不处理

        # 懒加载文件句柄（第一次遇到该文件名时才打开文件）
        if filename not in self.files:
            # 如果文件不存在，需要写表头
            file_exists = os.path.exists(filename)
            # 使用 utf-8-sig 编码以防 Excel 打开乱码
            f = open(filename, 'a', newline='', encoding='utf-8-sig')
            writer = csv.DictWriter(f, fieldnames=item.keys())

            if not file_exists:
                writer.writeheader()

            self.files[filename] = f
            self.writers[filename] = writer

        # 写入数据
        self.writers[filename].writerow(item)
        return item

    def close_spider(self, spider):
        # 爬虫结束时关闭所有文件
        for f in self.files.values():
            f.close()