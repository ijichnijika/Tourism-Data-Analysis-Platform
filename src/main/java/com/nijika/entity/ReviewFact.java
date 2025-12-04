package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("review_fact")
@Schema(description = "评论事实实体")
public class ReviewFact {
    @TableId(value = "review_id", type = IdType.AUTO)
    @Schema(description = "评论ID")
    private Long reviewId;

    @Schema(description = "关联景点ID")
    private Integer scenicId;

    @Schema(description = "关联用户ID")
    private Long userId;

    @Schema(description = "评论时间")
    private LocalDateTime commentTime;

    @Schema(description = "评分星级")
    private Integer star;

    @Schema(description = "消费金额")
    private BigDecimal price;

    @Schema(description = "是否包含攻略 (1:是, 0:否)")
    private Integer hasStrategy;

    @Schema(description = "评论摘要")
    private String commentShort;

    @Schema(description = "HBase RowKey")
    private String hbaseRowkey;
}
