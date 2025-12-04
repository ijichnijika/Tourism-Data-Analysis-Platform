package com.nijika.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.nijika.entity.ReviewFact;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import java.util.List;
import java.util.Map;
@Mapper
public interface ReviewFactMapper extends BaseMapper<ReviewFact> {

    /**
     * 需求2.4: 趋势分析
     * 按年月统计评论数量
     */
    @Select("SELECT DATE_FORMAT(comment_time, '%Y-%m') as timeStr, COUNT(*) as count " +
            "FROM review_fact " +
            "WHERE scenic_id = #{scenicId} " +
            "GROUP BY timeStr " +
            "ORDER BY timeStr ASC " +
            "LIMIT 36") // 取最近3年数据
    List<Map<String, Object>> selectTrendByScenic(@Param("scenicId") Integer scenicId);
}