package com.nijika.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.nijika.entity.ScenicSpot;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;

@Mapper
public interface ScenicSpotMapper extends BaseMapper<ScenicSpot> {

        /**
         * 需求2.2: 热门景点 Top 10
         * 直接使用 scenic_spot 表的 review_count 字段排序
         */
        @Select("SELECT * FROM scenic_spot ORDER BY review_count DESC LIMIT #{limit}")
        List<ScenicSpot> selectHotSpots(@Param("limit") int limit);

        /**
         * 需求2.3: 区域人气/评价/价格排序
         * 使用 MyBatis 动态 SQL (Script标签在注解中较难写，简单场景直接拼写，注意 sortField 需在 Service 层校验防注入)
         */
        @Select("<script>" +
                        "SELECT * FROM scenic_spot " +
                        "WHERE city_id = #{cityId} " +
                        "ORDER BY " +
                        "<choose>" +
                        "  <when test='sortField == \"price\"'>avg_price</when>" +
                        "  <when test='sortField == \"score\"'>avg_score</when>" +
                        "  <otherwise>scenic_id</otherwise>" + // 默认排序
                        "</choose> " +
                        "${sortOrder}" +
                        "</script>")
        List<ScenicSpot> selectSortedSpots(@Param("cityId") Integer cityId,
                        @Param("sortField") String sortField,
                        @Param("sortOrder") String sortOrder);
}