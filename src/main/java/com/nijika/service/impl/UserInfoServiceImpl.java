package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.UserInfo;
import com.nijika.mapper.UserInfoMapper;
import com.nijika.service.IUserInfoService;
import org.springframework.stereotype.Service;

@Service
public class UserInfoServiceImpl extends ServiceImpl<UserInfoMapper, UserInfo> implements IUserInfoService {
}
