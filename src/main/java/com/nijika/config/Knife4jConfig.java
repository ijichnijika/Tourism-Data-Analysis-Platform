package com.nijika.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springdoc.core.models.GroupedOpenApi;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class Knife4jConfig {

    @Bean
    public GroupedOpenApi publicApi() {
        return GroupedOpenApi.builder()
                .group("tourism-analysis") // 分组名称
                .pathsToMatch("/api/**")   // 只扫描 /api/ 开头的接口
                .packagesToScan("com.nijika.controller") // 核心：指定 Controller 所在包
                .build();
    }

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("分布式旅游大数据分析平台 API")
                        .version("1.0")
                        .description("基于 Spring Boot 3 + Vue 3 的后端接口文档"));
    }
}