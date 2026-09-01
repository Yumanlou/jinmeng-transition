*******************************************************
* Competing-explanation diagnostics
* This file supplements rather than replaces the main
* continuous-exposure DID estimates.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv"
local out  "`root'/result/tables/0726_competing_explanations"

capture mkdir "`root'/result/tables/0726_competing_explanations"
log using "`out'/policy_eval_competing_explanations_0726.log", text replace

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

*******************************************************
* Predetermined rival exposures.
*******************************************************

bysort province_id: egen double pre_sec = ///
    mean(cond(inrange(year, 2008, 2011), sec_pctg, .))
bysort province_id: egen double pre_so2 = ///
    mean(cond(inrange(year, 2008, 2011), industrial_so2, .))

egen double z_pre_sec = std(pre_sec)
egen double z_pre_so2 = std(pre_so2)
egen double z_pre_energy = std(pre_energy5_terminal_intensity_0)
egen double z_resdep = std(resdep_pre)

gen double post_pre_sec = post12 * z_pre_sec
gen double post_pre_so2 = post12 * z_pre_so2
gen double post_pre_energy = post12 * z_pre_energy
gen double post_pre_soe = post12 * z_pre_state_owned_industrial_ass
gen double post_coalprod = post12 * coal_production_share_z
gen double post_resdep_rival = post12 * z_resdep
gen double post_pre_bank = post12 * pre_wind_loan_gdp_ratio_0811_z

* Explicitly dated proxies for two major concurrent policy families.
gen double airplan_target = (year >= 2013) * z_pre_so2
gen double supplyside_target = (year >= 2016) * coal_production_share_z

*******************************************************
* Scope and denominator diagnostics.
*******************************************************

egen byte noncoal_n = rownonmiss(oil_terminal_10k_tce_approx ///
    lpg_terminal_10k_tce_approx gas_terminal_10k_tce_approx ///
    electricity_terminal_10k_tce_app)
egen double noncoal_terminal = rowtotal(oil_terminal_10k_tce_approx ///
    lpg_terminal_10k_tce_approx gas_terminal_10k_tce_approx ///
    electricity_terminal_10k_tce_app)
replace noncoal_terminal = . if noncoal_n < 4

gen double noncoal_int = noncoal_terminal / gdp
egen double z_noncoal_int = std(noncoal_int)
gen double asinh_coal_qty = asinh(coal_terminal_10k_tce_approx)
gen double asinh_noncoal_qty = asinh(noncoal_terminal)
gen double asinh_energy5_qty = asinh(energy5_terminal_10k_tce_approx)

*******************************************************
* Result collector.
*******************************************************

tempname results
postfile `results' str30 block str40 outcome str36 specification ///
    str32 term double b se p N r2 year_min year_max ///
    using "`out'/competing_explanations_results.dta", replace

*******************************************************
* 1. Pattern tests: coal-specific adjustment versus
*    general contraction, denominator effects, and
*    unrelated pollution changes.
*******************************************************

local scope_outcomes ///
    "energy5_int coalterm_int z_noncoal_int asinh_energy5_qty asinh_coal_qty asinh_noncoal_qty dln_gdp dln_sec_val dln_totgen pm_total industrial_wastewater"

foreach y of local scope_outcomes {
    local scope_controls "`controls'"
    if inlist("`y'", "dln_gdp", "dln_sec_val", "dln_totgen") ///
        local scope_controls "population urbanization_rate env_exp_share market_index"
    capture quietly reghdfe `y' did_coal `scope_controls', ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("pattern_test") ("`y'") ("baseline") ("did_coal") ///
            (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))
    }
}

*******************************************************
* 2. Horse races against predetermined rival exposure.
*    The reported coefficient is always the original
*    Post-2012 x pre-policy coal exposure term.
*******************************************************

local core_outcomes ///
    "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5"

