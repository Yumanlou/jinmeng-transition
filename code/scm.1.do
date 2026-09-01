/***********************************************************************
  SCM_InnerMongolia_2023_FULL.do   (可独立运行的完整版)
  - 数据：final_data.1.3.4_did.dta
  - 方法：Synthetic Control (synth)
  - treated：内蒙古 province_id = 3
  - 政策起点：2023
  - donor pool：除 treated 外全部（包含山西）
  - 输出：
      1) SCM 路径图（Actual vs Synthetic）
      2) Gap 图（Actual - Synthetic）
      3) gap 回归（仅作方向性量化）并 outreg2 append 到 Excel

  你遇到过的坑都在这里兜底了：
  - 不再用 if donor==1 | treated（避免 r(101)）
  - keep() 输出的时间变量是 _time，不是 year（避免 r(111)）
  - keep() 输出混有 donor 权重行（_time 缺失），要先过滤（避免乱回归/潜在 r(503)）
***********************************************************************/

clear all
set more off
version 17.0

*======================================================================*
* 1) PATHS（按你最新路径）
*======================================================================*
global output_path "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/result/"
global datafile     "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2025/第五学期/论文/ESG/carbon_emission_finance/data/final_data.1.3.4_did.dta"

* Excel（追加输出）
local outfile3 "${output_path}Table_3_Robustness_Variables.xls"

*======================================================================*
* 2) SCM SETTINGS（按你当前设定）
*======================================================================*
local idvar   province_id
local timevar year

local treated_id 3
local tr_year    2023

* 建议用数据质量更稳定的窗口；你当前 synth 输出从 2005 开始，说明早期缺失较多
local t_start 2005
local t_end   2023
local pre_start 2005
local pre_end   2022

* outcome
local y "gtfp_level"

* predictors（保持精简；变量名需与你数据一致）
local X "ln_gdp sec_pctg coal_share_pctg urbanization_rate market_index"

* special 年份（必须在 pre 内且 treated 不缺失）
local lags "2013 2018 2021"

* 是否导出图片
local export_graphs 1

*======================================================================*
* 3) PACKAGES
*======================================================================*
cap which synth
if _rc ssc install synth, replace

cap which outreg2
if _rc ssc install outreg2, replace

*======================================================================*
* 4) LOAD + BASIC PREP
*======================================================================*
use "${datafile}", clear
xtset `idvar' `timevar'

* 如果有 industrial_so2，可生成 ln_so2（不影响本次 SCM）
capture confirm variable industrial_so2
if !_rc {
    capture drop ln_so2
    gen ln_so2 = ln(industrial_so2 + 1)
}

* 限定时间窗口（让 pre 更干净）
keep if inrange(`timevar', `t_start', `t_end')

*======================================================================*
* 5) PRE-PERIOD COMPLETENESS（强制"省级完整"，提高 synth 稳定性）
*    - 只在 pre(2005-2022) 检查 y 和 X 是否缺失
*    - 任何一个省在 pre 期缺一项，就整省剔除
*    - 不会特意删山西，只要它 pre 完整就会保留
*======================================================================*
tempvar ok
gen byte `ok' = 1

foreach v of local X {
    replace `ok' = 0 if inrange(`timevar', `pre_start', `pre_end') & missing(`v')
}
replace `ok' = 0 if inrange(`timevar', `pre_start', `pre_end') & missing(`y')

bys `idvar': egen keep_prov = min(`ok')

* treated 必须保留，否则直接退出
count if `idvar'==`treated_id' & keep_prov==1
if r(N)==0 {
    di as error "Treated unit (province_id=`treated_id') fails pre-period completeness for y/X in `pre_start'-`pre_end'."
    di as error "Fix: check missingness in treated or adjust t_start / predictors / special years."
    exit 459
}

keep if keep_prov==1
drop `ok' keep_prov

preserve

keep province_id province
bys province_id: keep if _n == 1   // ← 比 duplicates drop 更安全

sort province_id
gen _Co_Number = _n

list _Co_Number province_id province, sep(0)

restore

*======================================================================*
* 6) RUN SYNTH（关键：不写 if donor==1 | treated）
*======================================================================*
di ""
di "=============================================================="
di "Running SCM"
di "Treated: province_id=`treated_id' | Treatment year: `tr_year'"
di "Outcome: `y'"
di "Predictors: `X'"
di "Special years: `lags'"
di "Donor pool: all provinces except treated (INCLUDING Shanxi)"
di "=============================================================="
di ""

