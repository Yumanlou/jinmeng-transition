*******************************************************
* Green-credit proxy validation and bounded associations
* Source proxy: 1 - six energy-intensive industries'
* interest-expense share, 31 provinces, 2005-2022.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
capture log close

local root   "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data   "`root'/data"
local outdir "`root'/result/tables/0716_green_credit_proxy"
cap mkdir "`outdir'"
log using "`outdir'/policy_eval_green_credit_proxy_0716.log", text replace

capture which reghdfe
if _rc ssc install reghdfe, replace

import delimited "`data'/final_data.1.3.4_did_full_resource_v2_credit_greencredit_0716.csv", ///
    clear varnames(1) encoding(utf8)
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes "gtfp_level gml_index energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh windsolar_gen_sh"

quietly summarize green_credit_proxy if !missing(green_credit_proxy)
gen double green_credit_proxy_z = (green_credit_proxy - r(mean)) / r(sd)
gen double green_credit_proxy_z_x_resdep = green_credit_proxy_z * resdep_pre
gen double lag_gc_z = L.green_credit_proxy_z
gen double lag_gc_z_x_resdep = lag_gc_z * resdep_pre

tempname response assoc
postfile `response' str20 sample double b_coal se_coal p_coal ///
    b_res se_res p_res b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/green_credit_policy_response.dta", replace

foreach sample in full no2017 {
    local condition "!missing(green_credit_proxy)"
    if "`sample'" == "no2017" local condition "!missing(green_credit_proxy) & year != 2017"
    quietly reghdfe green_credit_proxy coalexp_post post_resdep ddd_resdep ///
        `controls' if `condition', absorb(province_id year) vce(cluster province_id)
    scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post] / _se[coalexp_post]))
    scalar p_res = 2 * ttail(e(df_r), abs(_b[post_resdep] / _se[post_resdep]))
    scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_resdep] / _se[ddd_resdep]))
    post `response' ("`sample'") ///
        (_b[coalexp_post]) (_se[coalexp_post]) (p_coal) ///
        (_b[post_resdep]) (_se[post_resdep]) (p_res) ///
        (_b[ddd_resdep]) (_se[ddd_resdep]) (p_ddd) (e(N)) (e(r2))
}
postclose `response'

postfile `assoc' str32 outcome str20 model double b_gc se_gc p_gc ///
    b_gc_resdep se_gc_resdep p_gc_resdep N r2 ///
    using "`outdir'/green_credit_associations.dta", replace

foreach y of local outcomes {
    quietly reghdfe `y' green_credit_proxy_z green_credit_proxy_z_x_resdep ///
        `controls' if !missing(green_credit_proxy), ///
        absorb(province_id year) vce(cluster province_id)
    scalar p_gc = 2 * ttail(e(df_r), abs(_b[green_credit_proxy_z] / _se[green_credit_proxy_z]))
    scalar p_gc_resdep = 2 * ttail(e(df_r), abs(_b[green_credit_proxy_z_x_resdep] / _se[green_credit_proxy_z_x_resdep]))
    post `assoc' ("`y'") ("contemporaneous") ///
        (_b[green_credit_proxy_z]) (_se[green_credit_proxy_z]) (p_gc) ///
        (_b[green_credit_proxy_z_x_resdep]) (_se[green_credit_proxy_z_x_resdep]) ///
        (p_gc_resdep) (e(N)) (e(r2))

    quietly reghdfe `y' green_credit_proxy_z green_credit_proxy_z_x_resdep ///
        `controls' if !missing(green_credit_proxy) & year != 2017, ///
        absorb(province_id year) vce(cluster province_id)
    scalar p_gc = 2 * ttail(e(df_r), abs(_b[green_credit_proxy_z] / _se[green_credit_proxy_z]))
    scalar p_gc_resdep = 2 * ttail(e(df_r), abs(_b[green_credit_proxy_z_x_resdep] / _se[green_credit_proxy_z_x_resdep]))
    post `assoc' ("`y'") ("contemp_no2017") ///
        (_b[green_credit_proxy_z]) (_se[green_credit_proxy_z]) (p_gc) ///
        (_b[green_credit_proxy_z_x_resdep]) (_se[green_credit_proxy_z_x_resdep]) ///
        (p_gc_resdep) (e(N)) (e(r2))

    quietly reghdfe `y' lag_gc_z lag_gc_z_x_resdep ///
        `controls' if !missing(lag_gc_z), ///
        absorb(province_id year) vce(cluster province_id)
    scalar p_gc = 2 * ttail(e(df_r), abs(_b[lag_gc_z] / _se[lag_gc_z]))
    scalar p_gc_resdep = 2 * ttail(e(df_r), abs(_b[lag_gc_z_x_resdep] / _se[lag_gc_z_x_resdep]))
    post `assoc' ("`y'") ("lagged") ///
        (_b[lag_gc_z]) (_se[lag_gc_z]) (p_gc) ///
        (_b[lag_gc_z_x_resdep]) (_se[lag_gc_z_x_resdep]) ///
        (p_gc_resdep) (e(N)) (e(r2))
}
postclose `assoc'

use "`outdir'/green_credit_policy_response.dta", clear
export delimited using "`outdir'/Table_0716_1_GreenCreditPolicyResponse.csv", replace

use "`outdir'/green_credit_associations.dta", clear
export delimited using "`outdir'/Table_0716_2_GreenCreditOutcomeAssociations.csv", replace

log close
