# 相关数据续搜与整合状态（2026-07-16）

## 一、本轮新增的可用数据

### 0. 省级绿色信贷代理：高耗能行业利息支出占比

用户提供的工作簿覆盖 31 省、2005-2022 年。原始“计算结果”并不是正向绿色信贷水平，而是六大高耗能行业利息支出占规模以上工业企业利息支出的比例。本文按文献常见口径构造正向代理：

\[
GreenCredit_{it}=1-\frac{六大高耗能行业利息支出_{it}}{规模以上工业企业利息支出_{it}}.
\]

| 变量 | 构造 | 覆盖 |
|---|---|---|
| `green_credit_high_energy_interest_share` | 六大高耗能行业利息支出占比 | 31省，2005-2022年 |
| `green_credit_proxy` | 1－高耗能行业利息支出占比 | 31省，2005-2022年 |
| `green_credit_proxy_pct` | 正向代理乘以100 | 31省，2005-2022年 |
| `green_credit_interpolated_flag` | 2017年插值标记 | 31省，2017年 |
| `green_credit_proxy_x_resdep_pre` | 正向代理×政策前资源依赖 | 有绿色信贷代理的省年 |
| `green_credit_proxy_x_coalexp_pre` | 正向代理×政策前煤炭暴露 | 有绿色信贷代理的省年 |

工作簿中的 2021 年和 2022 年结果已经逐省用原始分行业表重新计算，最大差异小于 `10^-12`；2017 年由工作簿明确标记为插值年份，因此回归同时报告保留和剔除 2017 年的结果。该指标反映信贷资源从高耗能行业相对退出的工业融资结构，不等同于银行监管口径的省级绿色贷款余额。

### 1. 煤电资本锁定：新增煤电装机

来源为 Global Energy Monitor 的 Global Coal Plant Tracker 2026 年 1 月版中国分省汇总表，统计口径为 30MW 及以上煤电机组。原表覆盖中国内地 30 个省份，西藏未列示；合并时将西藏标记为来源表中的结构性零值，而不是缺失值插补。

| 变量 | 构造 | 覆盖 |
|---|---|---|
| `gem_coal_new_capacity_mw` | 当年新投运煤电装机 | 31省，2000-2023年 |
| `pre_gem_coal_additions_0011_mw` | 2000-2011年累计新增煤电装机 | 31省 |
| `pre_gem_coal_additions_0811_mw` | 2008-2011年累计新增煤电装机 | 31省 |
| `post_gem_coal_additions_1223_mw` | 2012-2023年累计新增煤电装机 | 31省 |
| `cpbuild_raw_z` | 政策前人均新增煤电装机标准化值 | 31省 |
| `cpbuild_log_z` | 上述人均值取对数后标准化 | 31省 |
| `cpbuild_vintage_z` | 2008-2011年新增煤电装机/2011年火电装机 | 31省 |

2000-2025 年省级新增量与 GEM 表内省级合计、全国年度合计均已进行双重校验。2000-2011 年内蒙古累计新增 49,750MW，山西为 37,261MW；2012-2023 年分别为 60,052MW 和 34,771MW。

KAPSARC 镜像中的旧版 GCPT 文件只有 605 条记录，且没有投运年和退役年，不能构造煤电资本锁定，本轮没有将其并入面板。

### 2. 煤炭生产依赖：分省原煤产量

Wind 中的各省统计局年度序列只有 6 省，不能组成全国面板。本轮改用 Wind EDB 的国家统计局分省原煤产量月度累计序列，以每年 12 月累计值构造年度产量，并统一换算为万吨。

| 变量 | 构造 | 覆盖 |
|---|---|---|
| `wind_raw_coal_output_10k_ton` | 当年12月原煤产量累计值 | 26省，545个省年 |
| `wind_raw_coal_output_national_share` | 本省原煤产量/全国原煤产量 | 26省 |
| `pre_raw_coal_output_share_0809` | 2008-2009年全国份额均值 | 26省完整 |
| `coal_production_share_z` | 政策前全国份额标准化值 | 26省 |
| `coal_production_dep_log_z` | 政策前人均原煤产量取对数后标准化 | 26省 |

天津、上海、广东、海南和西藏在 Wind 返回中没有分省原煤产量累计序列。由于 2010-2014 年存在统计序列断点，完整共同政策前窗口只能使用 2008-2009 年；2008-2011 年均值保留观测数标记，不作为主定义。

政策前 2008-2009 年，内蒙古原煤产量年均 53,450.23 万吨、全国份额 19.06%；山西分别为 60,150.53 万吨和 21.63%。

### 3. 一般信贷供给：省级人民币贷款、存款和贷存比

