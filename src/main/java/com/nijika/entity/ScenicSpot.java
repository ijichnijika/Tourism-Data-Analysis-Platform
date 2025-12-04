package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.math.BigDecimal;

import java.io.Serializable;

@Data
@TableName("scenic_spot")
@Schema(description = "景点信息实体")
public class ScenicSpot implements Serializable {
    private static final long serialVersionUID = 1L;

    @TableId(value = "scenic_id", type = IdType.AUTO)
    @Schema(description = "景点ID")
    private Integer scenicId;

    @Schema(description = "景点名称")
    private String scenicName;

    @Schema(description = "所属城市ID")
    private Integer cityId;

    @Schema(description = "景点类别")
    private String category;

    @Schema(description = "人均消费/门票")
    private BigDecimal avgPrice;

    @Schema(description = "综合评分")
    private BigDecimal avgScore;

    /**
     * 评论总数 (冗余字段，用于排序)
     */
    private Integer reviewCount;

    @Schema(description = "详细地址")
    private String address;
}
