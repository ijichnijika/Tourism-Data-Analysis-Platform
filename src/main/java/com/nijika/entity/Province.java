package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("province")
@Schema(description = "省份信息实体")
public class Province {
    @TableId(value = "province_id", type = IdType.AUTO)
    @Schema(description = "省份ID")
    private Integer provinceId;

    @Schema(description = "省份名称")
    private String provinceName;

    @Schema(description = "所属大区")
    private String region;
}
