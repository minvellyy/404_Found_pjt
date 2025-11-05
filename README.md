```
CREATE DATABASE dalba_seeding_db
```

주현 sql문
```
-- --------------------------------------------------
-- 1. 데이터베이스 선택
-- --------------------------------------------------
USE dalba_seeding_db;

-- --------------------------------------------------
-- 2. (안전장치) 기존 테이블 삭제 (외래 키 제약조건 임시 해제)
-- --------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS campaign_posts;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS influencers;
SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------
-- 3. 테이블 생성 (influencers, products, campaigns)
-- --------------------------------------------------

-- 인플루언서 테이블
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

-- 제품 테이블
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

-- 캠페인 테이블
CREATE TABLE campaigns (
    campaign_id     INT AUTO_INCREMENT PRIMARY KEY,
    campaign_name   VARCHAR(100) NOT NULL UNIQUE,   -- 캠페인명
    objective       VARCHAR(100) NOT NULL,          -- 목적 (인지도/전환/신제품런칭 등)
    start_date      DATE         NOT NULL,
    end_date        DATE         NOT NULL,
    total_budget    INT          NOT NULL          -- 캠페인 총 예산
);

-- --------------------------------------------------
-- 4. 테이블 생성 (campaign_posts) 및 외래 키 연결
-- --------------------------------------------------
CREATE TABLE campaign_posts (
    post_id                 INT NOT NULL AUTO_INCREMENT,
    campaign_id             INT NOT NULL,
    influencer_id           INT NOT NULL,
    product_id              INT NOT NULL,
    post_date               DATE NOT NULL,
    post_url                VARCHAR(200) NOT NULL,
    views                   INT NOT NULL,
    likes                   INT NOT NULL,
    comments                INT NOT NULL,
    saves                   INT NOT NULL,
    cost                    INT NOT NULL,
    engagement_rate         DECIMAL(6,2) NULL,
    save_share_ratio        DECIMAL(6,2) NULL,
    true_engagement_score   DECIMAL(8,2) NULL,
    comment_quality_score   DECIMAL(8,2) NULL,
    ctr_proxy               DECIMAL(6,2) NULL,
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

-- --------------------------------------------------
-- 5. 더미 데이터 생성 (총 4130개 레코드)
-- --------------------------------------------------

-- 인플루언서 1000명 생성
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
    CONCAT('인플루언서_', LPAD(n, 4, '0'))     AS influencer_name,
    CONCAT('influencer_', LPAD(n, 4, '0'))     AS handle,
    'Instagram'                                AS platform,
    CASE 
        WHEN n % 3 = 0 THEN '뷰티전문'
        WHEN n % 3 = 1 THEN '뷰티·일상'
        ELSE '패션·뷰티'
    END                                        AS account_category,
    CONCAT('키워드_', LPAD(n, 4, '0'), ',뷰티,스킨케어') AS account_keywords,
    CONCAT('Beauty_Niche_', LPAD(n, 4, '0'))   AS niche,
    1000 + n * 10                              AS follower_count,
    100 + n * 2                                AS avg_likes,
    20 + n                                     AS avg_comments,
    CASE
        WHEN n % 3 = 0 THEN 'A'
        WHEN n % 3 = 1 THEN 'B'
        ELSE 'C'
    END                                        AS quality_grade,
    CONCAT('influencer', n, '@example.com')    AS email,
    DATE_ADD(DATE '2023-01-01', INTERVAL n DAY)  AS join_date
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 1000
) AS seq;

-- 제품 100개 생성
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
    CONCAT('Brand_', LPAD(n, 3, '0'))           AS brand_name,
    CONCAT('Product_', LPAD(n, 3, '0'))         AS product_name,
    CASE 
        WHEN n % 3 = 0 THEN 'Toner'
        WHEN n % 3 = 1 THEN 'Essence'
        ELSE 'Cushion'
    END                                         AS category,
    10000 + n * 500                             AS price,
    CASE 
        WHEN n % 3 = 0 THEN 'Dry'
        WHEN n % 3 = 1 THEN 'Oily'
        ELSE 'Sensitive'
    END                                         AS skin_type,
    CONCAT('text_kw_',   LPAD(n, 3, '0'))       AS text_keyword,
    CONCAT('visual_kw_', LPAD(n, 3, '0'))       AS visual_keyword,
    CONCAT('effect_kw_', LPAD(n, 3, '0'))       AS effect_keyword,
    CONCAT('kw_',        LPAD(n, 3, '0'))       AS keyword_tag
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 100
) AS seq;

-- 캠페인 30개 생성
SET @n := 0;
INSERT INTO campaigns (
    campaign_name,
    objective,
    start_date,
    end_date,
    total_budget
)
SELECT
    CONCAT('Campaign_', LPAD(n, 2, '0'))      AS campaign_name,
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

-- 포스팅(활동) 데이터 3000개 생성
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
    ((n - 1) % 30) + 1                AS campaign_id,    -- 1~30 캠페인 순환
    ((n - 1) % 1000) + 1              AS influencer_id,  -- 1~1000 인플루언서 순환
    ((n - 1) % 100) + 1               AS product_id,     -- 1~100 제품 순환
    DATE_ADD('2024-02-01', INTERVAL n DAY) AS post_date,
    CONCAT('https://instagram.com/post/', n) AS post_url,
    1000 + n * 5                      AS views,
    100 + (n % 300)                   AS likes,
    10 + (n % 50)                     AS comments,
    5 + (n % 30)                      AS saves,
    50000 + (n % 40) * 1000           AS cost
FROM (
    SELECT @n := @n + 1 AS n
    FROM information_schema.tables
    LIMIT 3000
) AS seq;

-- --------------------------------------------------
-- 6. 데이터 생성 확인
-- --------------------------------------------------
SELECT 'influencers' AS table_name, COUNT(*) AS cnt FROM influencers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'campaigns', COUNT(*) FROM campaigns
UNION ALL
SELECT 'campaign_posts', COUNT(*) FROM campaign_posts;
```

