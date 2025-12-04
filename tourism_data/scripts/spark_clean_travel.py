# -*- coding: utf-8 -*-
"""
马蜂窝旅游评论清洗脚本（面向 HBase ImportTsv）

输入：
    本地 CSV：
        /home/tian/bigdata/travel/data/raw/mfw_comment_raw.csv

        列：
            景点名称, 日期列表, 星级列表, 评论列表
        日期格式：
            2019-04-2313:11:40  （中间没有空格）

处理：
    1. 读取本地 CSV（file://）
    2. 去掉日期中的所有空白符，按 yyyy-MM-ddHH:mm:ss 解析为 timestamp
    3. 过滤掉时间解析失败 / 星级为空 / 景点名为空 / 评论为空 的行
    4. 拆分出 year / month / day
    5. 生成 HBase rowkey：
         scenic_name_year_month_day_star_自增ID
    6. 以 TSV 写到本地：
         /home/tian/bigdata/travel/data/clean/mfw_comment_clean_for_hbase.tsv

输出列顺序（给 ImportTsv 用）：
    HBASE_ROW_KEY
    scenic_name
    comment_time
    year
    month
    day
    star
    comment
"""

from __future__ import print_function

import os
import sys
import shutil
import glob

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    # ------------------------------------------------------------------
    # 0. 路径配置
    # ------------------------------------------------------------------
    # 当前脚本：/home/tian/bigdata/travel/scripts/spark_clean_travel.py
    # 项目根目录：/home/tian/bigdata/travel
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # /home/tian/bigdata/travel

    raw_csv = os.path.join(base_dir, "data", "raw", "mfw_comment_raw.csv")
    # 最终给 HBase ImportTsv 的 TSV
    hbase_tsv = os.path.join(base_dir, "data", "clean", "mfw_comment_clean_for_hbase.tsv")
    # Spark 写文件的临时目录（本地）
    tmp_dir_local = os.path.join(base_dir, "data", "clean", "_tmp_tsv_output")
    # Spark 访问本地目录需要加 file:// 前缀
    tmp_dir_spark = "file://" + tmp_dir_local

    print("===== 马蜂窝旅游评论清洗脚本启动 =====")
    print("项目根目录: {}".format(base_dir))
    print("原始 CSV 路径: {}".format(raw_csv))
    print("HBase TSV 输出路径: {}".format(hbase_tsv))
    sys.stdout.flush()

    # ------------------------------------------------------------------
    # 1. 创建 SparkSession
    # ------------------------------------------------------------------
    spark = (
        SparkSession.builder
        .appName("TravelCommentClean")
        .enableHiveSupport()  # 有 hive-site.xml 就顺带带上
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # ------------------------------------------------------------------
    # 2. 检查原始 CSV 是否存在
    # ------------------------------------------------------------------
    if not os.path.exists(raw_csv):
        print("!!! 原始 CSV 不存在: {}".format(raw_csv))
        spark.stop()
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. 读取原始 CSV（本地 file://）
    # ------------------------------------------------------------------
    print(">>> 读取原始 CSV ...")
    sys.stdout.flush()

    local_raw_uri = "file://" + raw_csv

    raw_df = (
        spark.read
        .option("header", "true")      # 第一行是表头
        .option("multiLine", "true")   # 评论里可能有换行
        .option("escape", "\"")        # 处理引号
        .csv(local_raw_uri)
    )

    # schema 打个样
    print(">>> 原始数据 Schema:")
    raw_df.printSchema()

    # ------------------------------------------------------------------
    # 4. 时间解析：2019-04-2313:11:40  -> timestamp
    # ------------------------------------------------------------------
    # 先把日期里的所有空白符去掉（防止有奇怪空格）
    # 再用 yyyy-MM-ddHH:mm:ss 解析
    print(">>> 时间解析统计 ...")
    sys.stdout.flush()

    df_time = (
        raw_df
        .select(
            F.col("景点名称").alias("scenic_name_raw"),
            F.col("日期列表").alias("date_raw"),
            F.col("星级列表").alias("star_raw"),
            F.col("评论列表").alias("comment_raw"),
        )
    )

    df_time = df_time.withColumn(
        "raw_time_trim",
        F.regexp_replace(F.col("date_raw"), r"\s+", "")  # 去掉空白
    )

    df_parsed = df_time.withColumn(
        "comment_time",
        F.to_timestamp("raw_time_trim", "yyyy-MM-ddHH:mm:ss")
    )

    # 统计解析成功/失败
    total_rows = raw_df.count()
    success_df = df_parsed.filter(F.col("comment_time").isNotNull())
    failed_df = df_parsed.filter(F.col("comment_time").isNull())

    success_rows = success_df.count()
    failed_rows = failed_df.count()

    print("总行数: {}  解析成功: {}  解析失败: {}".format(
        total_rows, success_rows, failed_rows
    ))

    if failed_rows > 0:
        print("===== 解析失败示例（前 20 行）=====")
        (
            failed_df
            .select("scenic_name_raw", "raw_time_trim")
            .show(20, truncate=False)
        )

    # ------------------------------------------------------------------
    # 5. 清洗 + 衍生字段（year/month/day/star 等）
    # ------------------------------------------------------------------
    # 只保留时间解析成功 + 星级非空 + 景点名非空 + 评论非空
    cleaned = (
        success_df
        .filter(F.col("star_raw").isNotNull())
        .filter(F.col("scenic_name_raw").isNotNull())
        .filter(F.col("comment_raw").isNotNull())
        .filter(F.col("scenic_name_raw") != "")
        .filter(F.col("comment_raw") != "")
    )

    # 衍生 year/month/day + star（int）
    cleaned = (
        cleaned
        .withColumn("year", F.date_format("comment_time", "yyyy"))
        .withColumn("month", F.date_format("comment_time", "MM"))
        .withColumn("day", F.date_format("comment_time", "dd"))
        .withColumn("star", F.col("star_raw").cast("int"))
        .withColumnRenamed("scenic_name_raw", "scenic_name")
        .withColumnRenamed("comment_raw", "comment")
    )

    # 再给 comment_time 格式化成字符串（方便 ImportTsv）
    cleaned = cleaned.withColumn(
        "comment_time_str",
        F.date_format("comment_time", "yyyy-MM-dd HH:mm:ss")
    )

    # 生成 rowkey：景点名_年_月_日_星级_唯一ID
    cleaned = cleaned.withColumn(
        "rowkey",
        F.concat_ws(
            "_",
            F.col("scenic_name"),
            F.col("year"),
            F.col("month"),
            F.col("day"),
            F.col("star").cast("string"),
            F.monotonically_increasing_id(),  # 保证同一景点同一天不同评论不冲突
        )
    )

    # 按 HBase ImportTsv 需要的顺序选列
    # HBASE_ROW_KEY, scenic_name, comment_time, year, month, day, star, comment
    result = cleaned.select(
        "rowkey",
        "scenic_name",
        "comment_time_str",
        "year",
        "month",
        "day",
        "star",
        "comment",
    )

    print("===== 清洗后前 5 行（检查 comment_time/year/month/day）=====")
    (
        result.select(
            "scenic_name",
            "comment_time_str",
            "year",
            "month",
            "day",
            "star",
        )
        .show(5, truncate=False)
    )

    # ------------------------------------------------------------------
    # 6. 写 TSV 到本地（给 HBase ImportTsv）
    # ------------------------------------------------------------------
    print(">>> 写入 HBase TSV 到本地 ...")
    sys.stdout.flush()

    # 先删掉本地临时目录
    if os.path.exists(tmp_dir_local):
        shutil.rmtree(tmp_dir_local)

    # coalesce(1) -> 生成单个 part-00000 文件，便于后面 mv
    (
        result
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("delimiter", "\t")
        .option("quote", "\u0000")   # 不要自动加引号
        .option("escape", "\u0000")
        .option("header", "false")   # 不输出表头
        .csv(tmp_dir_spark)          # 注意：用 file:// 前缀，明确写本地
    )

    # 在本地文件系统中查找 part-*.csv
    part_files = glob.glob(os.path.join(tmp_dir_local, "part-*.csv"))
    if not part_files:
        print("!!! 没有找到 TSV 输出文件 part-*.csv，清洗失败。")
        spark.stop()
        sys.exit(1)

    part_file = part_files[0]

    # 如果已有老的 TSV，先删掉
    if os.path.exists(hbase_tsv):
        os.remove(hbase_tsv)

    # 把 part-xxxx.csv 移动/重命名成正式的 mfw_comment_clean_for_hbase.tsv
    shutil.move(part_file, hbase_tsv)

    # 临时目录没用了，删掉
    shutil.rmtree(tmp_dir_local)

    print(">>> HBase TSV 已生成: {}".format(hbase_tsv))
    print("===== 脚本执行完成 =====")

    spark.stop()


if __name__ == "__main__":
    main()
