*******************************************************
* Resource-dependence v2 robustness: original three
* dimensions plus pre-policy coal-production dependence.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
capture log close

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local outdir  "`root'/result/tables/0716_resource_dependence_v2"
cap mkdir "`root'/result/tables/0716_resource_dependence_v2"
log using "`outdir'/policy_eval_resource_dependence_v2_0716.log", text replace

capture which reghdfe
if _rc ssc install reghdfe, replace
import delimited "`data'/final_data.1.3.4_did_full_resource_v2_0716.csv", ///
    clear varnames(1) encoding(utf8)
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes2012 "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh gem_coal_new_capacity_mw"
local outcomes2016 "wind_gen_sh windsolar_gen_sh wind_cap_sh"

gen byte post2016_v2 = year >= 2016
gen double coalexp_post16_v2 = post2016_v2 * coalexp_pre

tempname results
postfile `results' str32 outcome str12 indexdef int breakpoint double ///
    b_coal se_coal p_coal b_res se_res p_res b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/resource_dependence_v2_results.dta", replace

foreach idx in v2share v2log {
    gen double post16_resdep_`idx' = post2016_v2 * resdep_`idx'
    gen double ddd16_resdep_`idx' = post2016_v2 * coalexp_pre * resdep_`idx'
    foreach y of local outcomes2012 {
        quietly reghdfe `y' coalexp_post post_resdep_`idx' ddd_resdep_`idx' `controls' ///
            if !missing(resdep_`idx'), absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post] / _se[coalexp_post]))
        scalar p_res = 2 * ttail(e(df_r), abs(_b[post_resdep_`idx'] / _se[post_resdep_`idx']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_resdep_`idx'] / _se[ddd_resdep_`idx']))
        post `results' ("`y'") ("`idx'") (2012) ///
            (_b[coalexp_post]) (_se[coalexp_post]) (p_coal) ///
            (_b[post_resdep_`idx']) (_se[post_resdep_`idx']) (p_res) ///
            (_b[ddd_resdep_`idx']) (_se[ddd_resdep_`idx']) (p_ddd) (e(N)) (e(r2))
    }
    foreach y of local outcomes2016 {
        quietly reghdfe `y' coalexp_post16_v2 post16_resdep_`idx' ddd16_resdep_`idx' `controls' ///
            if !missing(resdep_`idx'), absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post16_v2] / _se[coalexp_post16_v2]))
        scalar p_res = 2 * ttail(e(df_r), abs(_b[post16_resdep_`idx'] / _se[post16_resdep_`idx']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd16_resdep_`idx'] / _se[ddd16_resdep_`idx']))
        post `results' ("`y'") ("`idx'") (2016) ///
            (_b[coalexp_post16_v2]) (_se[coalexp_post16_v2]) (p_coal) ///
            (_b[post16_resdep_`idx']) (_se[post16_resdep_`idx']) (p_res) ///
            (_b[ddd16_resdep_`idx']) (_se[ddd16_resdep_`idx']) (p_ddd) (e(N)) (e(r2))
    }
}
postclose `results'
use "`outdir'/resource_dependence_v2_results.dta", clear
export delimited using "`outdir'/Table_0716_ResourceDependenceV2_DDD_coefficients.csv", replace
log close
