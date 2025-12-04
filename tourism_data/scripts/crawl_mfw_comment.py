#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
马蜂窝景点评论爬虫
输出: data/raw/mfw_comment_raw.csv
字段: 景点名称,日期列表,星级列表,评论列表
"""

import requests
import time
import random
import re
import os
from tqdm import trange

BASE_DIR = "/home/tian/bigdata/travel"
RAW_PATH = os.path.join(BASE_DIR, "data/raw/mfw_comment_raw.csv")
LOG_PATH = os.path.join(BASE_DIR, "logs/mfw_crawl.log")

# 多个 User-Agent，随机挑一个
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)

def get_page(scenic_spot: str, poi: int, max_page: int, f):
    """
    scenic_spot: 景点名称
    poi: mafengwo poi id
    max_page: 最多翻多少页（遇到空页会提前停止）
    f: 已经打开的 csv 文件句柄
    """
    comment_poi_url = "http://pagelet.mafengwo.cn/poi/pagelet/poiCommentListApi"

    session = requests.session()
    total_count = 0

    try:
        for num in trange(1, max_page + 1, desc=f"{scenic_spot}", ncols=80):
            headers = {
                "Referer": f"http://www.mafengwo.cn/poi/{poi}.html",
                "User-Agent": random.choice(UA_LIST),
            }

            params = {
                "params": f'{{"poi_id":"{poi}","page":"{num}","just_comment":1}}'
            }

            try:
                res = session.get(
                    url=comment_poi_url,
                    headers=headers,
                    params=params,
                    timeout=5,
                )
            except Exception as e:
                log(f"[WARN] 第 {num} 页请求异常: {e}")
                # 短暂休息后继续下一页
                time.sleep(random.uniform(0.3, 0.8))
                continue

            # 和你原始代码一样的解码逻辑
            page = (
                res.text.encode()
                .decode("unicode-escape")
                .encode("utf-8", "ignore")
                .decode("utf-8")
            )
            page = (
                page.replace("\\/", "/")
                .replace("<br />", "")
                .replace(" ", "")
                .replace("\n", "")
                .replace("\r", "")
            )

            # 正则和你给的保持一致（因为前面把空格都删了）
            date_pattern = r'<aclass="btn-comment_j_comment"title="添加评论">评论</a><spanclass="time">(.*?)</span>'
            star_pattern = r'<spanclass="s-stars-star(\d)"></span>'
            comment_pattern = r'<pclass="rev-txt">(.*?)</p>'

            json_dates = re.compile(date_pattern).findall(page)
            json_stars = re.compile(star_pattern).findall(page)
            json_comments = re.compile(comment_pattern).findall(page)

            if not json_dates or not json_comments:
                log(f"[INFO] {scenic_spot} 第 {num} 页已经没有评论，提前结束。")
                break

            # 三个列表长度以最短的为准，防止溢出
            n = min(len(json_dates), len(json_stars), len(json_comments))
            for i in range(n):
                json_date = json_dates[i]
                json_star = json_stars[i]
                json_comment = json_comments[i]

                # 去掉逗号，避免影响 csv
                json_comment = json_comment.replace(",", "，")

                seq = (scenic_spot, json_date, json_star, json_comment)
                f.write(",".join(seq) + "\n")
                total_count += 1

            # 随机访问间隔，模拟真人
            time.sleep(random.uniform(0.3, 1.0))

        log(f"[OK] {scenic_spot} 共采集 {total_count} 条评论。")
        return total_count

    except Exception as e:
        log(f"[ERROR] 获取 {scenic_spot} 评论失败: {e}")
        return total_count


if __name__ == "__main__":
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    # 景点字典
    scenicSpot_poi_dict = {
        "香港海洋公园": 488,
        "星光大道": 483,
        "维多利亚港": 484,
        "太平山": 518,
        "尖沙咀": 12261,
        "金紫荆广场": 12259,
        "香港迪士尼乐园": 520,
        "旺角": 528,
        "黄鹤楼": 5426285,
        "湖北省博物馆": 6221,

        "北京故宫": 10065,
        "八达岭长城": 10422,
        "西安兵马俑": 14703,
        "西安城墙": 14966,
        "上海外滩": 2759,
        "南京夫子庙": 10987,
        "广州塔": 10175,
        "杭州西湖": 10399,

    }

    total_all = 0
    with open(RAW_PATH, "w", encoding="utf-8") as name:
        print("开始写入文件".center(20, "-"))
        header = ("景点名称", "日期列表", "星级列表", "评论列表")
        name.write(",".join(header) + "\n")

        # 每个景点最多翻 500 页；如果没有那么多评论，会自动提前结束
        MAX_PAGE_PER_POI = 500

        for scenic, poi in scenicSpot_poi_dict.items():
            log(f"正在爬取景点 {scenic} (poi={poi}) 的评论 ...")
            cnt = get_page(scenic, poi, MAX_PAGE_PER_POI, name)
            total_all += cnt
            log(f"{scenic} 完成，本景点采集 {cnt} 条，累计采集 {total_all} 条。")
            # 每个景点之间稍微歇一下
            time.sleep(random.uniform(3.0, 6.0))

    log(f"全部景点爬取完成，总共采集 {total_all} 条评论。")
