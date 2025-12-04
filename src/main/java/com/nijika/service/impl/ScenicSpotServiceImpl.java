package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.ScenicSpot;
import com.nijika.entity.TravelConsumption;
import com.nijika.entity.ScenicStats;
import com.nijika.mapper.ScenicSpotMapper;
import com.nijika.mapper.StatsMapper;
import com.nijika.service.IScenicSpotService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class ScenicSpotServiceImpl extends ServiceImpl<ScenicSpotMapper, ScenicSpot> implements IScenicSpotService {

    private final ScenicSpotMapper scenicSpotMapper;
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private StatsMapper statsMapper;

    @Override
    public List<ScenicSpot> getHotSpots(int limit) {
        return scenicSpotMapper.selectHotSpots(limit);
    }

    @Override
    public List<ScenicSpot> getSpotsByCity(Integer cityId, String sortField, String sortOrder) {
        // 白名单校验，防止 SQL 注入
        if (!"price".equals(sortField) && !"score".equals(sortField)) {
            sortField = "id";
        }
        if (!"ASC".equalsIgnoreCase(sortOrder)) {
            sortOrder = "DESC";
        }
        return scenicSpotMapper.selectSortedSpots(cityId, sortField, sortOrder);
    }

    @Override
    @SuppressWarnings("unchecked")
    public List<ScenicSpot> searchSpots(String keyword) {
        String cacheKey = "search:scenic:" + keyword;

        // 1. Search in Redis
        if (Boolean.TRUE.equals(redisTemplate.hasKey(cacheKey))) {
            return (List<ScenicSpot>) redisTemplate.opsForValue().get(cacheKey);
        }

        // 2. Search in DB (Scenic Spots)
        List<ScenicSpot> spots = this.lambdaQuery()
                .like(ScenicSpot::getScenicName, keyword)
                .or()
                .like(ScenicSpot::getAddress, keyword)
                .or()
                .like(ScenicSpot::getCategory, keyword)
                .list();

        // 3. Search in DB (Travel Consumption -> Destinations)
        List<TravelConsumption> consumptions = statsMapper.selectConsumptionByKeyword(keyword);
        for (TravelConsumption c : consumptions) {
            ScenicSpot s = new ScenicSpot();
            s.setScenicName(c.getDestination());
            s.setAvgPrice(c.getAvgCost() != null ? java.math.BigDecimal.valueOf(c.getAvgCost()) : null);
            s.setCategory("热门目的地");
            s.setAvgScore(java.math.BigDecimal.valueOf(4.5)); // Default score
            s.setCityId(999); // Dummy ID
            spots.add(s);
        }

        // 4. Search in DB (City Stats -> Cities)
        List<ScenicStats> cities = statsMapper.selectCityStatsByKeyword(keyword);
        for (ScenicStats c : cities) {
            ScenicSpot s = new ScenicSpot();
            s.setScenicName(c.getCity());
            s.setAvgPrice(c.getAvgPrice() != null ? java.math.BigDecimal.valueOf(c.getAvgPrice()) : null);
            s.setAvgScore(c.getAvgScore() != null ? java.math.BigDecimal.valueOf(c.getAvgScore()) : null);
            s.setCategory("城市");
            s.setCityId(c.getCityId() != null ? c.getCityId() : 999);
            spots.add(s);
        }

        // 5. Cache results
        if (!spots.isEmpty()) {
            redisTemplate.opsForValue().set(cacheKey, spots, 1, TimeUnit.HOURS);
        }

        return spots;
    }
}