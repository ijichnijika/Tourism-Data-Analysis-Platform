BOT_NAME = 'tourism_data'

SPIDER_MODULES = ['tourism_data.spiders']
NEWSPIDER_MODULE = 'tourism_data.spiders'
# 遵守robots.txt (建议False)
ROBOTSTXT_OBEY = False

# 下载延迟 (原脚本使用了随机延迟，Scrapy默认开启随机化)
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
}

# 开启Pipeline
ITEM_PIPELINES = {
   'tourism_data.pipelines.MultiCsvPipeline': 300,
}

# 编码
FEED_EXPORT_ENCODING = 'utf-8'