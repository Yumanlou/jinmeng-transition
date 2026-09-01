*******************************************************
* Trend robustness: replace province fixed trends
* with treatment-intensity-specific trends, combined
* with short-window restrictions.
*
* 0820 v2: drop the pre_year specification whose
* construction is collinear with absorb(year).
* Use c.coalexp_pre#c.year as the recommended spec.
* Add short-window versions (year<=2012, year<=2015)
* so the policy effect is identified off the early
* post-period before supply-side reform and before
* differential trends can cumulate much.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv"
local out  "`root'/result/tables/0820_trend_robustness"

capture mkdir "`out'"
log using "`out'/policy_eval_trend_robustness_0820.log", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required"
    exit 499
}

import delimited using "`data'", clear varnames(1) encoding(utf8)
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
gen byte post12 = year >= 2012
gen double did_coal = post12 * coalexp_pre

* Standardized treatment intensity (for numeric-stability checks)
egen double z_coalexp = std(coalexp_pre)

local core_outcomes ///
    "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5"

tempname results
postfile `results' str30 outcome str40 specification str32 term ///
    double b se p N r2 year_min year_max ///
    using "`out'/trend_robustness_results.dta", replace

*******************************************************
* Specs: 6 columns
*   (1) baseline (no trend)
*   (2) province linear trend (0726 reference)
*   (3) treatintensity x year (recommended)
*   (4) baseline  short window (year<=2015)
*   (5) province linear trend short window
*   (6) treatintensity x year short window
* then add earliest-window (year<=2012) variants
*   (7) baseline  early window
*   (8) province linear trend early window
*   (9) treatintensity x year early window
*******************************************************

foreach y of local core_outcomes {

    * === Full sample ===
    capture quietly reghdfe `y' did_coal `controls', ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("1_baseline") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.year#i.province_id, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("2_province_linear_trend") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.coalexp_pre#c.year, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("3_treatintensity_x_year") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    * === Short window (year<=2015) ===
    capture quietly reghdfe `y' did_coal `controls' if year <= 2015, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("4_baseline_thru2015") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.year#i.province_id ///
        if year <= 2015, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("5_province_trend_thru2015") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.coalexp_pre#c.year ///
        if year <= 2015, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("6_treatintensity_x_year_thru2015") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    * === Earliest window (year<=2012) ===
    capture quietly reghdfe `y' did_coal `controls' if year <= 2012, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("7_baseline_thru2012") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.year#i.province_id ///
        if year <= 2012, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("8_province_trend_thru2012") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }

    capture quietly reghdfe `y' did_coal `controls' c.coalexp_pre#c.year ///
        if year <= 2012, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("`y'") ("9_treatintensity_x_year_thru2012") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }
}

postclose `results'

preserve
    use "`out'/trend_robustness_results.dta", clear
    sort outcome specification
    export delimited using ///
        "`out'/Table_0820_Trend_Robustness.csv", replace
restore

log close