민지 sql
```
USE dalba_seeding_db;

CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category VARCHAR(100),
  description TEXT,
  ingredients TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO products (name, category, description, ingredients) VALUES
('Hydra Calm Cream', 'Skincare', 'Light moisturizing cream for daily use with non-greasy finish.', 'Aqua; Glycerin; Hyaluronic Acid; Centella Asiatica; Panthenol'),
('Fresh Citrus Toner', 'Skincare', 'Refreshing vitamin C toner that gently exfoliates and brightens.', 'Water; Ascorbic Acid; Niacinamide; Citrus Extract; Allantoin'),
('Deep Moist Serum', 'Skincare', 'Intense hydration serum that plumps and smooths fine lines.', 'Hyaluronic Acid (3 weights); Betaine; Panthenol; Trehalose'),
('Matte Balance Lotion', 'Skincare', 'Oil-control lotion designed for oily/combination skin types.', 'Niacinamide; Zinc PCA; Silica; Green Tea; Allantoin'),
('Herbal Repair Cream', 'Skincare', 'Restorative cream for stressed skin featuring herbal extracts.', 'Centella; Madecassoside; Mugwort; Shea Butter; Ceramide NP'),
('Rose Glow Mist', 'Skincare', 'Dewy face mist for an instant glow and hydration boost.', 'Rosa Damascena Water; Aloe; Beta-Glucan; Glycerin'),
('Ocean Energy Gel', 'Skincare', 'Cooling gel moisturizer with marine minerals for fatigued skin.', 'Sea Water; Algae Extract; Menthol; Panthenol'),
('Lavender Night Mask', 'Skincare', 'Overnight sleeping mask to soothe and nourish skin.', 'Lavender Oil; Squalane; Ceramide; Sodium PCA'),
('Green Tea Cleanser', 'Skincare', 'Daily gel cleanser that removes impurities without stripping.', 'Green Tea Extract; Cocamidopropyl Betaine; Glycerin'),
('Vanilla Shea Body Butter', 'Bodycare', 'Rich body butter for very dry skin with long-lasting moisture.', 'Shea Butter; Cocoa Butter; Jojoba Oil; Vanilla'),
('Cica Soothing Ampoule', 'Skincare', 'Fast-calming ampoule for redness and sensitivity.', 'Centella Complex; Madecassoside; Panthenol; Beta-Glucan'),
('Aqua Shield Sunscreen SPF50+', 'Skincare', 'Lightweight, water-based sunscreen with broad spectrum protection.', 'Uvinul A Plus; Tinosorb S; Niacinamide; Vitamin E'),
('Ceramide Barrier Cream', 'Skincare', 'Barrier-repair cream for compromised and dry skin.', 'Ceramide NP; Cholesterol; Free Fatty Acids; Squalane'),
('Pore Clear Clay Mask', 'Skincare', 'Weekly clay mask to absorb sebum and refine pores.', 'Kaolin; Bentonite; Charcoal; Tea Tree'),
('Brightening Spot Serum', 'Skincare', 'Dark spot corrector targeting uneven tone.', 'Tranexamic Acid; Arbutin; Licorice; Niacinamide'),
('Cooling Aloe Gel', 'Bodycare', 'Multi-purpose aloe gel for face and body.', 'Aloe Vera; Allantoin; Panthenol'),
('Silky Hand Cream', 'Bodycare', 'Non-sticky hand cream with quick absorption.', 'Shea Butter; Sweet Almond Oil; Vitamin E'),
('Coconut Hair Mask', 'Haircare', 'Deep conditioning mask for damaged hair.', 'Coconut Oil; Hydrolyzed Keratin; Argan Oil'),
('Mint Scalp Tonic', 'Haircare', 'Refreshing scalp tonic for oil control.', 'Menthol; Salicylic Acid; Niacinamide'),
('Volumizing Dry Shampoo', 'Haircare', 'Instant refresh and volume between washes.', 'Rice Starch; Silica; Fragrance'),
('Soft Cotton EDT', 'Fragrance', 'Clean and soft fragrance with cotton musk.', 'Ethanol; Perfume; Musk Accord'),
('Citrus Wood EDT', 'Fragrance', 'Bright citrus opening with a woody base.', 'Ethanol; Perfume; Citrus Accord; Cedarwood'),
('Blooming Rose Mist', 'Skincare', 'Fine rose mist to refresh makeup and skin.', 'Rose Water; Glycerin; Betaine'),
('Tea Tree Blemish Toner', 'Skincare', 'Clarifying toner for breakout-prone skin.', 'Tea Tree; Salicylic Acid; Zinc PCA'),
('Hyaluron Bounce Cream', 'Skincare', 'Bouncy gel-cream with multi-weight hyaluron.', 'Hyaluronic Acid; Panthenol; Squalane'),
('Chamomile Calming Cream', 'Skincare', 'Comfort cream to reduce irritation and heat.', 'Chamomile; Bisabolol; Allantoin'),
('Berry Peeling Pads', 'Skincare', 'Pre-soaked pads for gentle daily exfoliation.', 'Lactic Acid; PHA; Berry Extract'),
('Vitamin Eye Bright Cream', 'Skincare', 'Eye cream for dark circles and dullness.', 'Niacinamide; Vitamin C; Caffeine'),
('Sheer Lip Balm', 'Makeup', 'Hydrating tinted balm with natural finish.', 'Beeswax; Shea Butter; Jojoba Oil'),
('Moist Cushion Foundation', 'Makeup', 'Dewy cushion with skincare benefits.', 'Hyaluronic Acid; Niacinamide; SPF Filters'),
('Matte Fixing Powder', 'Makeup', 'Translucent powder to set makeup and control shine.', 'Silica; Mica; Dimethicone');
```
