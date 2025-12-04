-- 1. 初始化数据库
DROP DATABASE IF EXISTS travel_db;
CREATE DATABASE IF NOT EXISTS travel_db DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;
USE travel_db;

--   ==
-- 2. 基础维表 (Dimension Tables)
--   ==

-- 表1：省份表
CREATE TABLE province (
  province_id   INT PRIMARY KEY AUTO_INCREMENT,
  province_name VARCHAR(50) NOT NULL UNIQUE COMMENT '省份名称，如陕西省、广东省',
  region        VARCHAR(50) NULL COMMENT '大区：华北、华东、西北等（可选）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='省份维表';

-- 表2：城市表
CREATE TABLE city (
  city_id     INT PRIMARY KEY AUTO_INCREMENT,
  city_name   VARCHAR(50) NOT NULL COMMENT '城市名称，如西安市',
  province_id INT NOT NULL COMMENT '所属省份',
  level       TINYINT NULL COMMENT '1直辖市,2省会,3地级市等，可选',
  lat         DOUBLE NULL COMMENT '纬度（可选）',
  lon         DOUBLE NULL COMMENT '经度（可选）',
  INDEX idx_city_name (city_name),
  CONSTRAINT fk_city_province FOREIGN KEY (province_id) REFERENCES province(province_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='城市维表';

-- 表3：景点表 (核心实体)
CREATE TABLE scenic_spot (
  scenic_id   INT PRIMARY KEY AUTO_INCREMENT,
  scenic_name VARCHAR(200) NOT NULL COMMENT '景点名称，如香港海洋公园',
  city_id     INT NOT NULL COMMENT '所属城市',
  category    VARCHAR(50) NULL COMMENT '景点类型：主题公园/自然风景/博物馆等',
  avg_price   DECIMAL(10,2) NULL COMMENT '大致人均价格或门票',
  avg_score   DECIMAL(3,2) NULL COMMENT '综合评分',
  review_count INT DEFAULT 0 COMMENT '评论总数',
  address     VARCHAR(255) NULL COMMENT '详细地址（可选）',
  INDEX idx_scenic_city (city_id),
  INDEX idx_scenic_name (scenic_name),
  CONSTRAINT fk_scenic_city FOREIGN KEY (city_id) REFERENCES city(city_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景点基础信息表';

-- 表4：用户信息表
CREATE TABLE user_info (
  user_id       BIGINT PRIMARY KEY AUTO_INCREMENT,
  nick_name     VARCHAR(100) NULL COMMENT '用户昵称',
  gender        CHAR(1) NULL COMMENT 'M/F，可选',
  age_range     VARCHAR(20) NULL COMMENT '年龄段，如18-25',
  city_id       INT NULL COMMENT '用户所在城市',
  register_date DATE NULL COMMENT '注册时间',
  CONSTRAINT fk_user_city FOREIGN KEY (city_id) REFERENCES city(city_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

--   ==
-- 3. 原始事实表 (Fact Table)
--   ==

-- 表5：评论事实表 (用于存储爬取的原始数据引用)
CREATE TABLE review_fact (
  review_id     BIGINT PRIMARY KEY AUTO_INCREMENT,
  scenic_id     INT NOT NULL COMMENT '关联景点',
  user_id       BIGINT NULL COMMENT '关联用户（可为空）',
  comment_time  DATETIME NOT NULL COMMENT '评论时间',
  star          TINYINT NOT NULL COMMENT '评分星级 1-5',
  price         DECIMAL(10,2) NULL COMMENT '人均价格/消费',
  has_strategy  TINYINT(1) DEFAULT 0 COMMENT '是否攻略/长游记 1是0否',
  comment_short VARCHAR(500) NULL COMMENT '评论摘要/前500字',
  hbase_rowkey  VARCHAR(200) NULL COMMENT '关联 HBase 详细数据的 RowKey',

  INDEX idx_review_scenic_time (scenic_id, comment_time),
  INDEX idx_review_user (user_id),
  INDEX idx_review_star (star),
  CONSTRAINT fk_review_scenic FOREIGN KEY (scenic_id) REFERENCES scenic_spot(scenic_id),
  CONSTRAINT fk_review_user   FOREIGN KEY (user_id)   REFERENCES user_info(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论事实表';

--   ==
-- 4. 分析结果表 (Analysis/ADS Tables)
--   ==

-- 表6：景点词云/热词统计表
CREATE TABLE scenic_word_cloud (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  scenic_id    INT NOT NULL COMMENT '关联景点ID',
  city_id      INT NOT NULL COMMENT '冗余城市ID，用于快速聚合',
  province_id  INT NOT NULL COMMENT '冗余省份ID，用于快速聚合',

  -- 时间维度
  stat_year    SMALLINT NULL COMMENT '统计年份，如2023，NULL代表累计',
  stat_month   TINYINT  NULL COMMENT '统计月份，1-12，NULL代表全年',

  -- 词频数据
  word         VARCHAR(50) NOT NULL COMMENT '分词关键词',
  frequency    INT NOT NULL COMMENT '总词频',
  doc_count    INT NOT NULL COMMENT '包含该词的评论篇数',
  sentiment    TINYINT DEFAULT 0 COMMENT '情感倾向：1正向 0中性 -1负向',
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '统计生成时间',

  -- 索引与外键
  INDEX idx_scenic_time_freq (scenic_id, stat_year, stat_month, frequency),
  INDEX idx_city_time_freq   (city_id,   stat_year, stat_month, frequency),
  INDEX idx_word             (word),

  CONSTRAINT fk_wc_scenic   FOREIGN KEY (scenic_id)   REFERENCES scenic_spot(scenic_id),
  CONSTRAINT fk_wc_city     FOREIGN KEY (city_id)     REFERENCES city(city_id),
  CONSTRAINT fk_wc_province FOREIGN KEY (province_id) REFERENCES province(province_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景点词云统计结果表';

-- 表7：景点六要素分析表 (雷达图数据)
CREATE TABLE scenic_aspect_analysis (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  scenic_id     INT NOT NULL COMMENT '关联景点ID',
  city_id       INT NOT NULL COMMENT '冗余城市ID',
  province_id   INT NOT NULL COMMENT '冗余省份ID',

  -- 时间维度
  stat_year     SMALLINT NULL COMMENT '统计年份',
  stat_month    TINYINT  NULL COMMENT '统计月份',

  -- 维度分析数据
  aspect_name   ENUM('食','住','行','游','购','娱') NOT NULL COMMENT '评价维度',
  score         DECIMAL(3,2) NOT NULL COMMENT '维度评分 (0-5)',
  comment_count INT NOT NULL COMMENT '参与分析的评论数',
  positive_ratio DECIMAL(5,2) NULL COMMENT '正向评论占比(%)',
  keywords      VARCHAR(255) NULL COMMENT '该维度的典型关键词',
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '统计生成时间',

  -- 索引与外键
  INDEX idx_scenic_aspect_time (scenic_id, aspect_name, stat_year, stat_month),
  INDEX idx_city_aspect_time   (city_id,   aspect_name, stat_year, stat_month),

  CONSTRAINT fk_saa_scenic   FOREIGN KEY (scenic_id)   REFERENCES scenic_spot(scenic_id),
  CONSTRAINT fk_saa_city     FOREIGN KEY (city_id)     REFERENCES city(city_id),
  CONSTRAINT fk_saa_province FOREIGN KEY (province_id) REFERENCES province(province_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景点六要素评分结果表';
