package com.nijika.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.nijika.entity.City;
import com.nijika.mapper.CityMapper;
import com.nijika.service.ICityService;
import org.springframework.stereotype.Service;

@Service
public class CityServiceImpl extends ServiceImpl<CityMapper, City> implements ICityService {
}
