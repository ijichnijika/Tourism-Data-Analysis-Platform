package com.nijika.entity;

import lombok.Data;

@Data
public class TravelConsumption {
    private String destination;
    private Integer avgCost;
    private Integer avgDays;
    private Long noteCount;
}
