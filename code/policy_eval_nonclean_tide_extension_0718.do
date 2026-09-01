*******************************************************
* Added evidence for non-clean stability and inertia
* Monthly generation, realized renewable consumption,
* and provincial coal-unit reliability, 2000-2023
*******************************************************

clear all
set more off
version 17.0

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/final_data.1.3.4_did_full_resource_v2_credit_greencredit_natural_cleanproxy_tide_absorption_monthly_reliability_0718.csv"
local out "`root'/result/tables/0718_nonclean_tide_extension"
capture mkdir "`out'"

capture log close
log using "`out'/policy_eval_nonclean_tide_extension_0718.log", text replace

capture which reghdfe
if _rc {
    display as error "reghdfe is required"
    exit 499
}

import delimited using "`data'", clear varnames(1) encoding(utf8)
destring province_id year, replace force
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"

tempname results
postfile `results' str28 block str42 outcome str40 term ///
    double b se p N r2 using "`out'/nonclean_tide_extension_results.dta", replace

*******************************************************
* 1. Within-year stability: monthly generation CV.
*******************************************************

gen double windsolar_minus_thermal_cv = windsolar_month_cv - therm_month_cv

quietly reghdfe windsolar_minus_thermal_cv if ///
    windsolar_month_n >= 6 & therm_month_n >= 6, ///
    absorb(year) vce(cluster province_id)
scalar p = 2 * ttail(e(df_r), abs(_b[_cons] / _se[_cons]))
post `results' ("monthly_stability") ("windsolar_minus_thermal_cv") ("mean_difference") ///
    (_b[_cons]) (_se[_cons]) (p) (e(N)) (e(r2))

quietly reghdfe allsrc_month_cv L.therm_gen_sh `controls' ///
    if allsrc_month_n >= 6, ///
    absorb(province_id year) vce(cluster province_id)
scalar p = 2 * ttail(e(df_r), abs(_b[L.therm_gen_sh] / _se[L.therm_gen_sh]))
post `results' ("monthly_stability") ("allsrc_month_cv") ("L.thermal_generation_share") ///
    (_b[L.therm_gen_sh]) (_se[L.therm_gen_sh]) (p) (e(N)) (e(r2))

*******************************************************
* 2. Realized renewable consumption after 2016.
*******************************************************

local ddd_rhs "post16_pretherm_z post16_endow ddd_pretherm_endow"
foreach y in re_cons_sh nonhydro_re_cons_sh {
    quietly reghdfe `y' `ddd_rhs' `controls' if year >= 2015, ///
        absorb(province_id year) vce(cluster province_id)
    foreach x in post16_pretherm_z post16_endow ddd_pretherm_endow {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("renewable_absorption") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

*******************************************************
* 3. Coal-unit operating and standby role, 2018-2023.
* Predetermined dependence is time invariant, so these
* are descriptive year-FE associations, not causal tests.
*******************************************************

foreach y in coal_unit_operating_factor coal_unit_standby_factor {
    quietly reghdfe `y' pretherm_gen_z natural_wind_solar_endowment ///
        ln_gdp sec_pctg if year >= 2018, absorb(year) vce(cluster province_id)
    foreach x in pretherm_gen_z natural_wind_solar_endowment {
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `results' ("coal_reliability") ("`y'") ("`x'") ///
            (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}

postclose `results'

use "`out'/nonclean_tide_extension_results.dta", clear
export delimited using "`out'/Table_0718_Nonclean_Tide_Extension.csv", replace

log close
