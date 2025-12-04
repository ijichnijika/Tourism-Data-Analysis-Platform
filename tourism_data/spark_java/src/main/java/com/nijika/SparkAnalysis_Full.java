package com.nijika;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.*;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.spark.api.java.function.FilterFunction;
import org.apache.spark.sql.*;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.expressions.Window;
import org.apache.spark.sql.types.*;

import java.util.*;
import static org.apache.spark.sql.functions.*;

public class SparkAnalysis_Full {
    private static final String ZK_HOST = "ubuntu-linux-2404";
    private static final String DB_URL = "jdbc:mysql://localhost:3306/tourism_analysis?useSSL=false&characterEncoding=utf-8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true";

    //停用词表
    private static final Set<String> STOP_WORDS = new HashSet<>(Arrays.asList(
            "的", "了", "是", "在", "和", "有", "去", "我", "我们", "都", "很", "也", "就", "这", "那"
    ));

    public static void main(String[] args) {
        System.setProperty("HADOOP_USER_NAME", "hadoop");
        SparkSession spark = SparkSession.builder()
                .master("local[*]")
                .appName("Tourism_Final_Cleanup")
                .getOrCreate();

        Properties props = new Properties();
        props.put("user", "root");
        props.put("password", "waxyf2022");
        props.put("driver", "com.mysql.cj.jdbc.Driver");

        System.out.println("==========  启动强力清洗分析模式 ==========");

        try {
            analyzeGlobal(spark, props);      // 1. 全球
            analyzeHotels(spark, props);      // 2. 酒店
            analyzeScenics(spark, props);     // 3. 景点
            analyzeTravelNotes(spark, props); // 4. 游记
            analyzeComments(spark, props);    // 5. 评论

            System.out.println("========== 数据清洗完成，报表已生成 ==========");
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            spark.stop();
        }
    }

    
    // 1. 全球分析
    
    private static void analyzeGlobal(SparkSession s, Properties p) {
        StructType schema = new StructType()
                .add("country", DataTypes.StringType).add("city", DataTypes.StringType).add("visitors", DataTypes.LongType);

        Dataset<Row> df = loadFromHBaseDirect(s, "tourism:global_rank", schema, r -> {
            String c = safeStr(Bytes.toString(r.getValue(Bytes.toBytes("info"), Bytes.toBytes("country"))));
            String city = safeStr(Bytes.toString(r.getValue(Bytes.toBytes("info"), Bytes.toBytes("city"))));
            long v = safeLong(Bytes.toString(r.getValue(Bytes.toBytes("info"), Bytes.toBytes("visitors"))));

            return RowFactory.create(c, city, v);
        });

        // 规则：长度必须<=10，且不能包含特殊符号，不能是"未知"
        Dataset<Row> cleanDF = df.filter((FilterFunction<Row>) row -> {
            String city = row.getString(1);
            // 1. 长度过滤
            if (city.length() > 10 || city.length() < 2) return false;
            // 2. 关键词黑名单
            if (city.contains("http") || city.contains("攻略") || city.contains("简介") || city.contains("Unknown")) return false;
            // 3. 正则：必须是纯中文或纯字母，不能带标点符号（防止把评论当城市）
            return city.matches("^[\\u4e00-\\u9fa5a-zA-Z]+$");
        });

        // 取 Top City
        org.apache.spark.sql.expressions.WindowSpec w = Window.partitionBy("country").orderBy(col("visitors").desc());
        Dataset<Row> res = cleanDF.withColumn("rn", row_number().over(w))
                .filter(col("rn").equalTo(1))
                .groupBy("country", "city")
                .agg(sum("visitors").alias("total_visitors"), first("city").alias("top_city"))
                .join(
                        cleanDF.groupBy("country").agg(sum("visitors").alias("real_total"), round(avg("visitors"),0).alias("avg_city_heat")),
                        "country"
                )
                .select(col("country"), col("top_city"), col("real_total").alias("total_visitors"), col("avg_city_heat"));

        res.write().mode(SaveMode.Overwrite).jdbc(DB_URL, "ads_global_stats", p);
        System.out.println(">>> [1/5] 全球分析 (已剔除乱码城市)");
    }

    
    // 2. 酒店分析 (数据插补)
    
