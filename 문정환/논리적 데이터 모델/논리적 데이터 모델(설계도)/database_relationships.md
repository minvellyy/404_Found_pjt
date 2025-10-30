
### 관계(Relationship) 요약

이 테이블들이 어떻게 연결되는지(관계)가 중요해.

* `Influencer_Master` (1) : (N) `Campaign_Performance`
    * (한 명의 인플루언서는 여러 개의 성과를 낼 수 있다)
* `Campaign_Master` (1) : (N) `Campaign_Performance`
    * (하나의 캠페인에는 여러 인플루언서의 성과가 포함된다)
* `Product_Master` (1) : (N) `Campaign_Master`
    * (하나의 제품으로 여러 캠페인을 진행할 수 있다)

