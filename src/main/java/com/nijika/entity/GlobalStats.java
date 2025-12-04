package com.nijika.entity;

import lombok.Data;

@Data
public class GlobalStats {
    private String country;
    private String topCity;
    private Long totalVisitors;
    private Double avgCityHeat;
}