    private static void analyzeHotels(SparkSession s, Properties p) {
        StructType schema = new StructType().add("region", DataTypes.StringType).add("p", DataTypes.DoubleType).add("s", DataTypes.DoubleType);
        Dataset<Row> df = loadFromHBaseDirect(s, "tourism:hotels", schema, r -> {
            String rowKey = Bytes.toString(r.getRow());
            String region = (rowKey != null && rowKey.contains("_")) ? rowKey.split("_")[0] : "其他";
            double pr = safeDouble(Bytes.toString(r.getValue(Bytes.toBytes("price"), Bytes.toBytes("val"))));
            double sc = safeDouble(Bytes.toString(r.getValue(Bytes.toBytes("price"), Bytes.toBytes("score"))));

            return RowFactory.create(safeStr(region), pr, sc);
        });

        df.filter(col("region").notEqual("Unknown").and(length(col("region")).lt(10)))
                .groupBy("region").agg(
                        round(avg("p"),2).alias("avg_price"),
                        round(avg("s"),1).alias("avg_score"),
                        count("p").alias("hotel_count")
                ).write().mode(SaveMode.Overwrite).jdbc(DB_URL, "ads_hotel_stats", p);
        System.out.println(">>> [2/5] 酒店分析完成");
    }

    
    // 3. 景点分析
    
    private static void analyzeScenics(SparkSession s, Properties p) {
        StructType schema = new StructType()
                .add("city", DataTypes.StringType).add("s", DataTypes.DoubleType).add("p", DataTypes.DoubleType).add("c", DataTypes.LongType).add("st", DataTypes.IntegerType);

        Dataset<Row> df = loadFromHBaseDirect(s, "tourism:scenic", schema, r -> {
            String rowKey = Bytes.toString(r.getRow());
            String city = safeStr(Bytes.toString(r.getValue(Bytes.toBytes("detail"), Bytes.toBytes("city"))));
            if (city.equals("未知") && rowKey.contains("_")) city = rowKey.split("_")[0];

            String scStr = Bytes.toString(r.getValue(Bytes.toBytes("detail"), Bytes.toBytes("score")));
            double sc = 0.0;
            if (scStr != null && scStr.contains("width")) {
                try { sc = Double.parseDouble(scStr.replaceAll("\\D+", "")) / 20.0; } catch(Exception e){}
            } else {
                sc = safeDouble(scStr);
            }
            return RowFactory.create(city, sc, 0);
        });

        df.filter(length(col("city")).gt(1).and(length(col("city")).lt(8)).and(col("city").notEqual("未知")))
                .groupBy("city").agg(
                        count("city").alias("spot_count"),
                        round(avg("s"), 1).alias("avg_score"),
                        round(avg("p"), 2).alias("avg_price"),
                        sum("c").alias("total_sales"),
                        sum("st").alias("total_strategies")
                ).write().mode(SaveMode.Overwrite).jdbc(DB_URL, "ads_scenic_stats", p);
        System.out.println(">>> [3/5] 景点分析完成");
    }

    
    // 4. 游记分析
    
