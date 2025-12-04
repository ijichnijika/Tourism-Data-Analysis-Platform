package com.nijika.entity;

import lombok.Data;

@Data
public class ScenicStats {
    private String city;
    private Long spotCount;
    private Double avgScore;
    private Double avgPrice;
    private Long totalSales;
    private Long totalStrategies;
    private Integer cityId;
}