tempfile scm_keep
synth `y' `X', ///
    trunit(`treated_id') trperiod(`tr_year') ///
    unitvariable(`idvar') timevariable(`timevar') ///
    special(`y'(`lags')) ///
    keep("`scm_keep'") replace

*======================================================================*
* 7) POST-PROCESS KEEP OUTPUT
*    - keep() 输出含 donor 权重行：_time 缺失
*    - 时间变量名是 _time，不是 year
*======================================================================*
use "`scm_keep'", clear

* 7.1 只保留 treated 的时间序列行（_time 非缺失）
keep if !missing(_time)

* 7.2 统一时间变量名
rename _time year

* 7.3 检查关键变量存在
capture confirm variable _Y_treated
if _rc {
    di as error "ERROR: _Y_treated not found in keep output."
    exit 198
}
capture confirm variable _Y_synthetic
if _rc {
    di as error "ERROR: _Y_synthetic not found in keep output."
    exit 198
}

* 7.4 gap + post
capture drop gap_scm
gen gap_scm = _Y_treated - _Y_synthetic
gen post2023 = (year >= `tr_year')

*======================================================================*
* 8) GRAPHS
*======================================================================*
twoway ///
    (line _Y_treated year, lwidth(medthick)) ///
    (line _Y_synthetic year, lpattern(dash) lwidth(medthick)), ///
    xline(`tr_year', lpattern(shortdash)) ///
    title("SCM: Inner Mongolia (province_id=`treated_id')") ///
    subtitle("Outcome: `y' | Treatment starts `tr_year'") ///
    legend(order(1 "Actual" 2 "Synthetic")) ///
    ytitle("`y'") xtitle("Year")

if `export_graphs'==1 {
    graph export "${output_path}SCM_IM_`y'_path.png", replace width(2200)
}

twoway ///
    (line gap_scm year, lwidth(medthick)), ///
    xline(`tr_year', lpattern(shortdash)) ///
    yline(0, lpattern(dot)) ///
    title("SCM Gap (Actual - Synthetic): Inner Mongolia") ///
    subtitle("Outcome: `y'") ///
    ytitle("Gap") xtitle("Year")

if `export_graphs'==1 {
    graph export "${output_path}SCM_IM_`y'_gap.png", replace width(2200)
}

*======================================================================*
* 9) GAP REGRESSION（仅用于方向性量化 + 表格输出）
*======================================================================*
reg gap_scm post2023, vce(robust)

* append 到你的 Excel
outreg2 using "`outfile3'", excel append ctitle("SCM IM `y' (Post=`tr_year')") dec(4)

di ""
di "=============================================================="
di "DONE."
di "Excel appended: `outfile3'"
if `export_graphs'==1 {
    di "Graphs exported to: ${output_path}"
}
di "=============================================================="

/***********************************************************************
  10) PLACEBO-IN-SPACE (空间安慰剂)
  - 对 donor pool 中每个省 j != treated_id：
      假装 j 在 tr_year 被处理，跑同一套 synth
  - 统计指标：post2023 的平均 gap（你这里等价于 year==2023 的 gap）
  - 输出：
      (1) placebo 结果数据：placebo_space_results.dta
      (2) 排序图：Placebo_in_Space_IM.png
***********************************************************************/

di ""
di "=============================================================="
di "Running PLACEBO-IN-SPACE ..."
di "Outcome: `y' | Treatment year: `tr_year' | Pre: `pre_start'-`pre_end'"
di "=============================================================="
di ""

*------------------------------------------------------------*
* 10.1 先把"synth 实际使用的样本（筛后）"存起来，保证 placebo 和主结果一致
*      （非常关键：否则 _Co_Number/样本集合会漂移）
*------------------------------------------------------------*
tempfile base_for_placebo
preserve
    * 这里假设你已经在主代码里完成了：
    * keep if inrange(year, t_start, t_end)
    * 以及 keep if keep_prov==1 的省级完整性筛选
    * 所以当前内存中的数据就是 synth 的有效样本
    
    save "`base_for_placebo'", replace
restore

*------------------------------------------------------------*
* 10.2 取 donor pool 列表（基于筛后样本）
*------------------------------------------------------------*
use "`base_for_placebo'", clear

* donor：除内蒙古 treated 以外的所有省
preserve
    keep `idvar'
    duplicates drop `idvar', force
    levelsof `idvar' if `idvar' != `treated_id', local(placebo_units)
restore

di "Placebo units count = " : word count `placebo_units'

*------------------------------------------------------------*
* 10.3 建立结果存储文件
*------------------------------------------------------------*
tempname postfile_handle
tempfile placebo_results
postfile `postfile_handle' int placebo_id ///
    double gap2023 double pre_mspe using "`placebo_results'", replace

*------------------------------------------------------------*
* 10.4 循环跑 placebo synth
*------------------------------------------------------------*
foreach pid of local placebo_units {

    quietly use "`base_for_placebo'", clear

    * 对每个 placebo treated，跑 synth
    tempfile keep_one

    * 关键：synth 不要写 if donor==... 让它自动用"除 treated 外所有省"为 donor
    capture noisily synth `y' `X', ///
        trunit(`pid') trperiod(`tr_year') ///
        unitvariable(`idvar') timevariable(`timevar') ///
        special(`y'(`lags')) ///
        keep("`keep_one'") replace

    * 如果某个省因缺失/异常导致 synth 跑不动，跳过（不让整个循环死）
    if _rc {
        di as error "Placebo failed for province_id=`pid' (rc=" _rc "). Skipped."
        continue
    }

    * 读取 keep 输出，提取 treated 时间路径行（_time 非缺失）
    use "`keep_one'", clear
    keep if !missing(_time)
    rename _time year

    gen gap = _Y_treated - _Y_synthetic

    * post2023 平均 gap（你这里只有 2023 一年）
    quietly summarize gap if year==`tr_year'
    local g2023 = r(mean)

    * pre-period MSPE（衡量 pre 拟合质量；越小越好）
    gen gap2 = gap^2
    quietly summarize gap2 if inrange(year, `pre_start', `pre_end')
    local mspe = r(mean)

    post `postfile_handle' (`pid') (`g2023') (`mspe')
}

postclose `postfile_handle'

*------------------------------------------------------------*
* 10.5 整理 placebo 结果 + 把内蒙古主结果也加进去
*------------------------------------------------------------*
use "`placebo_results'", clear
rename placebo_id province_id

* 加入 treated（内蒙古）的 gap2023 和 pre_mspe
tempfile im_main_gap
preserve
    * 这里假设你在主 SCM 后处理时，内存里处理过的 treated 路径数据已经不在了
    * 所以重新从 base_for_placebo 里跑一次内蒙古的 synth（保证口径一致）
    use "`base_for_placebo'", clear
    tempfile keep_im
    synth `y' `X', ///
        trunit(`treated_id') trperiod(`tr_year') ///
        unitvariable(`idvar') timevariable(`timevar') ///
        special(`y'(`lags')) ///
        keep("`keep_im'") replace

    use "`keep_im'", clear
    keep if !missing(_time)
    rename _time year
    gen gap = _Y_treated - _Y_synthetic

    quietly summarize gap if year==`tr_year'
    local im_g2023 = r(mean)

    gen gap2 = gap^2
    quietly summarize gap2 if inrange(year, `pre_start', `pre_end')
    local im_mspe = r(mean)
restore

* 把内蒙古插入结果集
set obs `=_N+1'
replace province_id = `treated_id' in L
replace gap2023     = `im_g2023'   in L
replace pre_mspe    = `im_mspe'    in L

gen treated_flag = (province_id==`treated_id')

* 为了避免"拟合很差的 placebo"干扰比较，常见做法是做 MSPE ratio 过滤
* 你也可以先不滤，只画全体；下面给一个可选过滤阈值
* local mspe_cut = 10
* keep if pre_mspe < `mspe_cut'

* 保存结果
save "${output_path}placebo_space_results.dta", replace

*------------------------------------------------------------*
* 10.6 生成排序图（内蒙古 vs placebo）
*------------------------------------------------------------*
gsort -gap2023
gen rank = _n

twoway ///
    (scatter gap2023 rank if treated_flag==0, msize(small)) ///
    (scatter gap2023 rank if treated_flag==1, msize(large)), ///
    yline(0, lpattern(dot)) ///
    title("Placebo-in-Space: Post-`tr_year' Gap Distribution") ///
    subtitle("Outcome: `y' | Marker=Inner Mongolia (treated)") ///
    ytitle("Gap in `tr_year' (Actual - Synthetic)") ///
    xtitle("Placebo provinces ranked by gap") ///
    legend(order(1 "Placebo provinces" 2 "Inner Mongolia"))

graph export "${output_path}Placebo_in_Space_IM_`y'.png", replace width(2200)

*------------------------------------------------------------*
* 10.7 给你一个"百分位"读数（论文很有用）
*------------------------------------------------------------*
summ gap2023 if treated_flag==0, detail
local p90 = r(p90)
local p95 = r(p95)
local p99 = r(p99)

di ""
di "=============================================================="
di "Placebo summary (gap2023):"
di "  Inner Mongolia gap2023 = " %9.4f `im_g2023'
di "  Placebo p90 = " %9.4f `p90' " | p95 = " %9.4f `p95' " | p99 = " %9.4f `p99'
di "Saved:"
di "  ${output_path}placebo_space_results.dta"
di "  ${output_path}Placebo_in_Space_IM_`y'.png"
di "=============================================================="
