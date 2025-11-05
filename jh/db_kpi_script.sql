CREATE DATABASE demo_db
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE demo_db;

-------

USE demo_db;
---
--- 인플루언서 테이블
CREATE TABLE influencers (
    influencer_id   INT AUTO_INCREMENT PRIMARY KEY,
    handle          VARCHAR(50)  NOT NULL UNIQUE,  -- @계정명
    platform        VARCHAR(20)  NOT NULL,         -- Instagram 등
    email           VARCHAR(100) NOT NULL UNIQUE,
    follower_count  INT          NOT NULL,
    avg_likes       INT          NOT NULL,
    avg_comments    INT          NOT NULL,
    niche           VARCHAR(50)  NOT NULL,         -- 뷰티, 패션 등
    quality_grade   CHAR(1)      NOT NULL,         -- A/B/C 등급
    join_date       DATE         NOT NULL
);

ALTER TABLE influencers
    ADD COLUMN influencer_name   VARCHAR(100) NULL,
    ADD COLUMN account_category  VARCHAR(50)  NULL,
    ADD COLUMN account_keywords  VARCHAR(200) NULL;


--- 제품 테이블---

CREATE TABLE products (
    product_id      INT AUTO_INCREMENT PRIMARY KEY,
    brand_name      VARCHAR(100) NOT NULL,
    product_name    VARCHAR(100) NOT NULL UNIQUE,
    category        VARCHAR(50)  NOT NULL,   -- 토너, 에센스, 쿠션 등
    price           INT          NOT NULL,
    skin_type       VARCHAR(50)  NOT NULL,   -- 건성, 지성, 민감성 등
    keyword_tag     VARCHAR(100) NOT NULL    -- 비타민C, 미백, 진정 등
);
ALTER TABLE products
    ADD COLUMN text_keyword   VARCHAR(200) NULL,
    ADD COLUMN visual_keyword VARCHAR(200) NULL,
    ADD COLUMN effect_keyword VARCHAR(200) NULL;


--- 캠페인 테이블 ---

CREATE TABLE campaigns (
    campaign_id     INT AUTO_INCREMENT PRIMARY KEY,
    campaign_name   VARCHAR(100) NOT NULL UNIQUE,   -- 캠페인명
    objective       VARCHAR(100) NOT NULL,          -- 목적 (인지도/전환/신제품런칭 등)
    start_date      DATE         NOT NULL,
    end_date        DATE         NOT NULL,
    total_budget    INT          NOT NULL           -- 캠페인 총 예산
);

--- 캠페인 활동/성과 테이블---

USE demo_db;

CREATE TABLE campaign_posts (
    post_id                INT NOT NULL AUTO_INCREMENT,
    campaign_id            INT NOT NULL,
    influencer_id          INT NOT NULL,
    product_id             INT NOT NULL,

    post_date              DATE NOT NULL,
    post_url               VARCHAR(200) NOT NULL,

    views                  INT NOT NULL,
    likes                  INT NOT NULL,
    comments               INT NOT NULL,
    saves                  INT NOT NULL,
    cost                   INT NOT NULL,

    engagement_rate        DECIMAL(6,2) NULL,
    save_share_ratio       DECIMAL(6,2) NULL,
    true_engagement_score  DECIMAL(8,2) NULL,
    comment_quality_score  DECIMAL(8,2) NULL,
    ctr_proxy              DECIMAL(6,2) NULL,

    PRIMARY KEY (post_id),

    CONSTRAINT fk_post_campaign
        FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),

    CONSTRAINT fk_post_influencer
        FOREIGN KEY (influencer_id) REFERENCES influencers(influencer_id),

    CONSTRAINT fk_post_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
)
ENGINE=InnoDB
DEFAULT CHARSET = utf8mb4;

USE demo_db;

DROP TABLE IF EXISTS campaign_posts;

