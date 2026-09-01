version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/green_credit_bank_policy_proxy"
local outdir "`root'/result/tables/0718_green_credit_bank_policy_proxy"
cap mkdir "`outdir'"
log using "`outdir'/green_credit_bank_policy_proxy_iv_0718.log", text replace

foreach package in reghdfe ftools ivreg2 ranktest ivreghdfe outreg2 {
    capture which `package'
    if _rc ssc install `package', replace
}

use "`data'/green_credit_bank_policy_proxy_panel_2005_2022.dta", clear
capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
xtset province_id year

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local sample "inrange(year, 2005, 2022) & !missing(gc_proxy_z_full, resdep_pre)"
local z1 "bank_policy_iv_z"
local z2 "bank_policy_iv_z_x_resdep"

tempname first second
postfile `first' str32 endogenous double b_z1 se_z1 p_z1 b_z2 se_z2 p_z2 ///
    joint_f joint_p N r2 using "`outdir'/bank_policy_proxy_first_stage.dta", replace

foreach endogenous in gc_proxy_z_full gc_proxy_z_x_resdep {
    quietly reghdfe `endogenous' `z1' `z2' `controls' if `sample', ///
        absorb(province_id year) vce(cluster province_id)
    scalar p1 = 2 * ttail(e(df_r), abs(_b[`z1'] / _se[`z1']))
    scalar p2 = 2 * ttail(e(df_r), abs(_b[`z2'] / _se[`z2']))
    quietly test `z1' `z2'
    post `first' ("`endogenous'") ///
        (_b[`z1']) (_se[`z1']) (p1) (_b[`z2']) (_se[`z2']) (p2) ///
        (r(F)) (r(p)) (e(N)) (e(r2))
}
postclose `first'

local outcomes "energy5_int coalterm_int industrial_so2 coalshare5 ln_co2 therm_cap_sh therm_gen_sh windsolar_gen_sh"
postfile `second' str32 outcome double b_gc se_gc p_gc b_int se_int p_int ///
    kp_f N using "`outdir'/bank_policy_proxy_second_stage.dta", replace

cap erase "`outdir'/Table_0718_BankPolicyProxy_IV_2SLS.xls"
local firstcol 1
foreach y of local outcomes {
    capture quietly ivreghdfe `y' `controls' ///
        (gc_proxy_z_full gc_proxy_z_x_resdep = `z1' `z2') ///
        if `sample', absorb(province_id year) cluster(province_id)
    if _rc {
        di as error "Skipping `y': ivreghdfe returned error " _rc
        continue
    }
    scalar pgc = 2 * normal(-abs(_b[gc_proxy_z_full] / _se[gc_proxy_z_full]))
    scalar pint = 2 * normal(-abs(_b[gc_proxy_z_x_resdep] / _se[gc_proxy_z_x_resdep]))
    scalar weakf = .
    capture scalar weakf = e(widstat)
    post `second' ("`y'") ///
        (_b[gc_proxy_z_full]) (_se[gc_proxy_z_full]) (pgc) ///
        (_b[gc_proxy_z_x_resdep]) (_se[gc_proxy_z_x_resdep]) (pint) ///
        (weakf) (e(N))

    if `firstcol' {
        outreg2 using "`outdir'/Table_0718_BankPolicyProxy_IV_2SLS.xls", excel replace ///
            keep(gc_proxy_z_full gc_proxy_z_x_resdep) dec(4) ctitle("`y'") ///
            addtext(Province FE, Yes, Year FE, Yes, Cluster, Province, KP rk Wald F, weakf)
        local firstcol 0
    }
    else {
        outreg2 using "`outdir'/Table_0718_BankPolicyProxy_IV_2SLS.xls", excel append ///
            keep(gc_proxy_z_full gc_proxy_z_x_resdep) dec(4) ctitle("`y'") ///
            addtext(Province FE, Yes, Year FE, Yes, Cluster, Province, KP rk Wald F, weakf)
    }
}
postclose `second'

use "`outdir'/bank_policy_proxy_first_stage.dta", clear
export delimited using "`outdir'/Table_0718_BankPolicyProxy_FirstStage.csv", replace
list, noobs clean

use "`outdir'/bank_policy_proxy_second_stage.dta", clear
export delimited using "`outdir'/Table_0718_BankPolicyProxy_SecondStage.csv", replace
list, noobs clean

log close
