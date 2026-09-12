# 国赛数据源速查表(30+数据库)

> 整合自数模乐园 2026 年汇总,按类别分组。建模第一步先查数据,确认数据可获取性再定技术路线。

---

## 一、政府与官方数据(14 个)

| 数据源 | 网址 | 适用题型 | 说明 |
|--------|------|---------|------|
| 国家统计局 | https://data.stats.gov.cn/ | C/D | 人口、GDP、工业、农业等全口径年度/月度数据 |
| 美国政府开放数据 | https://data.gov/ | C/D | 美国各联邦机构公开数据集 |
| 自然资源部 | http://www.mnr.gov.cn/sj/ | A/C | 地理、矿产、海洋、土地利用 |
| 工信部 | http://www.miit.gov.cn/gxsj/index.html | C/D | 工业产值、通信、制造业数据 |
| 交通运输部 | https://www.mot.gov.cn/shuju/ | A/B/C | 公路/铁路/水运/航空运输数据 |
| 商务部 | http://www.mofcom.gov.cn/article/tongjiziliao/ | C/D | 进出口、消费、外资数据 |
| 国家气象科学数据中心 | http://data.cma.cn/ | A/D | 气温、降水、风速、辐射等气象数据 |
| 北京大学开放数据台 | https://opendata.pku.edu.cn/ | C/D | 学术开放数据集 |
| 中国票房数据 | https://www.endata.com.cn/BoxOffice/ | D | 影视票房、娱乐产业数据 |
| 世界数据大全(Knoema) | https://cn.knoema.com/atlas | C/D | 全球宏观指标可视化 |
| 世界人口统计 | https://www.ifreesite.com/population/ | C/D | 各国人口、出生率、死亡率 |
| 世界气象数据(WMO) | https://public.wmo.int/zh-hans | A/D | 全球气象观测与气候数据 |
| 中国互联网络信息中心(CNNIC) | https://www.cnnic.net.cn/ | C/D | 互联网普及率、网民规模 |
| 全国地理信息资源目录 | https://www.webmap.cn/ | A/B | 地理空间数据、行政区划 |

---

## 二、财经与经济数据(6 个)

| 数据源 | 网址 | 适用题型 | 说明 |
|--------|------|---------|------|
| 英为财情(Investing) | https://cn.investing.com/ | C/D | 股票、期货、外汇、债券实时与历史数据 |
| 东方财富网 | https://www.eastmoney.com/ | C/D | A股/港股/美股行情、基金、财经新闻 |
| 同花顺数据中心 | https://data.10jqka.com.cn/ | C/D | 股票财务数据、行业分析 |
| 中国人民银行统计司 | http://www.pbc.gov.cn/diaochatongjisi/116219/index.html | C/D | 货币供应、利率、信贷数据 |
| WIND 万得 | https://www.wind.com.cn/ | C/D | 金融终端,覆盖宏观经济/行业/公司(需付费) |
| 世界银行公开数据 | https://data.worldbank.org.cn/ | C/D | 全球发展指标,免费开放 |

---

## 三、综合数据平台(5 个)

| 数据源 | 网址 | 适用题型 | 说明 |
|--------|------|---------|------|
| CEIC 全球数据库 | https://www.ceicdata.com/zh-hans/countries | C/D | 195 个国家 400 万+时间序列 |
| GitHub Awesome Datasets | https://github.com/awesomedata/awesome-public-datasets | 全题型 | 开源数据集索引,按领域分类 |
| 搜数网 | http://www.soshoo.com/index.do | C/D | 中国统计年鉴数据检索 |
| 亚马逊 AWS 开放数据 | https://registry.opendata.aws/ | 全题型 | 大规模开放数据集(需 AWS 账号) |
| 世界经济数据(CEIC) | https://www.ceicdata.com/zh-hans | C/D | 全球经济指标时间序列 |

---

## 四、论文与文献(4 个)

| 数据源 | 网址 | 用途 |
|--------|------|------|
| 中国知网(CNKI) | http://www.cnki.net/ | 中文核心期刊、学位论文 |
| 万方数据 | http://www.wanfangdata.com.cn/ | 中文期刊、专利、标准 |
| 维普网 | http://www.cqvip.com/ | 中文科技期刊全文 |
| 百度文库 | https://wenku.baidu.com/ | 行业报告、教材资料 |

---

## 五、代码与算法社区(3 个)

| 平台 | 网址 | 用途 |
|------|------|------|
| CSDN | https://www.csdn.net/ | 中文技术博客、算法实现 |
| GitHub | https://github.com/ | 开源算法代码、竞赛方案 |
| MATLAB 中文社区 | https://www.mathworks.com/matlabcentral/ | MATLAB 工具箱、函数参考 |

---

## 六、数据获取实战技巧

### 6.1 关键词策略

1. **精准定位**:分析赛题→提炼核心关键词(如"城市交通流量数据")
2. **拓展关联词**:考虑衍生概念(如"交通拥堵数据""道路规划数据")
3. **中英双搜**:同一数据集中文搜不到时试英文关键词

### 6.2 数据获取优先级

```
1. 赛题附件直接提供(最优)
2. 政府官方网站(权威性高)
3. 专业数据库(CEIC/WIND/搜数网)
4. GitHub/Kaggle 开源数据集
5. 论文附录中的参考数据
6. 自行采集/模拟(最后手段,需说明合理性)
```

### 6.3 数据处理流水线

```
原始数据 → 缺失值处理(插值/删除) → 异常值检测(3σ/IQR)
        → 标准化/归一化 → 特征工程 → 建模输入
```

常用工具:Pandas(清洗) + Matplotlib/Seaborn(可视化) + Scikit-learn(预处理)

### 6.4 数据来源标注规范(论文中)

论文中必须标注数据来源,格式:
> 数据来源:国家统计局(http://data.stats.gov.cn/),访问日期:2026年X月X日。

---

## 七、与 v7 流程的集成

| v7 阶段 | 数据源使用场景 |
|---------|--------------|
| Step 1 题型识别 | 判断是否需要外部数据(D 数据型概率最高) |
| Step 2 建模 | 从上述数据源获取训练/验证数据,写入 `data/` 目录 |
| Step 4 论文 | 在论文中引用数据来源URL,增强可信度 |
| Step 5 门禁 | auto_check 验证数据来源标注完整性 |