foreach y of local core_outcomes {
    foreach spec in ///
        "baseline" ///
        "industrial" ///
        "environmental" ///
        "resource" ///
        "finance" ///
        "dated_policies" ///
        "combined" {

        local rivals ""
        if "`spec'" == "industrial" ///
            local rivals "post_pre_sec post_pre_soe"
        if "`spec'" == "environmental" ///
            local rivals "post_pre_energy post_pre_so2"
        if "`spec'" == "resource" ///
            local rivals "post_coalprod post_resdep_rival"
        if "`spec'" == "finance" ///
            local rivals "post_pre_bank"
        if "`spec'" == "dated_policies" ///
            local rivals "airplan_target supplyside_target"
        if "`spec'" == "combined" ///
            local rivals "post_pre_sec post_pre_so2 post_coalprod post_pre_bank airplan_target supplyside_target"

        capture quietly reghdfe `y' did_coal `rivals' `controls', ///
            absorb(province_id year) vce(cluster province_id)
        if !_rc {
            tempvar matched_sample
            generate byte `matched_sample' = e(sample)
            scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
            quietly summarize year if e(sample), meanonly
            post `results' ("horse_race") ("`y'") ("`spec'") ("did_coal") ///
                (_b[did_coal]) (_se[did_coal]) (pval) (e(N)) (e(r2)) (r(min)) (r(max))

            if "`spec'" != "baseline" {
                quietly reghdfe `y' did_coal `controls' if `matched_sample', ///
                    absorb(province_id year) vce(cluster province_id)
                scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
                quietly summarize year if e(sample), meanonly
                post `results' ("horse_race") ("`y'") ("`spec'_matched_base") ///
                    ("did_coal") (_b[did_coal]) (_se[did_coal]) (pval) ///
                    (e(N)) (e(r2)) (r(min)) (r(max))
            }
            drop `matched_sample'
        }
    }
}

*******************************************************
* 3. Timing restrictions. Estimates through 2015 are
*    not contaminated by post-2016 supply-side reform;
*    2012-only estimates test immediate movement.
*******************************************************

foreach y of local core_outcomes {
    foreach cutoff in 2012 2015 2023 {
        capture quietly reghdfe `y' did_coal `controls' if year <= `cutoff', ///
            absorb(province_id year) vce(cluster province_id)
        if !_rc {
            scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
            quietly summarize year if e(sample), meanonly
            post `results' ("timing_restriction") ("`y'") ("through_`cutoff'") ///
                ("did_coal") (_b[did_coal]) (_se[did_coal]) (pval) ///
                (e(N)) (e(r2)) (r(min)) (r(max))
        }
    }
}

*******************************************************
* 4. Bank-dependence channel test with all estimable
*    lower-order interactions included.
*******************************************************

egen double z_coalexp = std(coalexp_pre)
gen double post_coal_z = post12 * z_coalexp
gen double post_bank_z = post12 * pre_wind_loan_gdp_ratio_0811_z
gen double ddd_bank = post12 * z_coalexp * pre_wind_loan_gdp_ratio_0811_z

foreach y of local core_outcomes {
    capture quietly reghdfe `y' post_coal_z post_bank_z ddd_bank `controls', ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[ddd_bank] / _se[ddd_bank]))
        quietly summarize year if e(sample), meanonly
        post `results' ("bank_channel") ("`y'") ("ddd_with_lower_orders") ///
            ("ddd_bank") (_b[ddd_bank]) (_se[ddd_bank]) (pval) ///
            (e(N)) (e(r2)) (r(min)) (r(max))
    }
}

*******************************************************
* 5. Province-specific linear trends. This is the
*    strongest test against differential secular trends.
*******************************************************

foreach y of local core_outcomes {
    capture quietly reghdfe `y' did_coal `controls' c.year#i.province_id, ///
        absorb(province_id year) vce(cluster province_id)
    if !_rc {
        scalar pval = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
        quietly summarize year if e(sample), meanonly
        post `results' ("trend_test") ("`y'") ("province_linear_trends") ///
            ("did_coal") (_b[did_coal]) (_se[did_coal]) (pval) ///
            (e(N)) (e(r2)) (r(min)) (r(max))
    }
}

postclose `results'

preserve
    use "`out'/competing_explanations_results.dta", clear
    sort block outcome specification
    export delimited using ///
        "`out'/Table_0726_Competing_Explanations.csv", replace
restore

log close
