*******************************************************
* File: policy_eval_coal_power_lockin_0716.do
* Purpose: Diagnose whether policy-pre coal-power build
* lock-in changes the 2012 policy response hierarchy.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local outdir  "`root'/result/tables/0716_coal_power_lockin"
cap mkdir "`root'/result/tables/0716_coal_power_lockin"

log using "`outdir'/policy_eval_coal_power_lockin_0716.log", text replace

capture which reghdfe
if _rc ssc install reghdfe, replace

import delimited "`data'/final_data.1.3.4_did_full_resource_coalpower_0716.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes2012 "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh gem_coal_new_capacity_mw"
local outcomes2016 "wind_gen_sh windsolar_gen_sh wind_cap_sh"
local dimensions "raw log vintage"

gen byte post2016_cp = year >= 2016
gen double coalexp_post16_cp = post2016_cp * coalexp_pre
foreach dim of local dimensions {
    gen double post16_cpbuild_`dim'_z = post2016_cp * cpbuild_`dim'_z
    gen double ddd16_cpbuild_`dim'_z = post2016_cp * coalexp_pre * cpbuild_`dim'_z
}

tempname results
postfile `results' str32 outcome str12 dimension int breakpoint double ///
    b_coal se_coal p_coal b_lock se_lock p_lock b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/coal_power_lockin_results.dta", replace

foreach dim of local dimensions {
    local postlock "post_cpbuild_`dim'_z"
    local triple "ddd_cpbuild_`dim'_z"

    foreach y of local outcomes2012 {
        quietly reghdfe `y' coalexp_post `postlock' `triple' `controls', ///
            absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post] / _se[coalexp_post]))
        scalar p_lock = 2 * ttail(e(df_r), abs(_b[`postlock'] / _se[`postlock']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[`triple'] / _se[`triple']))
        post `results' ("`y'") ("`dim'") (2012) ///
            (_b[coalexp_post]) (_se[coalexp_post]) (p_coal) ///
            (_b[`postlock']) (_se[`postlock']) (p_lock) ///
            (_b[`triple']) (_se[`triple']) (p_ddd) (e(N)) (e(r2))
    }

    local postlock16 "post16_cpbuild_`dim'_z"
    local triple16 "ddd16_cpbuild_`dim'_z"
    foreach y of local outcomes2016 {
        quietly reghdfe `y' coalexp_post16_cp `postlock16' `triple16' `controls', ///
            absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post16_cp] / _se[coalexp_post16_cp]))
        scalar p_lock = 2 * ttail(e(df_r), abs(_b[`postlock16'] / _se[`postlock16']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[`triple16'] / _se[`triple16']))
        post `results' ("`y'") ("`dim'") (2016) ///
            (_b[coalexp_post16_cp]) (_se[coalexp_post16_cp]) (p_coal) ///
            (_b[`postlock16']) (_se[`postlock16']) (p_lock) ///
            (_b[`triple16']) (_se[`triple16']) (p_ddd) (e(N)) (e(r2))
    }
}
postclose `results'

use "`outdir'/coal_power_lockin_results.dta", clear
export delimited using "`outdir'/Table_0716_CoalPowerLockin_DDD_coefficients.csv", replace

log close
