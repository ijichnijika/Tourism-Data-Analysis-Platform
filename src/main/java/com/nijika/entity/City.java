package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("city")
@Schema(description = "城市信息实体")
public class City {
    @TableId(value = "city_id", type = IdType.AUTO)
    @Schema(description = "城市ID")
    private Integer cityId;

    @Schema(description = "城市名称")
    private String cityName;

    @Schema(description = "所属省份ID")
    private Integer provinceId;

    @Schema(description = "城市级别 (1:直辖市, 2:省会, 3:地级市)")
    private Integer level;

    @Schema(description = "纬度")
    private Double lat;

    @Schema(description = "经度")
    private Double lon;
}
