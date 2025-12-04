package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.ReviewFact;
import com.nijika.mapper.ReviewFactMapper;
import com.nijika.service.IReviewFactService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class ReviewFactServiceImpl extends ServiceImpl<ReviewFactMapper, ReviewFact> implements IReviewFactService {

    private final ReviewFactMapper reviewFactMapper;

    @Override
    public Map<String, Object> getTrendAnalysis(Integer scenicId) {
        List<Map<String, Object>> data = reviewFactMapper.selectTrendByScenic(scenicId);

        // 转换为前端 ECharts 易用的格式: { xAxis: [...], series: [...] }
        List<String> xAxis = new ArrayList<>();
        List<Long> series = new ArrayList<>();

        for (Map<String, Object> record : data) {
            xAxis.add((String) record.get("timeStr"));
            series.add((Long) record.get("count"));
        }

        Map<String, Object> result = new HashMap<>();
        result.put("xAxis", xAxis);
        result.put("series", series);
        return result;
    }
}