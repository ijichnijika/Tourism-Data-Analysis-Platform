package com.nijika.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import java.time.LocalDate;

@Data
@TableName("user_info")
@Schema(description = "用户信息实体")
public class UserInfo {
    @TableId(value = "user_id", type = IdType.AUTO)
    @Schema(description = "用户ID")
    private Long userId;

    @Schema(description = "用户昵称")
    private String nickName;

    @Schema(description = "性别")
    private String gender;

    @Schema(description = "年龄段")
    private String ageRange;

    @Schema(description = "所在城市ID")
    private Integer cityId;

    @Schema(description = "注册日期")
    private LocalDate registerDate;
}
