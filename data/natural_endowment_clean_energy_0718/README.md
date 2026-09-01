# 风光自然禀赋与清洁电力代理变量

## 1. 模块目的

本模块将三个不同概念分开：

1. **风光自然禀赋**：由长期气象资源决定，是政策前给定条件。
2. **清洁电力实现基础**：由实际装机和发电形成，包含投资、并网和政策选择。
3. **清洁能源经济贡献**：应由增加值、就业、投资额和财政收益衡量；当前主面板没有这些直接数据。

因此，本模块中的发电量、装机、区位商和新增装机只能称为清洁电力物理产出、显性专业化或扩张强度，不能称为清洁能源产业增加值。

## 2. 自然禀赋来源

### 风能

- He, G. and Kammen, D. M. (2014), *Energy Policy* 74: 116--122。
- DOI: `10.1016/j.enpol.2014.07.003`
- 使用其表2报告的2001--2010年省级陆上风电平均容量因子及下限技术潜力。

### 太阳能

- He, G. and Kammen, D. M. (2016), *Renewable Energy* 85: 74--82。
- DOI: `10.1016/j.renene.2015.06.027`
- 使用其表4报告的2001--2010年省级固定式光伏平均容量因子及下限技术潜力。

论文将内蒙古拆分为东部和西部。本模块用各自技术潜在装机作为权重合并容量因子，并加总潜在装机和潜在发电量。

主回归应分别使用：

- `wind_resource_cf_z`：标准化风能资源容量因子。
- `solar_resource_cf_z`：标准化太阳能资源容量因子。

`natural_wind_solar_endowment` 是二者均值，只适合做综合指标稳健性。风电和光伏具有替代性，主模型不应只报告综合指数。

## 3. 清洁电力代理变量

### 清洁电力发电区位商

```text
clean_generation_lq_it
  = 本省风光发电占比_it / 全国风光发电占比_t
```

该指标衡量本省清洁电力生产相对全国的显性专业化程度，不是产业增加值。

### 清洁电力产出强度

```text
clean_generation_kwh_per_cny_gdp_it
  = 风光发电量_it / 地区GDP_it
```

主面板发电量单位为十亿千瓦时，GDP单位为亿元；脚本已换算为千瓦时/元GDP。

### 新增装机强度

```text
clean_capacity_addition_per_gdp_it
  = 风光新增装机_it / 地区GDP_it
```

新增装机统一由装机存量差分构造。负差分通常表示统计口径或来源切换，整条风光新增装机记录置为缺失，并由 `clean_capacity_addition_data_break_flag` 标记。

## 4. 覆盖与识别边界

- 自然禀赋：31省，常数型省级指标，可匹配2000--2023年全部744条面板记录。
- 风光发电代理：31省，主要覆盖2011--2023年。
- 风光装机代理：31省，主要覆盖2005--2023年，但早期年份不平衡。
- 2008--2011年清洁发电区位商只有1个省形成有效均值，`pre_clean_generation_lq_0811` 不能进入全国调节模型。
- 2013--2016年清洁发电区位商覆盖31省，`early_clean_generation_lq_1316` 只能解释政策后早期实现基础，不能称为政策前禀赋。

直接衡量地方经济贡献仍缺：

1. 风电和光伏产业增加值及其占GDP比重。
2. 风光制造、建设和运维就业及其占总就业比重。
3. 风光项目实际投资额及其占固定资产投资比重。
4. 风光产业地方税收、土地收益和国有资本收益。

在取得上述数据前，论文应使用“清洁电力生产专业化”“物理产出强度”或“扩张强度”，避免使用“清洁能源经济贡献”作为已观测变量名称。

## 5. 文件

- `natural_wind_solar_endowment_province.csv`：31省自然禀赋横截面。
- `clean_energy_proxy_panel_2000_2023.csv`：可并入回归的省份年度模块。
- `natural_clean_proxy_codebook.csv`：变量定义及解释边界。
- `natural_clean_proxy_coverage.csv`：覆盖报告。
- `natural_endowment_correlations.csv`：自然禀赋、早期清洁电力基础、煤炭暴露和资源依赖的省级相关系数。
- `source_metadata.json`：文献与数据出处。
- 项目主面板：`../final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv`。

## 6. 重建命令

```bash
/Users/yumanlou/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  code/build_natural_endowment_clean_energy_proxy_0718.py
```

构造脚本不会覆盖原主面板。
