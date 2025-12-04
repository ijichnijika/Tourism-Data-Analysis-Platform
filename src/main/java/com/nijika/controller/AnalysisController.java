package com.nijika.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.nijika.common.Result;
import com.nijika.entity.*;
import com.nijika.mapper.StatsMapper;
import com.nijika.service.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@Tag(name = "旅游大数据分析接口")
@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class AnalysisController {

    private final IScenicSpotService scenicSpotService;
    private final IScenicWordCloudService scenicWordCloudService;
    private final IScenicAspectAnalysisService scenicAspectAnalysisService;
    private final IReviewFactService reviewFactService;
    private final StatsMapper statsMapper;
    //   景点/产品热度与词云分析
    @Operation(summary = "热门景点 ", description = "基于评论数量倒序排列，返回前10个热门景点")
    @GetMapping("/hotspot/scenic")
    public Result<List<ScenicSpot>> getHotScenicSpots() {
        return Result.success(scenicSpotService.getHotSpots(10));
    }

    @Operation(summary = "景点词云分析", description = "获取指定景点的词云数据，返回前50个高频词")
    @GetMapping("/wordcloud")
    public Result<List<ScenicWordCloud>> getWordCloud(
            @Parameter(description = "景点ID") @RequestParam(required = false) Integer scenicId) {
        LambdaQueryWrapper<ScenicWordCloud> wrapper = new LambdaQueryWrapper<>();
        if (scenicId != null) {
            wrapper.eq(ScenicWordCloud::getScenicId, scenicId);
        }
        wrapper.orderByDesc(ScenicWordCloud::getFrequency);
        wrapper.last("LIMIT 50");
        return Result.success(scenicWordCloudService.list(wrapper));
    }

    @Operation(summary = "景点模糊搜索", description = "根据名称、地址或类别模糊搜索景点 (支持 Redis 缓存)")
    @GetMapping("/search")
    public Result<List<ScenicSpot>> searchSpots(
            @Parameter(description = "搜索关键词") @RequestParam String keyword) {
        return Result.success(scenicSpotService.searchSpots(keyword));
    }

    //   区域人气排行与多维排序

    @Operation(summary = "区域景点排行", description = "支持按人气(popularity)、评分(rating)、价格(price)排序")
    @GetMapping("/ranking")
    public Result<List<ScenicSpot>> getRegionalRank(
            @Parameter(description = "排序类型: price/rating/popularity") @RequestParam(required = false) String sortType,
            @Parameter(description = "城市ID") @RequestParam(required = false) Integer cityId) {
        String sortField = "id";
        if ("price".equals(sortType)) {
            sortField = "price";
        } else if ("rating".equals(sortType)) {
            sortField = "score";
        }
        return Result.success(scenicSpotService.getSpotsByCity(cityId, sortField, "DESC"));
    }

    //  热门趋势时序分析

    @Operation(summary = "热门趋势分析", description = "获取景点的年度热度趋势数据")
    @GetMapping("/trend")
    public Result<Map<String, Object>> getTrendAnalysis(
            @Parameter(description = "景点ID") @RequestParam(required = false) Integer scenicId) {
        if (scenicId == null) {
            return Result.error("景点ID不能为空");
        }
        return Result.success(reviewFactService.getTrendAnalysis(scenicId));
    }

    //   “六要素”情感与语义网络分析

    @Operation(summary = "六要素情感分析", description = "获取景点在食、住、行、游、购、娱六个维度的情感评分")
    @GetMapping("/aspect")
    public Result<List<ScenicAspectAnalysis>> getAspectAnalysis(
            @Parameter(description = "景点ID") @RequestParam(required = false) Integer scenicId) {
        LambdaQueryWrapper<ScenicAspectAnalysis> wrapper = new LambdaQueryWrapper<>();
        if (scenicId != null) {
            wrapper.eq(ScenicAspectAnalysis::getScenicId, scenicId);
        }
        // 获取最新的统计
        wrapper.orderByDesc(ScenicAspectAnalysis::getStatYear);
        return Result.success(scenicAspectAnalysisService.list(wrapper));
    }


    @Operation(summary = "全球统计数据")
    @GetMapping("/stats/global")
    public Result<List<com.nijika.entity.GlobalStats>> getGlobalStats() {
        return Result.success(statsMapper.selectGlobalStats());
    }

    @Operation(summary = "景区统计数据")
    @GetMapping("/stats/scenic")
    public Result<List<com.nijika.entity.ScenicStats>> getScenicStats() {
        return Result.success(statsMapper.selectScenicStats());
    }

    @Operation(summary = "酒店统计数据")
    @GetMapping("/stats/hotel")
    public Result<List<com.nijika.entity.HotelStats>> getHotelStats() {
        return Result.success(statsMapper.selectHotelStats());
    }

    @Operation(summary = "旅游消费统计")
    @GetMapping("/stats/consumption")
    public Result<List<com.nijika.entity.TravelConsumption>> getTravelConsumption() {
        return Result.success(statsMapper.selectTravelConsumption());
    }

    @Operation(summary = "全局词云数据")
    @GetMapping("/stats/wordcloud")
    public Result<List<com.nijika.entity.WordCloudData>> getGlobalWordCloud() {
        return Result.success(statsMapper.selectGlobalWordCloud());
    }
}
