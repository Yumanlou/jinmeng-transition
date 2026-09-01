*******************************************************
* File: policy_eval_ddd_2012.do
* Purpose:
*   Triple-difference estimation with policy breakpoint
*   set to 2012 and a pre-policy efficiency grouping.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

*******************************************************
* 0. Paths
*******************************************************

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local result  "`root'/result"
local tables  "`result'/tables"

cap mkdir "`result'"
cap mkdir "`tables'"

*******************************************************
* 1. Install required packages
*******************************************************

capture program drop ensure_pkg
program define ensure_pkg
    syntax, CHECKCMD(string) INSTALLPKG(string)

    cap which `checkcmd'
    if _rc {
        di as txt "Package/command `checkcmd' not found. Trying to install `installpkg' from SSC ..."
        cap noi ssc install `installpkg', replace
        cap which `checkcmd'
        if _rc {
            di as error "Installation failed or interrupted: `installpkg'"
            di as error "Please run manually: ssc install `installpkg', replace"
            exit 199
        }
    }
end

ensure_pkg, checkcmd(reghdfe) installpkg(reghdfe)
ensure_pkg, checkcmd(ftools) installpkg(ftools)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)

*******************************************************
* 2. Read data
*******************************************************

import delimited "`data'/final_data.1.3.4_did.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm variable treat
if _rc {
    gen byte treat = inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia")
}
else {
    replace treat = inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia") if missing(treat)
}

xtset province_id year

*******************************************************
* 3. Policy and DDD variables
*******************************************************

local policy_year 2012

capture drop post did pre_gtfp_mean pre_gtfp_median high_efficiency ddd
gen byte post = year >= `policy_year'
gen double did = treat * post

* Third dimension: province-level pre-policy efficiency endowment.
* This avoids perfect collinearity because Shanxi and Neimenggu
* differ in their pre-policy GTFP levels.
bysort province_id: egen pre_gtfp_mean = mean(cond(year < `policy_year', gtfp_level, .))
egen pre_gtfp_median = median(pre_gtfp_mean)
gen byte high_efficiency = pre_gtfp_mean > pre_gtfp_median if !missing(pre_gtfp_mean)
replace high_efficiency = 0 if missing(high_efficiency)

gen double ddd = treat * post * high_efficiency

label var post         "Post-`policy_year'"
label var did          "Treat x Post-`policy_year'"
label var high_efficiency "High-efficiency province (pre-`policy_year')"
label var ddd             "Treat x Post x High-efficiency"

tab high_efficiency
tab treat high_efficiency

*******************************************************
* 4. Variable lists
*******************************************************

local outcomes "coal_share_pctg ln_co2 gtfp_level gml_index industrial_so2 industrial_wastewater"
local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local cluster_var "province_id"

*******************************************************
* 5. DDD regressions
*******************************************************

estimates clear

local out_xls "`tables'/Table_DDD_2012.xls"
local out_txt "`tables'/Table_DDD_2012.txt"
cap erase "`out_xls'"
cap erase "`out_txt'"

local first_model 1
foreach y of local outcomes {
    di as txt "Running DDD for outcome: `y'"

    reghdfe `y' did high_efficiency ddd `controls', ///
        absorb(province_id year) vce(cluster `cluster_var')

    if `first_model' {
        outreg2 using "`out_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(did high_efficiency ddd) ///
            addtext(Policy breakpoint, `policy_year', Third dimension, High-efficiency pre-policy GTFP, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`out_txt'", replace ///
            ctitle(`y') dec(4) ///
            keep(did high_efficiency ddd) ///
            addtext(Policy breakpoint, `policy_year', Third dimension, High-efficiency pre-policy GTFP, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_model 0
    }
    else {
        outreg2 using "`out_xls'", excel append ///
            ctitle(`y') dec(4) ///
            keep(did high_efficiency ddd) ///
            addtext(Policy breakpoint, `policy_year', Third dimension, High-efficiency pre-policy GTFP, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`out_txt'", append ///
            ctitle(`y') dec(4) ///
            keep(did high_efficiency ddd) ///
            addtext(Policy breakpoint, `policy_year', Third dimension, High-efficiency pre-policy GTFP, Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

di as txt "========================================"
di as result "DDD completed."
di as result "Results saved to: `out_xls'"
di as result "Text table saved to: `out_txt'"
di as txt "========================================"
