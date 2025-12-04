package com.nijika.entity;

import lombok.Data;

@Data
public class HotelStats {
    private String region;
    private Double avgPrice;
    private Double avgScore;
    private Long hotelCount;
}