    private static void analyzeTravelNotes(SparkSession s, Properties p) {
        StructType schema = new StructType().add("dest", DataTypes.StringType).add("c", DataTypes.DoubleType).add("d", DataTypes.DoubleType);
        Dataset<Row> df = loadFromHBaseDirect(s, "tourism:travel_notes", schema, r -> {
            String rowKey = Bytes.toString(r.getRow());
            String dest = "未知";
            if (rowKey.contains("_")) dest = rowKey.substring(0, rowKey.lastIndexOf("_"));

            double cost = safeDouble(Bytes.toString(r.getValue(Bytes.toBytes("content"), Bytes.toBytes("cost"))));
            double days = safeDouble(Bytes.toString(r.getValue(Bytes.toBytes("content"), Bytes.toBytes("days"))));

            return RowFactory.create(safeStr(dest), cost, days);
        });

        df.filter(length(col("dest")).gt(1).and(length(col("dest")).lt(10)).and(col("dest").notEqual("未知")))
                .groupBy("dest").agg(
                        round(avg("c"), 2).alias("avg_cost"),
                        round(avg("d"), 1).alias("avg_days"),
                        count("dest").alias("note_count")
                ).withColumnRenamed("dest", "destination")
                .write().mode(SaveMode.Overwrite).jdbc(DB_URL, "ads_travel_consumption", p);
        System.out.println(">>> [4/5] 游记分析完成");
    }

    
    // 5. 评论分析
    
    private static void analyzeComments(SparkSession s, Properties p) {
        List<Row> allWords = new ArrayList<>();
        Configuration conf = HBaseConfiguration.create();
        conf.set("hbase.zookeeper.quorum", ZK_HOST);
        conf.set("hbase.zookeeper.property.clientPort", "2181");
        try (Connection conn = ConnectionFactory.createConnection(conf);
             Table table = conn.getTable(TableName.valueOf("tourism:comments"));
             ResultScanner scanner = table.getScanner(new Scan())) {
            for (Result r : scanner) {
                String txt = Bytes.toString(r.getValue(Bytes.toBytes("data"), Bytes.toBytes("content")));
                if (txt != null) {
                    String clean = txt.replaceAll("[^\\u4e00-\\u9fa5]", " ");
                    for (String w : clean.split("\\s+")) {
                        // 过滤长度和停用词
                        if (w.length() >= 2 && w.length() < 5 && !STOP_WORDS.contains(w)) {
                            allWords.add(RowFactory.create(w));
                        }
                    }
                }
            }
        } catch (Exception e) {}

        Dataset<Row> df = s.createDataFrame(allWords, new StructType().add("keyword", DataTypes.StringType));
        df.groupBy("keyword").count()
                .withColumnRenamed("count", "cnt").orderBy(col("cnt").desc()).limit(100)
                .write().mode(SaveMode.Overwrite).jdbc(DB_URL, "ads_word_cloud", p);
        System.out.println(">>> [5/5] 评论分析完成");
    }

    // --- 工具 ---
    private static Dataset<Row> loadFromHBaseDirect(SparkSession spark, String tableNameStr, StructType schema, RowMapper mapper) {
        List<Row> rows = new ArrayList<>();
        Configuration conf = HBaseConfiguration.create();
        conf.set("hbase.zookeeper.quorum", ZK_HOST);
        conf.set("hbase.zookeeper.property.clientPort", "2181");
        try (Connection conn = ConnectionFactory.createConnection(conf);
             Table table = conn.getTable(TableName.valueOf(tableNameStr));
             ResultScanner scanner = table.getScanner(new Scan())) {
            for (Result result : scanner) {
                try {
                    Row row = mapper.map(result);
                    if (row != null) rows.add(row);
                } catch (Exception e) {}
            }
        } catch (Exception e) { e.printStackTrace(); }
        return spark.createDataFrame(rows, schema);
    }

    @FunctionalInterface interface RowMapper { Row map(Result result); }
    private static String safeStr(String s) { return (s == null || s.trim().isEmpty()) ? "未知" : s.trim(); }
    private static long safeLong(String s) { try { return Long.parseLong(s.replaceAll("\\D+", "")); } catch(Exception e){ return 0L; } }
    private static double safeDouble(String s) { try { return Double.parseDouble(s.replaceAll("[^0-9.]", "")); } catch(Exception e){ return 0.0; } }
}