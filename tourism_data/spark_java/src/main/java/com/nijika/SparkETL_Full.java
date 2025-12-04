package com.nijika;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.hadoop.hbase.mapreduce.TableOutputFormat;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.hadoop.mapreduce.Job;
import org.apache.spark.api.java.JavaPairRDD;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.SparkSession;
import scala.Tuple2;
import java.util.UUID;
import static org.apache.spark.sql.functions.*;

public class SparkETL_Full {

    private static final String HDFS_URI = "hdfs://ubuntu-linux-2404:9000";
    private static final String ZK_QUORUM = "ubuntu-linux-2404";

    public static void main(String[] args) {
        System.setProperty("HADOOP_USER_NAME", "hadoop");
        SparkSession spark = SparkSession.builder()
                .master("local[*]")
                .appName("Tourism_ETL_Full")
                .config("fs.defaultFS", HDFS_URI)
                .getOrCreate();

        try {
            // 1. 全球排名
            String[] countries = {"中国", "日本", "美国", "法国", "英国", "俄罗斯", "韩国"};
            for (String country : countries) {
                try {
                    Dataset<Row> df = spark.read().option("header", "true").csv("/tourism/ods/rankings/qyer_city_rank_" + country + ".csv");
                    Dataset<Row> cleanDf = df.withColumn("visitors", regexp_replace(col("peopleNum"), "人去过", "").cast("long"))
                            .filter(col("city").isNotNull());

                    JavaPairRDD<ImmutableBytesWritable, Put> hbaseRDD = cleanDf.javaRDD().mapToPair(row -> {
                        String city = row.getAs("city");
                        String rowKey = country + "_" + city;
                        Put put = new Put(Bytes.toBytes(rowKey));
                        // 使用 safeStr 防止空值报错，且兼容 HBase 2.4+
                        put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("country"), Bytes.toBytes(safeStr(country)));
                        put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("city"), Bytes.toBytes(safeStr(city)));
                        put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("visitors"), Bytes.toBytes(safeStr(row.getAs("visitors"))));
                        put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("hot_spots"), Bytes.toBytes(safeStr(row.getAs("hotSpot"))));
                        return new Tuple2<>(new ImmutableBytesWritable(), put);
                    });
                    writeToHBase("tourism:global_rank", hbaseRDD);
                    System.out.println(">>> 成功写入: " + country);
                } catch (Exception e) { System.out.println(">>> 跳过: " + country); }
            }

            // 2. 酒店
            try {
                Dataset<Row> hotelDf = spark.read().option("header", "true").csv("/tourism/ods/hotels/meituan_hotels.csv");
                Dataset<Row> cleanHotel = hotelDf.withColumn("price", regexp_replace(col("价格"), "¥", "").cast("double"))
                        .withColumn("score", col("评分").cast("double")).filter(col("标题").isNotNull());

                JavaPairRDD<ImmutableBytesWritable, Put> hotelRDD = cleanHotel.javaRDD().mapToPair(row -> {
                    String name = row.getAs("标题");
                    String region = row.getAs("地区");
                    String rowKey = (region != null ? region : "Unknown") + "_" + name;
                    Put put = new Put(Bytes.toBytes(rowKey));
                    put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"), Bytes.toBytes(safeStr(name)));
                    put.addColumn(Bytes.toBytes("price"), Bytes.toBytes("val"), Bytes.toBytes(safeStr(row.getAs("price"))));
                    put.addColumn(Bytes.toBytes("price"), Bytes.toBytes("score"), Bytes.toBytes(safeStr(row.getAs("score"))));
                    return new Tuple2<>(new ImmutableBytesWritable(), put);
                });
                writeToHBase("tourism:hotels", hotelRDD);
                System.out.println(">>> [成功] 酒店数据");
            } catch (Exception e) { e.printStackTrace(); }

            // 3. 景点
            try {
                Dataset<Row> baseDf = spark.read().option("header", "true").csv("/tourism/ods/scenic_spots/qunar_scenic.csv");
                JavaPairRDD<ImmutableBytesWritable, Put> baseRDD = baseDf.filter(col("spot_name").isNotNull()).javaRDD().mapToPair(row -> {
                    String starStr = row.getAs("star");
                    double score = 0.0;
                    if (starStr != null && starStr.contains("width")) score = Double.parseDouble(starStr.replaceAll("\\D+", "")) / 20.0;
                    String rowKey = row.getAs("city") + "_" + row.getAs("spot_name");
                    Put put = new Put(Bytes.toBytes(rowKey));
                    put.addColumn(Bytes.toBytes("detail"), Bytes.toBytes("city"), Bytes.toBytes(safeStr(row.getAs("city"))));
                    put.addColumn(Bytes.toBytes("detail"), Bytes.toBytes("name"), Bytes.toBytes(safeStr(row.getAs("spot_name"))));
                    put.addColumn(Bytes.toBytes("detail"), Bytes.toBytes("score"), Bytes.toBytes(String.valueOf(score)));
                    put.addColumn(Bytes.toBytes("detail"), Bytes.toBytes("lng"), Bytes.toBytes(safeStr(row.getAs("lng"))));
                    put.addColumn(Bytes.toBytes("detail"), Bytes.toBytes("lat"), Bytes.toBytes(safeStr(row.getAs("lat"))));
                    return new Tuple2<>(new ImmutableBytesWritable(), put);
                });
                writeToHBase("tourism:scenic", baseRDD);

                Dataset<Row> salesDf = spark.read().option("header", "true").csv("/tourism/ods/scenic_spots/cleaned_scenic_spots.csv");
                JavaPairRDD<ImmutableBytesWritable, Put> salesRDD = salesDf.filter(col("门票名称").isNotNull()).javaRDD().mapToPair(row -> {
                    String salesStr = row.getAs("已售数量");
                    long sales = (salesStr != null) ? Long.parseLong(salesStr.replaceAll("\\D+", "")) : 0;
                    Put put = new Put(Bytes.toBytes(row.getAs("地区") + "_" + row.getAs("门票名称")));
                    put.addColumn(Bytes.toBytes("sales"), Bytes.toBytes("price"), Bytes.toBytes(safeStr(row.getAs("门票价格"))));
                    put.addColumn(Bytes.toBytes("sales"), Bytes.toBytes("count"), Bytes.toBytes(String.valueOf(sales)));
                    return new Tuple2<>(new ImmutableBytesWritable(), put);
                });
                writeToHBase("tourism:scenic", salesRDD);

                Dataset<Row> extraDf = spark.read().option("header", "true").csv("/tourism/ods/scenic_spots/qunar_spots_data.csv");
                JavaPairRDD<ImmutableBytesWritable, Put> extraRDD = extraDf.filter(col("景点名称").isNotNull()).javaRDD().mapToPair(row -> {
                    Put put = new Put(Bytes.toBytes(row.getAs("城市名称") + "_" + row.getAs("景点名称")));
                    put.addColumn(Bytes.toBytes("extra"), Bytes.toBytes("strategies"), Bytes.toBytes(safeStr(row.getAs("攻略数量"))));
                    return new Tuple2<>(new ImmutableBytesWritable(), put);
                });
                writeToHBase("tourism:scenic", extraRDD);
                System.out.println(">>> [成功] 景点数据");
            } catch (Exception e) { e.printStackTrace(); }

            // 4. 评论
            processCommentFile(spark, "/tourism/ods/comments/mafengwo_comments.csv", "comment", "mafengwo");
            processCommentFile(spark, "/tourism/ods/comments/qyer_comments.csv", "comment", "qyer");
            processCommentFile(spark, "/tourism/ods/comments/cleaned_comments.csv", "评论", "cleaned");
            System.out.println(">>> [成功] 评论数据");

            // 5. 游记
            try {
                Dataset<Row> noteDf = spark.read().option("header", "true").csv("/tourism/ods/travel_notes/qunar_hotcore.csv");
                JavaPairRDD<ImmutableBytesWritable, Put> noteRDD = noteDf.filter(col("标题").isNotNull()).javaRDD().mapToPair(row -> {
                    String dest = row.getAs("途经目的地");
                    Put put = new Put(Bytes.toBytes((dest!=null?dest:"Unknown") + "_" + UUID.randomUUID().toString().substring(0,6)));
                    put.addColumn(Bytes.toBytes("content"), Bytes.toBytes("title"), Bytes.toBytes(safeStr(row.getAs("标题"))));
                    put.addColumn(Bytes.toBytes("content"), Bytes.toBytes("cost"), Bytes.toBytes(safeStr(row.getAs("人均费用"))));
                    put.addColumn(Bytes.toBytes("content"), Bytes.toBytes("days"), Bytes.toBytes(safeStr(row.getAs("出行天数"))));
                    return new Tuple2<>(new ImmutableBytesWritable(), put);
                });
                writeToHBase("tourism:travel_notes", noteRDD);
                System.out.println(">>> [成功] 游记数据");
            } catch (Exception e) { e.printStackTrace(); }

        } catch (Exception e) { e.printStackTrace(); } finally { spark.stop(); }
    }

    // 安全转换 String，防止 null 报错
    private static String safeStr(Object obj) {
        return obj == null ? "" : String.valueOf(obj);
    }

    private static void writeToHBase(String tableName, JavaPairRDD<ImmutableBytesWritable, Put> rdd) throws Exception {
        Configuration conf = HBaseConfiguration.create();
        conf.set("hbase.zookeeper.quorum", ZK_QUORUM);
        conf.set("hbase.zookeeper.property.clientPort", "2181");
        conf.set(TableOutputFormat.OUTPUT_TABLE, tableName);
        Job job = Job.getInstance(conf);
        job.setOutputKeyClass(ImmutableBytesWritable.class);
        job.setOutputValueClass(Put.class);
        job.setOutputFormatClass(TableOutputFormat.class);
        rdd.saveAsNewAPIHadoopDataset(job.getConfiguration());
    }

    private static void processCommentFile(SparkSession spark, String path, String colName, String source) {
        try {
            Dataset<Row> df = spark.read().option("header", "true").csv(path);
            JavaPairRDD<ImmutableBytesWritable, Put> rdd = df.filter(col(colName).isNotNull()).javaRDD().mapToPair(row -> {
                Put put = new Put(Bytes.toBytes(source + "_" + UUID.randomUUID().toString()));
                put.addColumn(Bytes.toBytes("data"), Bytes.toBytes("content"), Bytes.toBytes(safeStr(row.getAs(colName))));
                return new Tuple2<>(new ImmutableBytesWritable(), put);
            });
            writeToHBase("tourism:comments", rdd);
        } catch (Exception e) { System.out.println(">>> [跳过] 评论文件: " + path); }
    }
}