CREATE TABLE campaign_posts (
    post_id                INT NOT NULL AUTO_INCREMENT,
    campaign_id            INT NOT NULL,
    influencer_id          INT NOT NULL,
    product_id             INT NOT NULL,
    post_date              DATE NOT NULL,
    post_url               VARCHAR(200) NOT NULL,
    views                  INT NOT NULL,
    likes                  INT NOT NULL,
    comments               INT NOT NULL,
    saves                  INT NOT NULL,
    cost                   INT NOT NULL,
    engagement_rate        DECIMAL(6,2) NULL,
    save_share_ratio       DECIMAL(6,2) NULL,
    true_engagement_score  DECIMAL(8,2) NULL,
    comment_quality_score  DECIMAL(8,2) NULL,
    ctr_proxy              DECIMAL(6,2) NULL,
    PRIMARY KEY (post_id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4;

ALTER TABLE campaign_posts
    ADD INDEX idx_cp_campaign (campaign_id),
    ADD CONSTRAINT fk_cp_campaign
        FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id);

ALTER TABLE campaign_posts
    ADD INDEX idx_cp_influencer (influencer_id),
    ADD CONSTRAINT fk_cp_influencer
        FOREIGN KEY (influencer_id) REFERENCES influencers(influencer_id);

ALTER TABLE campaign_posts
    ADD INDEX idx_cp_product (product_id),
    ADD CONSTRAINT fk_cp_product
        FOREIGN KEY (product_id) REFERENCES products(product_id);


USE demo_db;

--- 더미 데이터 생성 - 인플루언서 1000명 ---

USE demo_db;

SET @n := 0;

INSERT INTO influencers (
    influencer_name,
    handle,
    platform,
    account_category,
    account_keywords,
    niche,
    follower_count,
    avg_likes,
    avg_comments,
    quality_grade,
    email,
    join_date
)
SELECT
    CONCAT('인플루언서_', LPAD(n, 4, '0'))       AS influencer_name,
    CONCAT('influencer_', LPAD(n, 4, '0'))       AS handle,
    'Instagram'                                  AS platform,
    CASE 
        WHEN n % 3 = 0 THEN '뷰티전문'
        WHEN n % 3 = 1 THEN '뷰티·일상'
        ELSE '패션·뷰티'
    END                                          AS account_category,
    CONCAT('키워드_', LPAD(n, 4, '0'), ',뷰티,스킨케어') AS account_keywords,
    CONCAT('Beauty_Niche_', LPAD(n, 4, '0'))     AS niche,
    1000 + n * 10                                AS follower_count,
    100 + n * 2                                  AS avg_likes,
    20 + n                                       AS avg_comments,
    CASE
        WHEN n % 3 = 0 THEN 'A'
        WHEN n % 3 = 1 THEN 'B'
        ELSE 'C'
    END                                          AS quality_grade,
    CONCAT('influencer', n, '@example.com')      AS email,
    DATE_ADD(DATE '2023-01-01', INTERVAL n DAY)  AS join_date
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 1000
) AS seq;


--- 제품 100개 생성 ---

USE demo_db;

SET @n := 0;

INSERT INTO products (
    brand_name,
    product_name,
    category,
    price,
    skin_type,
    text_keyword,
    visual_keyword,
    effect_keyword,
    keyword_tag
)
SELECT
    CONCAT('Brand_', LPAD(n, 3, '0'))             AS brand_name,
    CONCAT('Product_', LPAD(n, 3, '0'))           AS product_name,
    CASE 
        WHEN n % 3 = 0 THEN 'Toner'
        WHEN n % 3 = 1 THEN 'Essence'
        ELSE 'Cushion'
    END                                           AS category,
    10000 + n * 500                               AS price,
    CASE 
        WHEN n % 3 = 0 THEN 'Dry'
        WHEN n % 3 = 1 THEN 'Oily'
        ELSE 'Sensitive'
    END                                           AS skin_type,
    CONCAT('text_kw_',   LPAD(n, 3, '0'))         AS text_keyword,
    CONCAT('visual_kw_', LPAD(n, 3, '0'))         AS visual_keyword,
    CONCAT('effect_kw_', LPAD(n, 3, '0'))         AS effect_keyword,
    CONCAT('kw_',        LPAD(n, 3, '0'))         AS keyword_tag
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 100
) AS seq;

--- 캠페인 30개 생성 ---

USE demo_db;
SET @n := 0;


INSERT INTO campaigns (
    campaign_name,
    objective,
    start_date,
    end_date,
    total_budget
)
SELECT
    CONCAT('Campaign_', LPAD(n, 2, '0'))        AS campaign_name,
    CASE 
        WHEN n % 3 = 0 THEN 'Awareness'
        WHEN n % 3 = 1 THEN 'Conversion'
        ELSE 'Launch'
    END                                         AS objective,
    DATE_ADD('2024-01-01', INTERVAL (n - 1) * 10 DAY)     AS start_date,
    DATE_ADD('2024-01-01', INTERVAL (n - 1) * 10 + 7 DAY) AS end_date,
    1000000 + n * 50000                         AS total_budget
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 30
) AS seq;

