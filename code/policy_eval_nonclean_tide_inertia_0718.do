*******************************************************
* Non-clean energy stability, tide, and policy inertia
* Exploratory province-panel evidence, 2000-2023
*******************************************************

clear all
set more off
version 17.0

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_0718.csv"
local out "`root'/result/tables/0718_nonclean_tide_inertia"
capture mkdir "`out'"

capture log close
log using "`out'/policy_eval_nonclean_tide_inertia_0718.log", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required"
    exit 499
}

import delimited using "`data'", clear varnames(1) encoding(utf8)
destring province_id year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local growth_controls "dln_gdp sec_pctg urbanization_rate env_exp_share market_index"

tempname results
postfile `results' str28 block str36 outcome str32 term ///
    double b se p N r2 using "`out'/nonclean_tide_inertia_results.dta", replace

*******************************************************
* 1. Stable-output value: idiosyncratic volatility.
*******************************************************

quietly reghdfe dln_totgen dln_gdp, absorb(province_id year) residuals(gen_resid)
gen double abs_gen_resid = abs(gen_resid)

quietly reghdfe dln_gdp, absorb(province_id year) residuals(gdp_resid)
gen double abs_gdp_resid = abs(gdp_resid)

quietly reghdfe dln_sec_val, absorb(province_id year) residuals(sec_resid)
gen double abs_sec_resid = abs(sec_resid)

foreach y in abs_gen_resid abs_gdp_resid abs_sec_resid {
    quietly reghdfe `y' L.therm_gen_sh sec_pctg urbanization_rate ///
        env_exp_share market_index, absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[L.therm_gen_sh] / _se[L.therm_gen_sh]))
    post `results' ("stable_output") ("`y'") ("L.thermal_generation_share") ///
        (_b[L.therm_gen_sh]) (_se[L.therm_gen_sh]) (p) (e(N)) (e(r2))

    quietly reghdfe `y' post12_pretherm_z sec_pctg urbanization_rate ///
        env_exp_share market_index, absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[post12_pretherm_z] / _se[post12_pretherm_z]))
    post `results' ("stable_output") ("`y'") ("Post2012_x_PreThermal") ///
        (_b[post12_pretherm_z]) (_se[post12_pretherm_z]) (p) (e(N)) (e(r2))
}

*******************************************************
* 2. Tide: common capacity waves and realization gap.
*******************************************************

gen double thermal_cap_generation_gap = dln_thermcap - dln_thermgen

foreach y in dln_thermcap dln_thermgen thermal_cap_generation_gap {
    quietly reghdfe `y' tide_loading `growth_controls', ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[tide_loading] / _se[tide_loading]))
    post `results' ("thermal_tide") ("`y'") ("NationalThermalWave_x_PreThermal") ///
        (_b[tide_loading]) (_se[tide_loading]) (p) (e(N)) (e(r2))

    quietly reghdfe `y' demand_loading `growth_controls', ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[demand_loading] / _se[demand_loading]))
    post `results' ("thermal_tide") ("`y'") ("NationalDemandWave_x_PreThermal") ///
        (_b[demand_loading]) (_se[demand_loading]) (p) (e(N)) (e(r2))
}

quietly reghdfe F1.dln_therm_util dln_thermcap `growth_controls', ///
    absorb(province_id year) vce(cluster province_id)
scalar p = 2 * ttail(e(df_r), abs(_b[dln_thermcap] / _se[dln_thermcap]))
post `results' ("thermal_tide") ("F1.dln_thermal_utilization") ("dln_thermal_capacity") ///
    (_b[dln_thermcap]) (_se[dln_thermcap]) (p) (e(N)) (e(r2))

*******************************************************
* 3. Does thermal dependence block natural advantage?
*******************************************************

local ddd_rhs "post16_pretherm_z post16_endow ddd_pretherm_endow"
gen double windsolar_cap_gen_gap = windsolar_cap_sh - windsolar_gen_sh
local transition_outcomes "windsolar_cap_sh windsolar_gen_sh windsolar_cap_gen_gap clean_capacity_addition_per_gdp clean_generation_kwh_per_cny_gdp therm_cap_sh therm_gen_sh"

foreach y of local transition_outcomes {
    quietly reghdfe `y' `ddd_rhs' `controls' if year >= 2013, ///
        absorb(province_id year) vce(cluster province_id)
    foreach x in post16_pretherm_z post16_endow ddd_pretherm_endow {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("advantage_conversion") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

* Alternative predetermined thermal dependence and natural-resource dimensions.
gen double post16_prethermcap_z = post2016 * pretherm_cap_z
gen double triple_thermcap_combined = post2016 * pretherm_cap_z * natural_wind_solar_endowment
gen double post16_windendow = post2016 * wind_resource_cf_z
gen double triple_thermgen_wind = post2016 * pretherm_gen_z * wind_resource_cf_z
gen double post16_solarendow = post2016 * solar_resource_cf_z
gen double triple_thermgen_solar = post2016 * pretherm_gen_z * solar_resource_cf_z

foreach spec in ///
    "post16_prethermcap_z post16_endow triple_thermcap_combined thermcap_combined" ///
    "post16_pretherm_z post16_windendow triple_thermgen_wind thermgen_wind" ///
    "post16_pretherm_z post16_solarendow triple_thermgen_solar thermgen_solar" {
    tokenize `spec'
    local thermal_term "`1'"
    local endow_term "`2'"
    local triple_term "`3'"
    local spec_name "`4'"
    foreach y in windsolar_cap_sh windsolar_gen_sh windsolar_cap_gen_gap therm_cap_sh therm_gen_sh {
        quietly reghdfe `y' `thermal_term' `endow_term' `triple_term' `controls' ///
            if year >= 2013, absorb(province_id year) vce(cluster province_id)
        scalar p = 2 * ttail(e(df_r), abs(_b[`triple_term'] / _se[`triple_term']))
        post `results' ("conversion_robustness") ("`y'") ("`spec_name'") ///
            (_b[`triple_term']) (_se[`triple_term']) (p) (e(N)) (e(r2))
    }
}

*******************************************************
* 4. Observable political-economy lock-in proxies.
*******************************************************

foreach dim in fiscal soe {
    local rhs "post16_`dim' post16_endow ddd_`dim'_endow"
    foreach y in windsolar_cap_sh windsolar_gen_sh windsolar_cap_gen_gap clean_generation_kwh_per_cny_gdp therm_cap_sh therm_gen_sh {
        quietly reghdfe `y' `rhs' `controls' if year >= 2013, ///
            absorb(province_id year) vce(cluster province_id)
        foreach x in post16_`dim' post16_endow ddd_`dim'_endow {
            scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
            post `results' ("`dim'_lockin") ("`y'") ("`x'") ///
                (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
        }
    }
}

postclose `results'

preserve
    use "`out'/nonclean_tide_inertia_results.dta", clear
    export delimited using "`out'/Table_0718_Nonclean_Tide_Inertia.csv", replace
restore

log close
