# -*- coding: utf-8 -*-
"""
spark_analyze_to_mysql.py

使用 Spark 对马蜂窝旅行评论做文本分析，生成用于 MySQL 的 CSV 数据：
- scenic_dim：景点维度表
- scenic_word_cloud：景点词云表
- scenic_aspect_analysis：景点六要素（食住行游购娱）分析表

运行方式（在 /home/tian/bigdata/travel 下）：
  spark-submit --master local[2] scripts/spark_analyze_to_mysql.py
"""
from __future__ import annotations

import os
import re
import shutil
from typing import List

import jieba
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    TimestampType,
    ArrayType,
)
from pyspark.sql.window import Window


# 当前脚本所在目录：/home/tian/bigdata/travel/scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录：/home/tian/bigdata/travel
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# 清洗后的 TSV（本地）
CLEAN_TSV_LOCAL = os.path.join(BASE_DIR, "data", "clean", "mfw_comment_clean_for_hbase.tsv")
# MySQL 导出 CSV 目录（本地）
MYSQL_OUT_DIR = os.path.join(BASE_DIR, "data", "mysql")


# ---------------------
# 小工具：将 Spark 写出的 part-*.csv 移动/重命名成单一 CSV
# ---------------------
def _move_single_part_to_csv(part_dir: str, out_dir: str, filename: str) -> str:
    """
    将 part-*.csv 移动为 out_dir/filename，返回最终文件路径。
    part_dir: Spark 写出的 csv 目录（里面有 part-0000*.csv）
    out_dir:  目标目录（/home/tian/bigdata/travel/data/mysql）
    filename: 目标文件名，如 scenic_dim.csv
    """
    if not os.path.isdir(part_dir):
        print(f"[WARN] 目录不存在，无法移动 CSV：{part_dir}")
        return ""

    part_files = [f for f in os.listdir(part_dir) if f.startswith("part-") and f.endswith(".csv")]
    if not part_files:
        print(f"[WARN] 在目录中未找到 part-*.csv：{part_dir}")
        return ""

    src_path = os.path.join(part_dir, part_files[0])
    os.makedirs(out_dir, exist_ok=True)
    dst_path = os.path.join(out_dir, filename)

    # 如果已存在同名文件，先删掉
    if os.path.exists(dst_path):
        os.remove(dst_path)

    shutil.move(src_path, dst_path)
    print(f"[OK] 已生成 CSV 文件：{dst_path}")
    return dst_path


# ---------------------
# 文本处理：分词 & 六要素匹配
# ---------------------

# 简单停用词
STOPWORDS = set([
    "的", "了", "和", "是", "在", "也", "就", "都", "很", "啊", "嘛", "呢", "吧", "着",
    "我们", "他们", "你们", "然后", "还有", "但是", "因为", "所以", "如果",
])

def cut_words(text: str) -> List[str]:
    if text is None:
        return []
    text = text.strip()
    if not text:
        return []
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    words = []
    for w in jieba.lcut(text):
        w = w.strip()
        if not w:
            continue
        if w in STOPWORDS:
            continue
        # 过滤纯数字、长度为 1 的无意义词
        if re.fullmatch(r"\d+", w):
            continue
        if len(w) == 1:
            continue
        words.append(w)
    return words


cut_words_udf = F.udf(cut_words, ArrayType(StringType()))

# 六要素关键词字典
ASPECT_KEYWORDS = {
    "食": [
        "吃", "餐厅", "美食", "饭店", "早餐", "午餐", "晚餐", "餐饮", "味道", "菜",
        "餐馆", "小吃", "好吃", "难吃", "口味", "餐厅", "排队吃",
    ],
    "住": [
        "酒店", "宾馆", "住宿", "房间", "床", "入住", "退房", "卫生", "干净",
        "环境", "噪音", "前台", "服务员", "旅馆",
    ],
    "行": [
        "交通", "地铁", "公交", "大巴", "车", "路线", "自驾", "堵车", "路",
        "远", "近", "走路", "步行", "上山", "下山", "索道", "缆车",
    ],
    "游": [
        "景色", "风景", "游玩", "项目", "表演", "排队", "门票", "游乐",
        "体验", "拍照", "游览", "景点", "玩", "景区", "导游",
    ],
    "购": [
        "购物", "纪念品", "特产", "商店", "超市", "买", "卖", "礼物",
        "小摊", "价格", "贵", "便宜", "商场",
    ],
    "娱": [
        "娱乐", "节目", "活动", "玩乐", "夜景", "烟花", "音乐", "歌舞",
        "酒吧", "演出", "表演", "节日",
    ],
}