Wind EDB 可返回中国人民银行的省级金融机构人民币各项贷款余额和存款余额月度序列。本轮严格使用每年 12 月末值，不使用月均值或年内最后一个非缺失月。江苏的 PBoC 月度代码未出现在广义搜索首屏中，已通过代码 `M0059518`（贷款）和 `M0059509`（存款）定向补齐。

| 变量 | 构造 | 覆盖 |
|---|---|---|
| `wind_loan_balance_100m_cny` | 金融机构人民币各项贷款余额，年末值 | 31省，2003-2023年，651个省年 |
| `wind_deposit_balance_100m_cny` | 金融机构人民币各项存款余额，年末值 | 31省，2003-2023年，651个省年 |
| `wind_loan_deposit_ratio` | 贷款余额/存款余额 | 31省，2003-2023年 |
| `wind_loan_gdp_ratio` | 贷款余额/地区生产总值 | 31省，2003-2023年 |
| `pre_wind_loan_deposit_ratio_0811` | 2008-2011年贷存比均值 | 31省完整 |
| `pre_wind_loan_deposit_ratio_0811_z` | 政策前贷存比标准化值 | 31省完整 |
| `pre_wind_loan_gdp_ratio_0811_z` | 政策前贷款/GDP均值的标准化值 | 31省完整 |

这些变量衡量地方一般信贷供给和金融中介程度，可用作控制变量、异质性条件或附录稳健性变量；它们不是绿色贷款余额，不能替代绿色信贷强度。

## 二、资源依赖指标升级

在原有就业依赖、煤炭资产锁定和资源税依赖三个维度之外，新增煤炭生产依赖，形成两种四维指标：

- `resdep_v2share`：加入政策前原煤产量全国份额。
- `resdep_v2log`：加入政策前人均原煤产量对数。

新旧指标相关系数分别为 0.9814 和 0.9834，说明生产依赖与已有就业、资产和财政维度高度重合。煤炭生产维度适合作为替代定义和稳健性检验，不必取代原三维主指标。

新版 DDD 中，资源依赖三重交互对能源强度、煤炭终端强度、工业二氧化硫、工业固废和煤炭占比大多不显著，原主线结论没有被推翻。值得记录的是：

- 四维份额指标下，三重交互对当年新增煤电装机为 `-5205.97`（`p=0.0280`）；对后期风光发电占比为 `-0.1408`（`p=0.0552`）。
- 四维人均对数指标下，三重交互对当年新增煤电装机为 `-3987.76`（`p=0.0303`）；新能源结果不显著。

新增煤电装机是流量而非火电资本存量，上述结果只能说明高资源依赖地区的新增煤电节奏出现差异，不能据此认定既有火电体系已经退出。

## 三、仍未解决的数据缺口

### 0. 工具变量诊断

已使用2007—2011年各省六大高耗能行业融资权重与剔除本省后的全国行业融资变化，构造行业融资shift-share工具，并同时工具化绿色信贷代理及其与资源依赖的交互项。第一阶段联合F最高仅为2.9299，Kleibergen--Paap F介于0.0176和1.7325之间，属于明显弱工具；加之全国行业融资变化可能直接影响地方能耗和污染，该工具不能将绿色信贷相关结果升级为因果结论。

下一步首选银行网络shift-share。Wind已补齐五家大型银行2012—2022年绿色贷款余额、客户贷款总额和绿色贷款占比，当前仍缺2011年“省份×银行”网点数量或贷款份额。完整评估见 `output/green_credit_iv_assessment_0716.md`。

### 1. 银行披露口径的省级绿色贷款余额

基于工业利息费用的省级绿色信贷代理已经补齐，可以用于刻画高耗能行业在工业信贷资源中的相对份额及其条件相关性。现有主面板中的旧 `credit`、`bond`、`gf_index` 等列仍缺少原始工作簿、变量标签和构造公式，不应与新代理混用。

目前仍未获得全国可比、覆盖 2005-2022 年的银行监管口径省级绿色贷款余额。因而，新变量可以替代无来源的旧绿色信贷指数，但不能被命名为省级绿色贷款余额，也不宜单独承担绿色信贷政策的直接因果识别。

### 2. 煤炭专属财政收入

Wind 可得的是资源税或采矿业税收，采矿业还包括油气和金属矿业。未找到全国统一的煤炭行业税费/一般公共预算收入长面板，因此不能把现有采矿业税收命名为煤炭财政依赖。

### 3. 2012 年前电网、外送和消纳条件

现有输出电量从 2015 年起、风光利用小时从 2018 年起、弃风弃光率从 2020 年起。全国可比的 2012 年前跨省输电能力、外送电量和并网消纳能力仍缺，因此不能完整构造先验的电网承接条件。

