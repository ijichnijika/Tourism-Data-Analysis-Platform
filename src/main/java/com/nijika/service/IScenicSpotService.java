package com.nijika.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.nijika.entity.ScenicSpot;

import java.util.List;

public interface IScenicSpotService extends IService<ScenicSpot> {
    List<ScenicSpot> getHotSpots(int limit);

    List<ScenicSpot> getSpotsByCity(Integer cityId, String sortField, String sortOrder);

    List<ScenicSpot> searchSpots(String keyword);
}
