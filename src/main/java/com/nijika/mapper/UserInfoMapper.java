package com.nijika.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.nijika.entity.UserInfo;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserInfoMapper extends BaseMapper<UserInfo> {
}
