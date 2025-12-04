#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据 Mafengwo 评论明细，生成：
1) scenic_list.csv             景点ID映射表（方便建景点维表）
2) scenic_aspect_analysis.csv  对应 scenic_aspect_analysis 表
3) scenic_word_cloud.csv       对应 scenic_word_cloud 表
"""

import os
import csv
import datetime
from collections import defaultdict, Counter

import pandas as pd
import jieba
from snownlp import SnowNLP

# ====== 路径配置 ======
BASE_DIR = "/home/tian/bigdata/travel"
INPUT_CSV = os.path.join(BASE_DIR, "data", "clean", "mfw_comment_clean_for_mysql.csv")
OUT_DIR = os.path.join(BASE_DIR, "data", "analysis")

os.makedirs(OUT_DIR, exist_ok=True)

SCENIC_LIST_CSV = os.path.join(OUT_DIR, "scenic_list.csv")
ASPECT_OUT_CSV = os.path.join(OUT_DIR, "scenic_aspect_analysis.csv")
WORD_CLOUD_OUT_CSV = os.path.join(OUT_DIR, "scenic_word_cloud.csv")

# ====== 六要素手工词典 ======
ASPECT_DICT = {
    "食": ["吃", "餐厅", "美食", "早餐", "午餐", "晚餐", "餐饮", "饭店", "菜", "口味", "味道", "小吃", "餐馆", "自助餐"],
    "住": ["酒店", "宾馆", "住宿", "客栈", "房间", "床", "前台", "退房", "入住", "民宿", "卫生", "干净"],
    "行": ["地铁", "公交", "交通", "车", "路线", "导航", "高速", "大巴", "火车", "机场", "打车", "步行", "堵车", "停车"],
    "游": ["景色", "风景", "风光", "拍照", "游玩", "玩", "项目", "缆车", "表演", "体验", "景点", "观光", "游览"],
    "购": ["购物", "买", "纪念品", "特产", "商店", "超市", "小店", "价格", "贵", "便宜", "砍价", "礼物"],
    "娱": ["演出", "音乐", "夜景", "烟花", "酒吧", "KTV", "娱乐", "游戏", "夜市", "表演"]
}

# ====== 停用词 ======
DEFAULT_STOPWORDS = {
    "的", "了", "和", "是", "在", "就", "也", "都", "很", "小", "大", "非常",
    "一个", "我们", "他们", "然后", "而且", "但是", "如果", "因为", "所以",
    "这边", "那边", "这里", "那里", "感觉", "真的", "有点", "比较", "还是"
}

STOPWORDS_FILE = os.path.join(BASE_DIR, "data", "stopwords.txt")


def load_stopwords():
    stopwords = set(DEFAULT_STOPWORDS)
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    stopwords.add(w)
    return stopwords


# ====== 主流程 ======
def main():
    # 1. 读取清洗好的评论数据
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"找不到输入文件: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    if "scenic_name" not in df.columns or "comment" not in df.columns:
        raise ValueError("输入 CSV 需要至少包含 scenic_name 和 comment 两列，请检查列名。")

    # 去掉缺失
    df = df.dropna(subset=["scenic_name", "comment"])

    # 2. 为每个景点分配 scenic_id，并输出 scenic_list.csv（方便你建立景点维度表）
    scenic_names = sorted(df["scenic_name"].dropna().unique())
    scenic_id_map = {name: i + 1 for i, name in enumerate(scenic_names)}

    with open(SCENIC_LIST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["scenic_id", "scenic_name"])
        for name in scenic_names:
            writer.writerow([scenic_id_map[name], name])

    print(f"已生成景点映射表: {SCENIC_LIST_CSV}，共 {len(scenic_names)} 个景点。")

    # 3. 预备数据结构
    stopwords = load_stopwords()
    today_str = datetime.date.today().isoformat()

    # (scenic_id, aspect) -> list of sentiment score (0~1)
    aspect_sentiments = defaultdict(list)
    # (scenic_id, aspect) -> Counter(words)
    aspect_keywords = defaultdict(Counter)

    # scenic_id -> Counter(words)
    word_cloud_counter = defaultdict(Counter)
    # (scenic_id, word) -> list of sentiment scores
    word_sentiment_scores = defaultdict(list)

    # 4. 遍历每条评论做：分词 + 情感分析 + 六要素标注
    for _, row in df.iterrows():
        scenic_name = str(row["scenic_name"])
        comment = str(row["comment"])
        if not comment.strip():
            continue

        scenic_id = scenic_id_map.get(scenic_name)
        if scenic_id is None:
            continue

        # 情感打分（0~1，越大越正向）
        try:
            s = SnowNLP(comment)
            senti = float(s.sentiments)
        except Exception:
            # SnowNLP 偶尔会出错，直接跳过这条
            continue

        # 分词 + 去停用词 + 去掉单字
        words = [
            w.strip()
            for w in jieba.lcut(comment)
            if w.strip() and (w not in stopwords) and len(w.strip()) > 1
        ]

        if not words:
            continue

        # 更新词频（不区分一条评论内的重复词）
        word_cloud_counter[scenic_id].update(words)

        # 更新单词层面的情感
        for w in set(words):
            word_sentiment_scores[(scenic_id, w)].append(senti)

        # 判断该评论涉及到哪些六要素（按文本中是否包含关键词来粗略匹配）
        aspects_in_comment = set()
        for aspect, kws in ASPECT_DICT.items():
            if any(kw in comment for kw in kws):
                aspects_in_comment.add(aspect)

        # 更新维度评分和关键词
        for aspect in aspects_in_comment:
            aspect_sentiments[(scenic_id, aspect)].append(senti)
            aspect_keywords[(scenic_id, aspect)].update(words)

    # 5. 生成 scenic_aspect_analysis.csv
    aspect_rows = []
    aspect_id = 1

    for (scenic_id, aspect_name), scores in aspect_sentiments.items():
        if not scores:
            continue

        avg_senti = sum(scores) / len(scores)  # 0~1
        # 映射到 1~5 星（你也可以改成直接 0~1）
        score = avg_senti * 5.0
        if score < 0:
            score = 0
        if score > 5:
            score = 5

        # 取该景点该维度下的高频关键词（前10个）
        kw_counter = aspect_keywords[(scenic_id, aspect_name)]
        top_keywords = [w for w, _ in kw_counter.most_common(10)]
        keywords_str = "、".join(top_keywords)

        aspect_rows.append([
            aspect_id,
            scenic_id,
            aspect_name,
            round(score, 2),
            keywords_str
        ])
        aspect_id += 1

    with open(ASPECT_OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "scenic_id", "aspect_name", "score", "keywords"])
        writer.writerows(aspect_rows)

    print(f"已生成维度情感分析 CSV: {ASPECT_OUT_CSV}，共 {len(aspect_rows)} 行。")

    # 6. 生成 scenic_word_cloud.csv
    word_rows = []
    word_id = 1

    for scenic_id, counter in word_cloud_counter.items():
        for word, freq in counter.items():
            scores = word_sentiment_scores.get((scenic_id, word), [])
            if scores:
                avg = sum(scores) / len(scores)
            else:
                avg = 0.5  # 默认中性

            # 映射到 -1 / 0 / 1
            if avg >= 0.6:
                sentiment = 1
            elif avg <= 0.4:
                sentiment = -1
            else:
                sentiment = 0

            word_rows.append([
                word_id,
                scenic_id,
                word,
                int(freq),
                int(sentiment),
                today_str
            ])
            word_id += 1

    with open(WORD_CLOUD_OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "scenic_id", "word", "frequency", "sentiment", "create_time"])
        writer.writerows(word_rows)

    print(f"已生成词云 CSV: {WORD_CLOUD_OUT_CSV}，共 {len(word_rows)} 行。")


if __name__ == "__main__":
    main()
