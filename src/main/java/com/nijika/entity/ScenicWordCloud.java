package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("scenic_word_cloud")
@Schema(description = "景点词云分析实体")
public class ScenicWordCloud {
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

    @Schema(description = "关键词")
    private String word;

    @Schema(description = "词频")
    private Integer frequency;

    @Schema(description = "文档计数")
    private Integer docCount;

    @Schema(description = "情感倾向 (1:正向, 0:中性, -1:负向)")
    private Integer sentiment;

    @Schema(description = "创建时间")
    private LocalDateTime createdAt;
}
