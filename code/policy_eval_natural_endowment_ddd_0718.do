*******************************************************
* Natural wind/solar endowment and late clean-power DDD
* The model replaces realized early capacity with
* pre-policy physical resource quality.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data"
local out  "`root'/result/tables/0718_natural_endowment"
cap mkdir "`root'/result/tables/0718_natural_endowment"
log using "`out'/policy_eval_natural_endowment_ddd_0718.log", text replace

capture which reghdfe
if _rc {
    di as error "Required command not installed: reghdfe"
    exit 199
}

import delimited ///
    "`data'/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_0718.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
* solar_gen_sh has too little pre-2016 support for this breakpoint and is not
* estimated here. The recalculated clean shares equal the wind-solar shares,
* so duplicate outcomes are also omitted from the regression table.
local outcomes "nontherm_gen_sh wind_gen_sh windsolar_gen_sh wind_cap_sh solar_cap_sh windsolar_cap_sh clean_generation_lq clean_generation_kwh_per_cny_gdp clean_capacity_addition_per_gdp"

capture drop post2016_natural coal_post2016_natural
gen byte post2016_natural = year >= 2016
gen double coal_post2016_natural = post2016_natural * coalexp_pre

tempname results
postfile `results' str16 endowment str48 outcome double ///
    b_coal se_coal p_coal b_endow se_endow p_endow b_ddd se_ddd p_ddd ///
    N r2 year_min year_max province_n using "`out'/natural_endowment_ddd_results.dta", replace

foreach index in wind solar combined {
    if "`index'" == "wind" local zvar "wind_resource_cf_z"
    if "`index'" == "solar" local zvar "solar_resource_cf_z"
    if "`index'" == "combined" local zvar "natural_wind_solar_endowment"

    capture drop post16_endow ddd_natural
    gen double post16_endow = post2016_natural * `zvar'
    gen double ddd_natural = post2016_natural * coalexp_pre * `zvar'

    foreach y of local outcomes {
        capture confirm variable `y'
        if _rc continue

        quietly reghdfe `y' coal_post2016_natural post16_endow ddd_natural `controls', ///
            absorb(province_id year) vce(cluster province_id)

        scalar p_coal = 2 * ttail(e(df_r), abs(_b[coal_post2016_natural] / _se[coal_post2016_natural]))
        scalar p_endow = 2 * ttail(e(df_r), abs(_b[post16_endow] / _se[post16_endow]))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_natural] / _se[ddd_natural]))
        quietly summarize year if e(sample), meanonly
        scalar ymin = r(min)
        scalar ymax = r(max)
        quietly levelsof province_id if e(sample), local(sample_provinces)
        local pn : word count `sample_provinces'

        post `results' ("`index'") ("`y'") ///
            (_b[coal_post2016_natural]) (_se[coal_post2016_natural]) (p_coal) ///
            (_b[post16_endow]) (_se[post16_endow]) (p_endow) ///
            (_b[ddd_natural]) (_se[ddd_natural]) (p_ddd) ///
            (e(N)) (e(r2)) (ymin) (ymax) (`pn')
    }
}
postclose `results'

preserve
    use "`out'/natural_endowment_ddd_results.dta", clear
    export delimited using "`out'/Table_0718_NaturalEndowment_DDD.csv", replace
restore

*******************************************************
* Cross-sectional diagnostics: natural resource quality
* versus realized early clean-power base and coal exposure.
*******************************************************

preserve
    keep if year == 2011
    keep province coalexp_pre wind_resource_cf_0110 solar_resource_cf_0110 ///
        natural_wind_solar_endowment pre_nontherm_cap early_wind_cap early_wind_gen ///
        resdep_pre
    export delimited using "`out'/Table_0718_NaturalEndowment_ProvinceCrossSection.csv", replace
    pwcorr coalexp_pre wind_resource_cf_0110 solar_resource_cf_0110 ///
        natural_wind_solar_endowment pre_nontherm_cap early_wind_cap early_wind_gen ///
        resdep_pre, obs sig
restore

log close
