package com.nijika;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.hbase.HBaseConfiguration;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.hadoop.hbase.mapreduce.TableInputFormat;
import org.apache.hadoop.hbase.util.Bytes;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.sql.SparkSession;
import scala.Tuple2;

public class SparkDebug {
    private static final String ZK = "ubuntu-linux-2404";

    public static void main(String[] args) {
        System.setProperty("HADOOP_USER_NAME", "hadoop");
        SparkSession spark = SparkSession.builder()
                .master("local[*]")
                .appName("Debug_HBase")
                .getOrCreate();

        System.out.println("========== 🔍 开始 HBase 连通性诊断 ==========");

        try {
            Configuration conf = HBaseConfiguration.create();
            conf.set("hbase.zookeeper.quorum", ZK);
            conf.set(TableInputFormat.INPUT_TABLE, "tourism:global_rank");

            JavaRDD<Tuple2<ImmutableBytesWritable, Result>> rdd = spark.sparkContext()
                    .newAPIHadoopRDD(conf, TableInputFormat.class, ImmutableBytesWritable.class, Result.class)
                    .toJavaRDD();

            JavaRDD<String> resultRDD = rdd.map(tuple -> {
                Result result = tuple._2;
                String rowKey = Bytes.toString(result.getRow());
                byte[] val = result.getValue(Bytes.toBytes("info"), Bytes.toBytes("city"));
                String city = (val != null) ? Bytes.toString(val) : "NULL";
                return "RowKey: " + rowKey + ", City: " + city;
            });

            long count = rdd.count();
            System.out.println(">>> [诊断结果] HBase 'tourism:global_rank' 表中读取到: " + count + " 条数据");

            if (count > 0) {
                System.out.println(">>> [数据抽样] 第一条数据内容:");
                // ✅ Only collect the String result (which IS serializable)
                String firstResult = resultRDD.first();
                System.out.println(firstResult);
            } else {
                System.out.println(">>> ⚠️ 警告: Spark 连上了 HBase，但没读到数据！");
                System.out.println(">>> 可能原因: 1. 表真是空的 2. Mac 无法连接 RegionServer (检查 /etc/hosts)");
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        spark.stop();
    }
}