### 4. 煤炭行业信贷和长期资本

省级一般贷款和贷存比已经补齐，但煤炭企业贷款余额、煤电项目长期贷款、地方银行对煤炭行业的资产暴露仍没有公开省级长面板。这类数据更可能需要银行贷款数据库、企业贷款匹配或监管口径数据。

## 四、当前建议的数据层级

| 层级 | 数据 | 用法 |
|---|---|---|
| 主指标 | 原三维资源依赖指数 | 主 DDD：就业、资产、资源税依赖 |
| 稳健性 | 四维资源依赖 v2、煤炭生产份额 | 替代资源依赖定义 |
| 锁定机制 | 政策前新增煤电装机、2011年火电装机占比 | 描述煤电资本锁定 |
| 金融控制 | 省级贷款余额、存款余额、贷存比 | 一般信贷供给控制或异质性 |
| 金融代理 | `green_credit_proxy` | 工业融资结构及其与资源依赖的条件相关性 |
| 工具变量探索 | 行业融资shift-share | 第一阶段过弱，不进入主因果结果 |
| 待补工具变量 | 银行网络shift-share | 银行年度冲击已得，仍缺政策前省份银行权重 |
| 后验机制 | 外送电量、利用小时、弃风弃光率 | 附录相关性和晋蒙案例 |
| 暂不进入 | 无来源的旧 `credit` / `gf_index` | 不再作为可追溯的绿色信贷变量 |

## 五、主要新增文件

- `data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_0716.csv`：当前最完整面板，744行、31省、2000-2023年。
- `data/green_credit/2005-2022年绿色信贷水平.XLSX`：归档的用户原始工作簿。
- `data/green_credit/green_credit_province_2005_2022.csv`：清洗后的31省绿色信贷代理。
- `data/green_credit/green_credit_metadata.json`：口径、工作簿哈希和核验信息。
- `data/green_credit_iv/green_credit_shiftshare_iv_2007_2022.csv`：行业融资shift-share候选工具。
- `data/wind_bank_green_loan_shocks/wind_major_bank_green_loan_shocks_2012_2022.csv`：大型银行绿色贷款占比冲击。
- `data/gem_coal_power_lockin/gem_china_coal_additions_2000_2025.csv`：GEM分省新增煤电装机。
- `data/wind_raw_coal_output/wind_raw_coal_output_dec_ytd_2000_2023.csv`：Wind分省原煤产量12月累计值。
- `data/wind_provincial_credit/wind_provincial_credit_2000_2023.csv`：PBoC省级贷款、存款和贷存比。
- `data/wind_provincial_credit/wind_provincial_credit_metadata.csv`：Wind代码、来源、频率和更新时间。
- `code/clean_gem_china_coal_additions.py`：GEM清洗和双重合计校验。
- `code/fetch_wind_raw_coal_output_ytd.py`：Wind原煤产量提取脚本。
- `code/fetch_wind_provincial_credit.py`：Wind一般信贷供给提取脚本。
- `code/clean_merge_green_credit_2005_2022.py`：绿色信贷工作簿清洗、核验和面板合并脚本。
- `code/build_green_credit_shiftshare_iv.py`：行业融资shift-share构造脚本。
- `code/green_credit_shiftshare_iv_0716.do`：第一阶段和2SLS诊断脚本。
- `code/fetch_wind_major_bank_green_loan_shocks.py`：Wind大型银行绿色贷款冲击提取脚本。
- `result/tables/0716_coal_power_lockin/Table_0716_CoalPowerLockin_DDD_coefficients.csv`：煤电锁定 DDD。
- `result/tables/0716_coal_production_dependence/Table_0716_CoalProductionDependence_DDD_coefficients.csv`：煤炭生产依赖 DDD。
- `result/tables/0716_resource_dependence_v2/Table_0716_ResourceDependenceV2_DDD_coefficients.csv`：四维资源依赖 DDD。
- `result/tables/0716_green_credit_proxy/Table_0716_1_GreenCreditPolicyResponse.csv`：绿色信贷代理的政策响应模型。
- `result/tables/0716_green_credit_proxy/Table_0716_2_GreenCreditOutcomeAssociations.csv`：绿色信贷代理与各层结果变量的条件相关模型。
- `output/green_credit_integration_0716.md`：绿色信贷数据审计、模型和结果说明。
- `result/tables/0716_green_credit_iv/Table_0716_GreenCredit_IV_Diagnostics.xlsx`：第一阶段、2SLS和候选工具评估。
- `output/green_credit_iv_assessment_0716.md`：工具变量构造、诊断和下一步数据要求。
