*******************************************************
* Exploratory shift-share IV for the green-credit proxy
* Two endogenous regressors are instrumented jointly:
* GC proxy and GC proxy x pre-policy resource dependence.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
capture log close

local root   "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data   "`root'/data"
local outdir "`root'/result/tables/0716_green_credit_iv"
cap mkdir "`outdir'"
log using "`outdir'/green_credit_shiftshare_iv_0716.log", text replace

foreach package in require ftools reghdfe ivreg2 ranktest ivreghdfe outreg2 {
    capture which `package'
    if _rc ssc install `package', replace
}
* ivreghdfe 1.1.4 requires reghdfe 6.12.5 or newer.
quietly ssc install ftools, replace
quietly ssc install reghdfe, replace

import delimited "`data'/final_data.1.3.4_did_full_resource_v2_credit_greencredit_iv_0716.csv", ///
    clear varnames(1) encoding(utf8)
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes "gtfp_level gml_index energy5_int coalterm_int industrial_so2 coalshare5 ln_co2 therm_cap_sh therm_gen_sh windsolar_gen_sh"
local sample "inrange(year, 2012, 2022) & !missing(green_credit_proxy, resdep_pre)"

quietly summarize green_credit_proxy if `sample'
gen double green_credit_proxy_z = (green_credit_proxy - r(mean)) / r(sd)
gen double green_credit_proxy_z_x_resdep = green_credit_proxy_z * resdep_pre

tempname first second
postfile `first' str16 specification str32 endogenous ///
    double b_iv se_iv p_iv b_iv_resdep se_iv_resdep p_iv_resdep ///
    excluded_joint_f excluded_joint_p N r2 ///
    using "`outdir'/green_credit_iv_first_stage.dta", replace

postfile `second' str32 outcome str16 specification ///
    double b_gc se_gc p_gc b_gc_resdep se_gc_resdep p_gc_resdep ///
    kp_rk_wald_f N ///
    using "`outdir'/green_credit_iv_second_stage.dta", replace

cap erase "`outdir'/Table_0716_GreenCredit_IV_2SLS.xls"

foreach specification in relative relative_no2017 level {
    local iv "iv_bartik_gc_relative_z"
    local iv_resdep "iv_bartik_gc_relative_z_x_resdep"
    local condition "`sample'"
    if "`specification'" == "relative_no2017" local condition "`sample' & year != 2017"
    if "`specification'" == "level" {
        local iv "iv_bartik_gc_level_z"
        local iv_resdep "iv_bartik_gc_level_z_x_resdep"
    }

    foreach endogenous in green_credit_proxy_z green_credit_proxy_z_x_resdep {
        quietly reghdfe `endogenous' `iv' `iv_resdep' `controls' if `condition', ///
            absorb(province_id year) vce(cluster province_id)
        scalar p_iv = 2 * ttail(e(df_r), abs(_b[`iv'] / _se[`iv']))
        scalar p_iv_resdep = 2 * ttail(e(df_r), abs(_b[`iv_resdep'] / _se[`iv_resdep']))
        quietly test `iv' `iv_resdep'
        scalar excluded_f = r(F)
        scalar excluded_p = r(p)
        post `first' ("`specification'") ("`endogenous'") ///
            (_b[`iv']) (_se[`iv']) (p_iv) ///
            (_b[`iv_resdep']) (_se[`iv_resdep']) (p_iv_resdep) ///
            (excluded_f) (excluded_p) (e(N)) (e(r2))
    }

    foreach y of local outcomes {
        quietly ivreghdfe `y' `controls' ///
            (green_credit_proxy_z green_credit_proxy_z_x_resdep = `iv' `iv_resdep') ///
            if `condition', absorb(province_id year) cluster(province_id)
        scalar p_gc = 2 * normal(-abs(_b[green_credit_proxy_z] / _se[green_credit_proxy_z]))
        scalar p_gc_resdep = 2 * normal(-abs(_b[green_credit_proxy_z_x_resdep] / _se[green_credit_proxy_z_x_resdep]))
        scalar weak_f = .
        capture scalar weak_f = e(widstat)
        post `second' ("`y'") ("`specification'") ///
            (_b[green_credit_proxy_z]) (_se[green_credit_proxy_z]) (p_gc) ///
            (_b[green_credit_proxy_z_x_resdep]) (_se[green_credit_proxy_z_x_resdep]) ///
            (p_gc_resdep) (weak_f) (e(N))

        outreg2 using "`outdir'/Table_0716_GreenCredit_IV_2SLS.xls", excel append ///
            keep(green_credit_proxy_z green_credit_proxy_z_x_resdep) dec(4) ///
            ctitle("`y': `specification'") ///
            addtext(Province FE, Yes, Year FE, Yes, Cluster, Province, ///
                Instrument, "`specification'", KP rk Wald F, weak_f)
    }
}

postclose `first'
postclose `second'

use "`outdir'/green_credit_iv_first_stage.dta", clear
export delimited using "`outdir'/Table_0716_GreenCredit_IV_FirstStage.csv", replace

use "`outdir'/green_credit_iv_second_stage.dta", clear
export delimited using "`outdir'/Table_0716_GreenCredit_IV_SecondStage.csv", replace

log close
