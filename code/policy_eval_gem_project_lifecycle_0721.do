*******************************************************
* GEM project lifecycle extension, 2000-2023
* Retrospective project-level evidence from 2026 trackers
*******************************************************

clear all
set more off
version 17.0

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_projectlifecycle_0721.csv"
local out "`root'/result/tables/0721_gem_project_lifecycle"
capture mkdir "`out'"

capture log close
log using "`out'/policy_eval_gem_project_lifecycle_0721.log", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required"
    exit 499
}

import delimited using "`data'", clear varnames(1) encoding(utf8)
destring province_id year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"

gen double ihs_coal_new = asinh(gem_coal_new_mw)
gen double ihs_ws_new = asinh(gem_ws_new_mw)
gen double ihs_coal_retired = asinh(gem_coal_retired_mw)
gen double coal_net_new_mw = gem_coal_new_mw - gem_coal_retired_mw
gen double coal_new_share = gem_coal_new_mw / (gem_coal_new_mw + gem_ws_new_mw) ///
    if gem_coal_new_mw + gem_ws_new_mw > 0
gen double coal_stock_share_gem = gem_coal_stock_mw / (gem_coal_stock_mw + gem_ws_stock_mw) ///
    if gem_coal_stock_mw + gem_ws_stock_mw > 0

tempname results
postfile `results' str30 block str36 outcome str34 term ///
    double b se p N r2 using "`out'/gem_project_lifecycle_results.dta", replace

*******************************************************
* 1. Differential project formation after 2012.
*******************************************************

foreach y in ihs_coal_new ihs_ws_new coal_new_share coal_net_new_mw coal_stock_share_gem ihs_coal_retired {
    quietly reghdfe `y' post12_pretherm_z `controls', ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[post12_pretherm_z] / _se[post12_pretherm_z]))
    post `results' ("post2012_project_margin") ("`y'") ("Post2012_x_PreThermal") ///
        (_b[post12_pretherm_z]) (_se[post12_pretherm_z]) (p) (e(N)) (e(r2))
}

*******************************************************
* 2. Project-path persistence; descriptive only.
*******************************************************

foreach y in ihs_coal_new ihs_ws_new coal_new_share {
    quietly reghdfe `y' L.`y' `controls' if year >= 2001, ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[L.`y'] / _se[L.`y']))
    post `results' ("project_path_persistence") ("`y'") ("L.outcome") ///
        (_b[L.`y']) (_se[L.`y']) (p) (e(N)) (e(r2))
}

*******************************************************
* 3. Does natural advantage overcome thermal lock-in?
*******************************************************

foreach y in ihs_ws_new coal_new_share coal_stock_share_gem {
    quietly reghdfe `y' post16_pretherm_z post16_endow ddd_pretherm_endow `controls' ///
        if year >= 2013, absorb(province_id year) vce(cluster province_id)
    foreach x in post16_pretherm_z post16_endow ddd_pretherm_endow {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("natural_endowment_ddd") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

postclose `results'
use "`out'/gem_project_lifecycle_results.dta", clear
export delimited using "`out'/Table_0721_GEM_Project_Lifecycle.csv", replace

log close
