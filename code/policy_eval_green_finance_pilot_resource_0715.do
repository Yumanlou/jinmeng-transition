*******************************************************
* File: policy_eval_green_finance_pilot_resource_0715.do
* Purpose:
*   Supplementary province-level test using the first-batch
*   2017 green-finance reform and innovation pilot zones.
*
* Identification warning:
*   The official pilots were cities/new areas within five
*   provinces. Province-level coding is an approximation and
*   pilot placement is not random. Results are supplementary.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root   "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data   "`root'/data"
local outdir "`root'/result/tables/0715_resource_dependence"

log using "`outdir'/policy_eval_green_finance_pilot_resource_0715.log", text replace

capture which reghdfe
if _rc ssc install reghdfe, replace
capture which outreg2
if _rc ssc install outreg2, replace

import delimited "`data'/final_data.1.3.4_did_full_resource_0715.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

label var gfr_did2017 "First-batch pilot province x post-2017"
label var post2017_resdep "Post-2017 x pre-policy resource dependence"
label var gfr_ddd_resdep "Pilot x post-2017 x resource dependence"

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh wind_gen_sh windsolar_gen_sh wind_cap_sh"
local outfile "`outdir'/Table_0715_3_GreenFinancePilot_ResourceDependence.xls"
cap erase "`outfile'"

tempname results
postfile `results' str32 outcome double b_pilot se_pilot p_pilot ///
    b_postres se_postres p_postres b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/green_finance_pilot_resource_results.dta", replace

local first 1
foreach y of local outcomes {
    quietly reghdfe `y' gfr_did2017 post2017_resdep gfr_ddd_resdep `controls' ///
        if !missing(resdep_pre), absorb(province_id year) vce(cluster province_id)

    scalar p_pilot = 2 * ttail(e(df_r), abs(_b[gfr_did2017] / _se[gfr_did2017]))
    scalar p_postres = 2 * ttail(e(df_r), abs(_b[post2017_resdep] / _se[post2017_resdep]))
    scalar p_ddd = 2 * ttail(e(df_r), abs(_b[gfr_ddd_resdep] / _se[gfr_ddd_resdep]))
    post `results' ("`y'") ///
        (_b[gfr_did2017]) (_se[gfr_did2017]) (p_pilot) ///
        (_b[post2017_resdep]) (_se[post2017_resdep]) (p_postres) ///
        (_b[gfr_ddd_resdep]) (_se[gfr_ddd_resdep]) (p_ddd) ///
        (e(N)) (e(r2))

    if `first' {
        outreg2 using "`outfile'", excel replace ctitle(`y') dec(4) ///
            keep(gfr_did2017 post2017_resdep gfr_ddd_resdep) ///
            addtext(Pilot coding, First-batch five provinces, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first 0
    }
    else {
        outreg2 using "`outfile'", excel append ctitle(`y') dec(4) ///
            keep(gfr_did2017 post2017_resdep gfr_ddd_resdep) ///
            addtext(Pilot coding, First-batch five provinces, Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}
postclose `results'

preserve
    use "`outdir'/green_finance_pilot_resource_results.dta", clear
    export delimited using "`outdir'/Table_0715_3_GreenFinancePilot_ResourceDependence_coefficients.csv", replace
restore

log close
