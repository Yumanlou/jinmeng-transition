*******************************************************
* Provincial leadership turnover and policy attention
* Descriptive appendix evidence, 2003-2018
*******************************************************

clear all
set more off
version 17.0

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_leadership_0721.csv"
local out "`root'/result/tables/0721_leadership_policy_inertia"
capture mkdir "`out'"

capture log close
log using "`out'/policy_eval_leadership_policy_inertia_0721.log", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required"
    exit 499
}

import delimited using "`data'", clear varnames(1) encoding(utf8)
destring province_id year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local topics "green_finance fossil_security coal_retrofit pollution_control renewable grid_absorption"
local change_vars "gwr_gf_chg gwr_fs_chg gwr_cr_chg gwr_pc_chg gwr_re_chg gwr_ga_chg"

tempname results
postfile `results' str32 block str42 outcome str38 term ///
    double b se p N r2 using "`out'/leadership_policy_inertia_results.dta", replace

*******************************************************
* 1. Does leadership replacement coincide with agenda change?
*******************************************************

foreach y of local change_vars {
    quietly reghdfe `y' party_turnover government_turnover `controls' ///
        if year >= 2004 & year <= 2018, absorb(province_id year) vce(cluster province_id)
    foreach x in party_turnover government_turnover {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("agenda_change") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

*******************************************************
* 2. Does turnover weaken persistence from the prior year?
* Dynamic fixed-effects estimates are descriptive only.
*******************************************************

foreach topic of local topics {
    local y "gwr_`topic'_per10k"
    gen double turnover_lag_`topic' = any_top_leader_turnover * L.`y'
    quietly reghdfe `y' L.`y' any_top_leader_turnover turnover_lag_`topic' `controls' ///
        if year >= 2004 & year <= 2018, absorb(province_id year) vce(cluster province_id)
    foreach x in L.`y' any_top_leader_turnover turnover_lag_`topic' {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("persistence_moderation") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

postclose `results'
use "`out'/leadership_policy_inertia_results.dta", clear
export delimited using "`out'/Table_0721_Leadership_Policy_Inertia.csv", replace

log close
