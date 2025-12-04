#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Spark 的马蜂窝旅游评论分析脚本

数据来源：/home/tian/bigdata/travel/data/clean/mfw_comment_clean_for_hbase.tsv
字段顺序：
  rowkey, scenic_name, comment_time, year, month, day, star, comment

分析内容：
  1）按景点统计评论数 & 平均星级（人气景点 TOP20）
  2）按年月统计整体评论数 & 平均星级（时间趋势）
  3）指定景点（香港海洋公园）的评分分布
  4）全局评分分布
  5）按“景点 + 月份”统计热度（TOP50）
输出结果写到本地目录：
  /home/tian/bigdata/travel/data/analysis/...
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    count,
    avg,
    round as _round,
    lpad,
    concat_ws,
    desc,
)

# 项目根目录 & 文件路径
BASE_DIR = "/home/tian/bigdata/travel"
LOCAL_TSV = os.path.join(BASE_DIR, "data/clean/mfw_comment_clean_for_hbase.tsv")
LOCAL_ANALYSIS_DIR = os.path.join(BASE_DIR, "data/analysis")


def main():
    print("===== 马蜂窝旅游评论 Spark 分析脚本启动 =====")
    print("数据源 TSV:", LOCAL_TSV)
    print("分析结果输出目录:", LOCAL_ANALYSIS_DIR)

    # 1. 检查数据源是否存在
    if not os.path.exists(LOCAL_TSV):
        raise RuntimeError(
            f"找不到 TSV 文件: {LOCAL_TSV} ，请先运行 spark_clean_travel.py 生成清洗结果。"
        )

    # 创建本地分析结果目录
    os.makedirs(LOCAL_ANALYSIS_DIR, exist_ok=True)

    # 2. 创建 SparkSession
    spark = (
        SparkSession.builder.appName("TravelCommentAnalysis").getOrCreate()
    )

    # 3. 读取清洗后的 TSV
    print(">>> 1. 读取清洗后的 TSV ...")
    df = (
        spark.read
        .option("delimiter", "\t")
        .option("header", "false")  # TSV 无表头
        .csv(f"file://{LOCAL_TSV}")
    )

    # 重命名列
    df = df.toDF(
        "rowkey",
        "scenic_name",
        "comment_time",
        "year",
        "month",
        "day",
        "star",
        "comment",
    )

    # 类型转换
    df = (
        df.withColumn("year", col("year").cast("int"))
          .withColumn("day", col("day").cast("int"))
          .withColumn("star", col("star").cast("int"))
    )

    df.cache()

    total_cnt = df.count()
    print(f"总行数: {total_cnt}")
    print("示例前 5 行：")
    df.show(5, truncate=False)

    # ========== 分析一：按景点统计人气 ==========
    print("\n>>> 2. 分析一：按景点统计评论数 & 平均星级（人气景点 TOP20）")

    df_top_scenic = (
        df.groupBy("scenic_name")
          .agg(
              count("*").alias("comment_cnt"),
              _round(avg("star"), 2).alias("avg_star"),
          )
          .orderBy(desc("comment_cnt"))
    )

    df_top_scenic.show(20, truncate=False)

    out1 = f"file://{os.path.join(LOCAL_ANALYSIS_DIR, 'top_scenic')}"
    (
        df_top_scenic.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(out1)
    )
    print("人气景点统计结果已写出到目录：", out1)

    # ========== 分析二：按年月的整体时间趋势 ==========
    print("\n>>> 3. 分析二：按年月统计整体评论数 & 平均星级（时间趋势）")

    df_ym = df.withColumn(
        "ym",
        concat_ws(
            "-",
            col("year").cast("string"),
            lpad(col("month"), 2, "0"),
        ),
    )

    df_trend = (
        df_ym.groupBy("ym")
             .agg(
                 count("*").alias("comment_cnt"),
                 _round(avg("star"), 2).alias("avg_star"),
             )
             .orderBy("ym")
    )

    df_trend.show(50, truncate=False)

    out2 = f"file://{os.path.join(LOCAL_ANALYSIS_DIR, 'trend_by_month')}"
    (
        df_trend.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(out2)
    )
    print("按月时间趋势结果已写出到目录：", out2)

    # ========== 分析三：指定景点的评分分布 ==========
    target_scenic = "香港海洋公园"
    print(f"\n>>> 4. 分析三：景点《{target_scenic}》的评分分布")

    df_star_dist_scenic = (
        df.filter(col("scenic_name") == target_scenic)
          .groupBy("star")
          .agg(count("*").alias("cnt"))
          .orderBy("star")
    )

    df_star_dist_scenic.show(10, truncate=False)

    out3 = f"file://{os.path.join(LOCAL_ANALYSIS_DIR, 'star_dist_hk_oceanpark')}"
    (
        df_star_dist_scenic.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(out3)
    )
    print("指定景点评分分布已写出到目录：", out3)

    # ========== 分析四：全局评分分布 ==========
    print("\n>>> 5. 分析四：全局评分分布")

    df_star_dist_all = (
        df.groupBy("star")
          .agg(count("*").alias("cnt"))
          .orderBy("star")
    )

    df_star_dist_all.show(10, truncate=False)

    out4 = f"file://{os.path.join(LOCAL_ANALYSIS_DIR, 'star_dist_overall')}"
    (
        df_star_dist_all.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(out4)
    )
    print("全局评分分布已写出到目录：", out4)

    # ========== 分析五：景点 + 月份 的热度（TOP50） ==========
    print("\n>>> 6. 分析五：按 景点+年月 统计评论数（热度 TOP50）")

    df_scenic_month = (
        df_ym.groupBy("scenic_name", "ym")
             .agg(
                 count("*").alias("comment_cnt"),
                 _round(avg("star"), 2).alias("avg_star"),
             )
             .orderBy(desc("comment_cnt"))
    )

    df_scenic_month.show(50, truncate=False)

    out5 = f"file://{os.path.join(LOCAL_ANALYSIS_DIR, 'scenic_month_hot')}"
    (
        df_scenic_month.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .csv(out5)
    )
    print("景点+月份热度统计已写出到目录：", out5)

    # 结束
    spark.stop()
    print("\n===== Spark 分析完成，所有结果已写到 data/analysis 目录下 =====")


if __name__ == "__main__":
    main()
