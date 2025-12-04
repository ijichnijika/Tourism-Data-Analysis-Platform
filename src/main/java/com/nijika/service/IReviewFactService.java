package com.nijika.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.nijika.entity.ReviewFact;

import java.util.Map;

public interface IReviewFactService extends IService<ReviewFact> {
    Map<String, Object> getTrendAnalysis(Integer scenicId);
}