def detect_aspects(text: str) -> List[str]:
    """根据关键词粗略判断一条评论涉及哪些旅游六要素。"""
    if text is None:
        return []
    aspects = set()
    for aspect, kws in ASPECT_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                aspects.add(aspect)
                break
    return list(aspects)


detect_aspects_udf = F.udf(detect_aspects, ArrayType(StringType()))


def main():
    print("===== 旅行评论 -> MySQL 分析脚本启动 =====")
    print("项目根目录:", BASE_DIR)
    print("清洗后 TSV 本地路径:", CLEAN_TSV_LOCAL)
    print("MySQL 输出目录:", MYSQL_OUT_DIR)

    if not os.path.exists(CLEAN_TSV_LOCAL):
        raise FileNotFoundError(f"本地 TSV 不存在，请先执行清洗脚本：{CLEAN_TSV_LOCAL}")

    os.makedirs(MYSQL_OUT_DIR, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("TravelCommentToMySQL")
        # master 由 spark-submit --master local[2] 决定，这里不显式设置
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
        .getOrCreate()
    )

    # ---------------------
    # 1. 读取 TSV 数据（本地 file://）
    # ---------------------
    print(">>> 1) 读取清洗后的 TSV 数据 ...")

    schema = StructType([
        StructField("rowkey",      StringType(), True),
        StructField("scenic_name", StringType(), True),
        StructField("comment_time",StringType(), True),
        StructField("year",        StringType(), True),
        StructField("month",       StringType(), True),
        StructField("day",         StringType(), True),
        StructField("star",        StringType(), True),  # 先按字符串读，后面再转 int
        StructField("comment",     StringType(), True),
    ])

    df = (
        spark.read.format("csv")
        .option("sep", "\t")
        .option("header", "false")
        .schema(schema)
        .load("file://" + CLEAN_TSV_LOCAL)
    )

    # 基本清洗：转类型 + 过滤
    df = (
        df.withColumn("star_int", F.col("star").cast(IntegerType()))
          .withColumn("comment_time_ts", F.to_timestamp("comment_time", "yyyy-MM-dd HH:mm:ss"))
    )

    df = df.filter(
        (F.col("scenic_name").isNotNull()) & (F.col("scenic_name") != "") &
        (F.col("comment").isNotNull()) & (F.col("comment") != "") &
        F.col("star_int").isNotNull()
    )

    total_rows = df.count()
    print(f"总评论条数（过滤后）: {total_rows}")

    # 为后续简单情感打标签：星级 >=4 为正向，<=2 为负向，其余中性
    df = df.withColumn(
        "comment_sentiment",
        F.when(F.col("star_int") >= 4, F.lit(1))
         .when(F.col("star_int") <= 2, F.lit(-1))
         .otherwise(F.lit(0))
    )

    # ---------------------
    # 2. 构建景点维度 scenic_dim（含 scenic_id）
    # ---------------------
    print(">>> 2) 构建 scenic_dim 维度表 ...")

    scenic_dim = (
        df.groupBy("scenic_name")
          .agg(
              F.count("*").alias("comment_count"),
              F.round(F.avg("star_int"), 2).alias("avg_star"),
              F.min("comment_time_ts").alias("first_comment_time"),
              F.max("comment_time_ts").alias("last_comment_time"),
          )
    )

    w_scenic = Window.orderBy("scenic_name")
    scenic_dim = scenic_dim.withColumn("scenic_id", F.row_number().over(w_scenic))

    # 调整列顺序
    scenic_dim = scenic_dim.select(
        "scenic_id",
        "scenic_name",
        "comment_count",
        "avg_star",
        "first_comment_time",
        "last_comment_time",
    )

    scenic_dim.show(5, truncate=False)

    # 与原始 df 关联 scenic_id
    df_with_id = df.join(
        scenic_dim.select("scenic_id", "scenic_name"),
        on="scenic_name",
        how="left",
    )

    # ---------------------
    # 3. 生成景点词云 scenic_word_cloud
    # ---------------------
    print(">>> 3) 生成景点词云 scenic_word_cloud ...")

    df_words = (
        df_with_id
        .select("scenic_id", "comment", "comment_sentiment")
        .withColumn("words", cut_words_udf("comment"))
        .withColumn("word", F.explode("words"))
        .filter(F.col("word") != "")
    )

    word_agg = (
        df_words.groupBy("scenic_id", "word")
        .agg(
            F.count("*").alias("frequency"),
            F.sum("comment_sentiment").alias("sentiment_sum"),
        )
    )

    word_agg = word_agg.withColumn(
        "sentiment",
        F.when(F.col("sentiment_sum") > 0, F.lit(1))
         .when(F.col("sentiment_sum") < 0, F.lit(-1))
         .otherwise(F.lit(0))
    )

    word_cloud = (
        word_agg
        .select(
            "scenic_id",
            "word",
            "frequency",
            "sentiment",
        )
        .withColumn("create_time", F.current_date())
    )

    # ---------------------
    # 4. 生成六要素景点分析 scenic_aspect_analysis
    # ---------------------
    print(">>> 4) 生成六要素分析 scenic_aspect_analysis ...")

    df_aspect = (
        df_with_id
        .select("scenic_id", "star_int", "comment")
        .withColumn("aspects", detect_aspects_udf("comment"))
        .withColumn("aspect_name", F.explode("aspects"))
        .filter(F.col("aspect_name").isNotNull())
    )

    if df_aspect.rdd.isEmpty():
        print("[WARN] 未检测到任何六要素标签（食/住/行/游/购/娱），scenic_aspect_analysis 将为空表。")
        aspect_score = spark.createDataFrame([], schema="scenic_id INT, aspect_name STRING, score DOUBLE, keywords STRING")
    else:
        # 1) 计算每个景点-要素的评分（这里简单用星级均值）
        aspect_score_base = (
            df_aspect.groupBy("scenic_id", "aspect_name")
            .agg(F.round(F.avg("star_int"), 2).alias("score"))
        )

        # 2) 为每个景点-要素提取典型关键词（对该要素下的评论再分词统计）
        df_aspect_words = (
            df_aspect
            .withColumn("words", cut_words_udf("comment"))
            .withColumn("word", F.explode("words"))
            .filter(F.col("word") != "")
        )

        word_freq_aspect = (
            df_aspect_words.groupBy("scenic_id", "aspect_name", "word")
            .agg(F.count("*").alias("freq"))
        )

        w_kw = Window.partitionBy("scenic_id", "aspect_name").orderBy(F.desc("freq"))
        top_words = (
            word_freq_aspect
            .withColumn("rn", F.row_number().over(w_kw))
            .filter(F.col("rn") <= 10)
        )

        keywords_by_aspect = (
            top_words.groupBy("scenic_id", "aspect_name")
            .agg(F.concat_ws(",", F.collect_list("word")).alias("keywords"))
        )

        aspect_score = (
            aspect_score_base.join(
                keywords_by_aspect,
                on=["scenic_id", "aspect_name"],
                how="left",
            )
        )

    # ---------------------
    # 5. 写出到本地 CSV（给 MySQL 导入）
    # ---------------------
    print(">>> 5) 写出 CSV 到 data/mysql ...")

    scenic_dim_dir = os.path.join(MYSQL_OUT_DIR, "scenic_dim_tmp")
    word_cloud_dir = os.path.join(MYSQL_OUT_DIR, "scenic_word_cloud_tmp")
    aspect_dir = os.path.join(MYSQL_OUT_DIR, "scenic_aspect_analysis_tmp")

    # 先清空旧目录
    for d in [scenic_dim_dir, word_cloud_dir, aspect_dir]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    scenic_dim.coalesce(1).write.mode("overwrite").option("header", "true").csv("file://" + scenic_dim_dir)
    word_cloud.coalesce(1).write.mode("overwrite").option("header", "true").csv("file://" + word_cloud_dir)
    aspect_score.coalesce(1).write.mode("overwrite").option("header", "true").csv("file://" + aspect_dir)

    scenic_dim_csv = _move_single_part_to_csv(scenic_dim_dir, MYSQL_OUT_DIR, "scenic_dim.csv")
    word_cloud_csv = _move_single_part_to_csv(word_cloud_dir, MYSQL_OUT_DIR, "scenic_word_cloud.csv")
    aspect_csv = _move_single_part_to_csv(aspect_dir, MYSQL_OUT_DIR, "scenic_aspect_analysis.csv")

    print("=== 导出完成 ===")
    print("scenic_dim      CSV:", scenic_dim_csv or "(无)")
    print("scenic_word_cloud CSV:", word_cloud_csv or "(无)")
    print("scenic_aspect_analysis CSV:", aspect_csv or "(无)")

    spark.stop()


if __name__ == "__main__":
    main()
