#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据马蜂窝评论数据，生成：
1）scenic_word_cloud.csv
2）scenic_aspect_analysis.csv
用于导入 MySQL 的 scenic_word_cloud 和 scenic_aspect_analysis 两张表
"""

import pandas as pd
import jieba
from snownlp import SnowNLP
from collections import Counter
import pymysql
from datetime import date

COMMENTS_TSV = "/home/tian/bigdata/travel/data/clean/mfw_comment_clean_for_hbase.tsv"

OUTPUT_WORD_CLOUD_CSV = "/home/tian/bigdata/travel/data/clean/scenic_word_cloud.csv"
OUTPUT_ASPECT_CSV = "/home/tian/bigdata/travel/data/clean/scenic_aspect_analysis.csv"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "waxyf2022",
    "database": "travel_db",
    "charset": "utf8mb4"
}

STOPWORDS = set(["的", "了", "和", "是", "就", "都", "而", "及", "与", "着",
                 "啊", "呢", "吧", "嘛", "也", "很", "还", "在", "有"])

# 六个维度对应的关键词（可以根据效果再微调/扩展）
ASPECT_DICT = {
    '食': ['吃', '美食', '餐厅', '饭店', '小吃', '餐饮', '早餐', '午餐', '晚餐', '餐馆', '酒楼'],
    '住': ['酒店', '住宿', '民宿', '客栈', '房间', '入住', '床', '卫生', '前台', '旅馆'],
    '行': ['交通', '地铁', '公交', '巴士', '自驾', '停车', '路上', '车程', '走路', '距离'],
    '游': ['景色', '风景', '排队', '项目', '游玩', '游乐', '体验', '游览', '门票', '设施', '表演'],
    '购': ['购物', '商店', '纪念品', '特产', '小摊', '专卖', '免税店', '价格', '买东西'],
    '娱': ['娱乐', '演出', '玩', '项目', '节目', '乐园', '过山车', '摩天轮', '烟花']
}


def load_scenic_mapping():
    """
    从 scenic_spot 表里读取 id 和 scenic_name，构造一个
    {scenic_name: scenic_id} 的映射
    """
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        df = pd.read_sql("SELECT id, scenic_name FROM scenic_spot", conn)
    finally:
        conn.close()
    mapping = dict(zip(df["scenic_name"], df["id"]))
    return mapping


def load_comments():
    """
    从 TSV 里加载评论数据。
    目前 mfw_comment_clean_for_hbase.tsv 的列顺序是：
    rowkey, scenic_name, comment_time, year, month, day, star, comment
    """
    col_names = [
        'rowkey', 'scenic_name', 'comment_time',
        'year', 'month', 'day', 'star', 'comment'
    ]
    df = pd.read_csv(
        COMMENTS_TSV,
        sep='\t',
        header=None,
        names=col_names,
        dtype=str
    )
    return df


def analyze_and_export():
    scenic_map = load_scenic_mapping()
    print(f"从 scenic_spot 读取到 {len(scenic_map)} 个景点映射")

    df = load_comments()
    print(f"从评论文件读取到 {len(df)} 条原始评论")

    # scenic_name -> scenic_id
    df["scenic_id"] = df["scenic_name"].map(scenic_map)

    # 过滤掉没有映射上的景点（比如 scenic_spot 里暂时没有的）
    before_drop = len(df)
    df = df.dropna(subset=["scenic_id"])
    df["scenic_id"] = df["scenic_id"].astype(int)
    print(f"成功匹配 scenic_id 的评论：{len(df)} 条（丢弃 {before_drop - len(df)} 条）")

    # 词云统计：(scenic_id, word) -> freq + 情感
    word_stats = {}          # key: (sid, word) -> {"freq", "sent_sum", "sent_cnt"}
    # 维度统计：(scenic_id, aspect) -> score_sum(1~5) + cnt
    aspect_stats = {}        # key: (sid, aspect) -> {"score_sum", "cnt"}
    # 维度下的关键词统计：(scenic_id, aspect) -> Counter
    aspect_word_stats = {}   # key: (sid, aspect) -> Counter()

    today_str = date.today().strftime("%Y-%m-%d")

    for idx, row in df.iterrows():
        scenic_id = row["scenic_id"]
        comment = row["comment"]

        if not isinstance(comment, str) or not comment.strip():
            continue

        # 情感分析：SnowNLP.sentiments ∈ [0,1]，越大越正面
        try:
            s = SnowNLP(comment)
            sent = float(s.sentiments)
        except Exception:
            sent = 0.5  # 出错时给个中性分

        # 映射到 1~5 分，方便写入 scenic_aspect_analysis.score
        score_1_5 = 1.0 + 4.0 * sent

        # 分词+简单去停用词
        tokens = [
            w.strip() for w in jieba.lcut(comment)
            if len(w.strip()) > 1 and w.strip() not in STOPWORDS
        ]
        if not tokens:
            continue

        # 当前评论里的词频
        token_counter = Counter(tokens)

        # ===== 1）更新 scenic_word_cloud 的统计 =====
        for word, cnt in token_counter.items():
            key = (scenic_id, word)
            stat = word_stats.setdefault(
                key, {"freq": 0, "sent_sum": 0.0, "sent_cnt": 0}
            )
            stat["freq"] += cnt
            stat["sent_sum"] += sent * cnt
            stat["sent_cnt"] += cnt

        # ===== 2）更新 scenic_aspect_analysis 的统计 =====
        # 简单规则：只要评论文本里包含任一该维度关键词，就认为命中该维度
        for aspect, kw_list in ASPECT_DICT.items():
            if any(kw in comment for kw in kw_list):
                akey = (scenic_id, aspect)
                st = aspect_stats.setdefault(akey, {"score_sum": 0.0, "cnt": 0})
                st["score_sum"] += score_1_5
                st["cnt"] += 1

                aw = aspect_word_stats.setdefault(akey, Counter())
                aw.update(token_counter)

    # ===== 导出 scenic_word_cloud.csv =====
    rows_wc = []
    for (sid, word), stat in word_stats.items():
        if stat["sent_cnt"] > 0:
            avg_sent = stat["sent_sum"] / stat["sent_cnt"]
        else:
            avg_sent = 0.5

        # 情感标签：>0.55 正向，<0.45 负向，其余中性（可自行调整阈值）
        if avg_sent > 0.55:
            sent_label = 1
        elif avg_sent < 0.45:
            sent_label = -1
        else:
            sent_label = 0

        rows_wc.append({
            "scenic_id": int(sid),
            "word": word,
            "frequency": int(stat["freq"]),
            "sentiment": int(sent_label),
            "create_time": today_str
        })

    df_wc = pd.DataFrame(rows_wc)
    df_wc.to_csv(OUTPUT_WORD_CLOUD_CSV, index=False, encoding="utf-8-sig")
    print(f"已生成词云 CSV：{OUTPUT_WORD_CLOUD_CSV}，共 {len(df_wc)} 行")

    # ===== 导出 scenic_aspect_analysis.csv =====
    rows_aspect = []
    for (sid, aspect), st in aspect_stats.items():
        if st["cnt"] == 0:
            continue
        avg_score = round(st["score_sum"] / st["cnt"], 2)
        wc = aspect_word_stats.get((sid, aspect), Counter())
        top_keywords = [w for w, _ in wc.most_common(5)]
        keywords_str = "、".join(top_keywords)

        rows_aspect.append({
            "scenic_id": int(sid),
            "aspect_name": aspect,
            "score": avg_score,
            "keywords": keywords_str
        })

    df_aspect = pd.DataFrame(rows_aspect)
    df_aspect.to_csv(OUTPUT_ASPECT_CSV, index=False, encoding="utf-8-sig")
    print(f"已生成维度分析 CSV：{OUTPUT_ASPECT_CSV}，共 {len(df_aspect)} 行")


if __name__ == "__main__":
    analyze_and_export()
