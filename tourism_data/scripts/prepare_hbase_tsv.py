#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd

BASE_DIR = "/home/tian/bigdata/travel"
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")

ASPECT_CSV = os.path.join(ANALYSIS_DIR, "scenic_aspect_analysis.csv")
WORD_CSV   = os.path.join(ANALYSIS_DIR, "scenic_word_cloud.csv")

ASPECT_TSV = os.path.join(ANALYSIS_DIR, "scenic_aspect_for_hbase.tsv")
WORD_TSV   = os.path.join(ANALYSIS_DIR, "scenic_wordcloud_for_hbase.tsv")


def gen_aspect_tsv():
    df = pd.read_csv(ASPECT_CSV)

    # RowKey = scenicId_aspectName 例如 1_食
    df["rowkey"] = df["scenic_id"].astype(str) + "_" + df["aspect_name"].astype(str)

    # ImportTsv 要求：第一列是 HBASE_ROW_KEY，其余依次映射到 cf:xxx
    cols = ["rowkey", "scenic_id", "aspect_name", "score", "keywords"]
    df[cols].to_csv(ASPECT_TSV, sep="\t", header=False, index=False)
    print(f"已生成: {ASPECT_TSV}")


def gen_wordcloud_tsv():
    df = pd.read_csv(WORD_CSV)

    # RowKey = scenicId_word 例如 1_震撼
    df["rowkey"] = df["scenic_id"].astype(str) + "_" + df["word"].astype(str)

    cols = ["rowkey", "scenic_id", "word", "frequency", "sentiment", "create_time"]
    df[cols].to_csv(WORD_TSV, sep="\t", header=False, index=False)
    print(f"已生成: {WORD_TSV}")


if __name__ == "__main__":
    gen_aspect_tsv()
    gen_wordcloud_tsv()
