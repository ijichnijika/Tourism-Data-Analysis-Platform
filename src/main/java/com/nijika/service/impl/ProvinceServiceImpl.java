package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.Province;
import com.nijika.mapper.ProvinceMapper;
import com.nijika.service.IProvinceService;
import org.springframework.stereotype.Service;

@Service
public class ProvinceServiceImpl extends ServiceImpl<ProvinceMapper, Province> implements IProvinceService {
}
