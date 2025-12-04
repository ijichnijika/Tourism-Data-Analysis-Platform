package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.ScenicWordCloud;
import com.nijika.mapper.ScenicWordCloudMapper;
import com.nijika.service.IScenicWordCloudService;
import org.springframework.stereotype.Service;

@Service
public class ScenicWordCloudServiceImpl extends ServiceImpl<ScenicWordCloudMapper, ScenicWordCloud>
        implements IScenicWordCloudService {
}
