package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("scenic_aspect_analysis")
@Schema(description = "景点六要素分析实体")
public class ScenicAspectAnalysis {
    @TableId(value = "id", type = IdType.AUTO)
    @Schema(description = "主键ID")
    private Long id;

    @Schema(description = "景点ID")
    private Integer scenicId;

    @Schema(description = "城市ID")
    private Integer cityId;

    @Schema(description = "省份ID")
    private Integer provinceId;

    @Schema(description = "统计年份")
    private Integer statYear;

    @Schema(description = "统计月份")
    private Integer statMonth;

    @Schema(description = "评价维度 (食/住/行/游/购/娱)")
    private String aspectName;

    @Schema(description = "维度评分")
    private BigDecimal score;

    @Schema(description = "评论数量")
    private Integer commentCount;

    @Schema(description = "正向评论占比")
    private BigDecimal positiveRatio;

    @Schema(description = "典型关键词")
    private String keywords;

    @Schema(description = "创建时间")
    private LocalDateTime createdAt;
}
