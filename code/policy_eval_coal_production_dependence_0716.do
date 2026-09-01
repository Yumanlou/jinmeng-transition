*******************************************************
* File: policy_eval_coal_production_dependence_0716.do
* Purpose: Test pre-policy coal-production dependence
* using the common 2008-2009 December-YTD window.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local outdir  "`root'/result/tables/0716_coal_production_dependence"
cap mkdir "`root'/result/tables/0716_coal_production_dependence"

log using "`outdir'/policy_eval_coal_production_dependence_0716.log", text replace
capture which reghdfe
if _rc ssc install reghdfe, replace

import delimited "`data'/final_data.1.3.4_did_full_resource_coalpower_coalprod_0716.csv", ///
    clear varnames(1) encoding(utf8)
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes2012 "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh gem_coal_new_capacity_mw"
local outcomes2016 "wind_gen_sh windsolar_gen_sh wind_cap_sh"

gen byte post2016_prod = year >= 2016
gen double coalexp_post16_prod = post2016_prod * coalexp_pre

tempname results
postfile `results' str32 outcome str12 dimension int breakpoint double ///
    b_coal se_coal p_coal b_dep se_dep p_dep b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/coal_production_dependence_results.dta", replace

foreach dim in dep_log share {
    local prevar "coal_production_`dim'_z"
    local postvar "post_coal_production_`dim'_z"
    local triple "ddd_coal_production_`dim'_z"

    gen double post16_`dim'_z = post2016_prod * `prevar'
    gen double ddd16_`dim'_z = post2016_prod * coalexp_pre * `prevar'

    foreach y of local outcomes2012 {
        quietly reghdfe `y' coalexp_post `postvar' `triple' `controls' ///
            if !missing(`prevar'), absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post] / _se[coalexp_post]))
        scalar p_dep = 2 * ttail(e(df_r), abs(_b[`postvar'] / _se[`postvar']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[`triple'] / _se[`triple']))
        post `results' ("`y'") ("`dim'") (2012) ///
            (_b[coalexp_post]) (_se[coalexp_post]) (p_coal) ///
            (_b[`postvar']) (_se[`postvar']) (p_dep) ///
            (_b[`triple']) (_se[`triple']) (p_ddd) (e(N)) (e(r2))
    }

    foreach y of local outcomes2016 {
        quietly reghdfe `y' coalexp_post16_prod post16_`dim'_z ddd16_`dim'_z `controls' ///
            if !missing(`prevar'), absorb(province_id year) vce(cluster province_id)
        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post16_prod] / _se[coalexp_post16_prod]))
        scalar p_dep = 2 * ttail(e(df_r), abs(_b[post16_`dim'_z] / _se[post16_`dim'_z]))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd16_`dim'_z] / _se[ddd16_`dim'_z]))
        post `results' ("`y'") ("`dim'") (2016) ///
            (_b[coalexp_post16_prod]) (_se[coalexp_post16_prod]) (p_coal) ///
            (_b[post16_`dim'_z]) (_se[post16_`dim'_z]) (p_dep) ///
            (_b[ddd16_`dim'_z]) (_se[ddd16_`dim'_z]) (p_ddd) (e(N)) (e(r2))
    }
}
postclose `results'

use "`outdir'/coal_production_dependence_results.dta", clear
export delimited using "`outdir'/Table_0716_CoalProductionDependence_DDD_coefficients.csv", replace
log close
