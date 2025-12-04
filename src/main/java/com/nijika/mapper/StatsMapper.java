package com.nijika.mapper;

import com.nijika.entity.*;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface StatsMapper {

    @Select("SELECT * FROM tourism_analysis.ads_global_stats LIMIT 10")
    List<GlobalStats> selectGlobalStats();

    @Select("SELECT t1.*, t2.city_id as cityId FROM tourism_analysis.ads_scenic_stats t1 LEFT JOIN travel_db.city t2 ON t1.city = t2.city_name ORDER BY t1.total_sales DESC LIMIT 20")
    List<ScenicStats> selectScenicStats();

    @Select("SELECT * FROM tourism_analysis.ads_hotel_stats ORDER BY hotel_count DESC LIMIT 20")
    List<HotelStats> selectHotelStats();

    @Select("SELECT * FROM tourism_analysis.ads_travel_consumption ORDER BY note_count DESC LIMIT 20")
    List<TravelConsumption> selectTravelConsumption();

    @Select("SELECT * FROM tourism_analysis.ads_word_cloud")
    List<WordCloudData> selectGlobalWordCloud();

    @Select("SELECT * FROM tourism_analysis.ads_travel_consumption WHERE destination LIKE CONCAT('%', #{keyword}, '%')")
    List<TravelConsumption> selectConsumptionByKeyword(String keyword);


    @Select("SELECT * FROM tourism_analysis.ads_scenic_stats WHERE city LIKE CONCAT('%', #{keyword}, '%')")
    List<ScenicStats> selectCityStatsByKeyword(String keyword);
}
