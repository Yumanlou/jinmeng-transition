*******************************************************
* National provincial policy-attention diagnostics
* 31 provincial government work reports, 2003-2023
*******************************************************

clear all
set more off
version 17.0

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_policyworkreports_0721.csv"
local out "`root'/result/tables/0721_national_policy_attention"
capture mkdir "`out'"

capture log close
log using "`out'/policy_eval_national_policy_attention_0721.log", text replace

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

foreach topic of local topics {
    egen double z_gwr_`topic' = std(gwr_`topic'_per10k)
}
gen double gwr_clean_orientation_z = ///
    (z_gwr_renewable + z_gwr_grid_absorption) / 2 - z_gwr_fossil_security

tempname results
postfile `results' str30 block str40 outcome str34 term ///
    double b se p N r2 using "`out'/national_policy_attention_results.dta", replace

*******************************************************
* 1. Policy-attention persistence.
*******************************************************

foreach topic of local topics {
    local y "gwr_`topic'_per10k"
    quietly reghdfe `y' L.`y' `controls' if year >= 2004, ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[L.`y'] / _se[L.`y']))
    post `results' ("attention_persistence") ("`y'") ("L.attention") ///
        (_b[L.`y']) (_se[L.`y']) (p) (e(N)) (e(r2))
}

*******************************************************
* 2. Post-2012 agenda differences by thermal dependence.
*******************************************************

foreach y in gwr_green_finance_per10k gwr_fossil_security_per10k ///
    gwr_coal_retrofit_per10k gwr_pollution_control_per10k ///
    gwr_renewable_per10k gwr_grid_absorption_per10k gwr_clean_orientation_z {
    quietly reghdfe `y' post12_pretherm_z `controls' if year >= 2003, ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[post12_pretherm_z] / _se[post12_pretherm_z]))
    post `results' ("post2012_thermal_agenda") ("`y'") ("Post2012_x_PreThermal") ///
        (_b[post12_pretherm_z]) (_se[post12_pretherm_z]) (p) (e(N)) (e(r2))
}

*******************************************************
* 3. Pre-trend diagnostics for selected agenda outcomes.
*******************************************************

gen byte relbin = year - 2012
replace relbin = -5 if relbin <= -5
replace relbin = 4 if relbin >= 4
forvalues k = -5/4 {
    if `k' != -1 {
        local tag = cond(`k' < 0, "m" + string(abs(`k')), "p" + string(`k'))
        gen double evt_`tag' = (relbin == `k') * pretherm_gen_z
    }
}

local event_terms "evt_m5 evt_m4 evt_m3 evt_m2 evt_p0 evt_p1 evt_p2 evt_p3 evt_p4"
foreach y in gwr_fossil_security_per10k gwr_renewable_per10k gwr_grid_absorption_per10k {
    quietly reghdfe `y' `event_terms' `controls' if year >= 2003, ///
        absorb(province_id year) vce(cluster province_id)
    test evt_m5 evt_m4 evt_m3 evt_m2
    scalar pre_p = r(p)
    post `results' ("event_pretrend") ("`y'") ("joint_pretrend_p") ///
        (pre_p) (.) (pre_p) (e(N)) (e(r2))
}

*******************************************************
* 4. Policy attention and realized clean-power outcomes.
* These are descriptive associations, not mechanisms.
*******************************************************

foreach y in re_cons_sh nonhydro_re_cons_sh windsolar_gen_sh {
    quietly reghdfe `y' L.gwr_renewable_per10k L.gwr_grid_absorption_per10k ///
        L.gwr_fossil_security_per10k `controls' if year >= 2015, ///
        absorb(province_id year) vce(cluster province_id)
    foreach x in L.gwr_renewable_per10k L.gwr_grid_absorption_per10k L.gwr_fossil_security_per10k {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("attention_outcome_association") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

postclose `results'
use "`out'/national_policy_attention_results.dta", clear
export delimited using "`out'/Table_0721_National_Policy_Attention.csv", replace

log close