--- 포스팅(활동) 데이터 3000개 생성 ---

USE demo_db;
SET @n := 0;

INSERT INTO campaign_posts (
    campaign_id,
    influencer_id,
    product_id,
    post_date,
    post_url,
    views,
    likes,
    comments,
    saves,
    cost
)
SELECT
    ((n - 1) % 30) + 1              AS campaign_id,    -- 1~30 캠페인 순환
    ((n - 1) % 1000) + 1            AS influencer_id,  -- 1~1000 인플루언서 순환
    ((n - 1) % 100) + 1             AS product_id,     -- 1~100 제품 순환
    DATE_ADD('2024-02-01', INTERVAL n DAY) AS post_date,
    CONCAT('https://instagram.com/post/', n) AS post_url,
    1000 + n * 5                    AS views,
    100 + (n % 300)                 AS likes,
    10 + (n % 50)                   AS comments,
    5 + (n % 30)                    AS saves,
    50000 + (n % 40) * 1000         AS cost
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 3000
) AS seq;

SELECT 'influencers' AS table_name, COUNT(*) AS cnt FROM influencers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'campaigns', COUNT(*) FROM campaigns
UNION ALL
SELECT 'campaign_posts', COUNT(*) FROM campaign_posts;

--- csv 대신 쓸 쿼리 ---
-- products_for_app.sql

SELECT
    p.product_id        AS 제품ID,
    p.brand_name        AS 브랜드명,
    p.product_name      AS 제품명,
    p.category          AS 카테고리,
    p.price             AS 가격,
    p.text_keyword      AS 텍스트_키워드,
    p.visual_keyword    AS 시각_키워드,
    p.effect_keyword    AS 효과_키워드,
    p.keyword_tag       AS 통합_키워드
FROM products p;

-- influencers_for_app.sql

SELECT
    i.influencer_id     AS 인플루언서ID,
    i.influencer_name   AS 인플루언서명,
    i.handle            AS 계정핸들,
    i.platform          AS 플랫폼,
    i.account_category  AS 계정_카테고리,
    i.niche             AS 니치,
    i.follower_count    AS 팔로워수,
    i.avg_likes         AS 평균_좋아요,
    i.avg_comments      AS 평균_댓글,
    i.quality_grade     AS 품질등급,
    i.account_keywords  AS 계정_키워드,
    i.email             AS 이메일
FROM influencers i;


-- campaign_results_for_app.sql

SELECT cp.post_id
FROM campaign_posts cp
JOIN campaigns c ON cp.campaign_id = c.campaign_id
LIMIT 10;

SELECT
    cp.post_id,
    c.campaign_name,
    i.influencer_name,
    p.product_name
FROM campaign_posts cp
JOIN campaigns   c ON cp.campaign_id   = c.campaign_id
JOIN influencers i ON cp.influencer_id = i.influencer_id
JOIN products    p ON cp.product_id    = p.product_id
LIMIT 10;

SELECT
    cp.post_id            AS post_id,
    c.campaign_id         AS campaign_id,
    c.campaign_name       AS campaign_name,
    c.objective           AS campaign_objective,
    cp.influencer_id      AS influencer_id,
    i.influencer_name     AS influencer_name,
    i.handle              AS handle,
    i.platform            AS platform,
    i.follower_count      AS follower_count,
    i.quality_grade       AS influencer_grade,
    cp.product_id         AS product_id,
    p.brand_name          AS brand_name,
    p.product_name        AS product_name,
    p.category            AS product_category,
    cp.post_date          AS post_date,
    cp.post_url           AS post_url,
    cp.views              AS views,
    cp.likes              AS likes,
    cp.comments           AS comments,
    cp.saves              AS saves,
    cp.cost               AS cost
FROM campaign_posts cp
JOIN campaigns   c ON cp.campaign_id   = c.campaign_id
JOIN influencers i ON cp.influencer_id = i.influencer_id
JOIN products    p ON cp.product_id    = p.product_id;

SHOW TABLES;

DESCRIBE influencers;
SHOW COLUMNS FROM influencers;
SELECT * FROM influencers LIMIT 1;

-- 인플루언서들이 실제로 어떤 키워드를 가지고 있는지 확인
SELECT 
    influencer_name,
    account_keywords,
    niche
FROM influencers
LIMIT 10;

-- 제품들이 실제로 어떤 키워드를 가지고 있는지 확인
SELECT 
    product_name,
    text_keyword,
    visual_keyword
FROM products
LIMIT 10;