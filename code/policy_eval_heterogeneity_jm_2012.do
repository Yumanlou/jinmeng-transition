*******************************************************
* File: policy_eval_heterogeneity_jm_2012.do
* Purpose:
*   Heterogeneity DID by estimating Shanxi and
*   Neimenggu separately against the rest of China.
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

xtset province_id year

*******************************************************
* 3. Policy variables
*******************************************************

local policy_year 2012

capture drop post treat_sx did_sx treat_nmg did_nmg
gen byte post      = year >= `policy_year'
gen byte treat_sx  = province == "Shanxi"
gen byte treat_nmg = inlist(province, "Neimenggu", "Inner Mongolia")
gen double did_sx  = treat_sx  * post
gen double did_nmg = treat_nmg * post

label var did_sx  "Shanxi x Post-`policy_year'"
label var did_nmg "Neimenggu x Post-`policy_year'"

tab treat_sx
tab treat_nmg

*******************************************************
* 4. Variable lists
*******************************************************

local outcomes "coal_share_pctg ln_co2 gtfp_level gml_index industrial_so2 industrial_wastewater"
local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local cluster_var "province_id"

*******************************************************
* 5. Separate DID regressions
*******************************************************

estimates clear

local sx_xls  "`tables'/Table_Heterogeneity_Shanxi_2012.xls"
local sx_txt  "`tables'/Table_Heterogeneity_Shanxi_2012.txt"
local nmg_xls "`tables'/Table_Heterogeneity_Neimenggu_2012.xls"
local nmg_txt "`tables'/Table_Heterogeneity_Neimenggu_2012.txt"
cap erase "`sx_xls'"
cap erase "`sx_txt'"
cap erase "`nmg_xls'"
cap erase "`nmg_txt'"

local first_sx 1
foreach y of local outcomes {
    di as txt "Running Shanxi DID for outcome: `y'"
    reghdfe `y' did_sx `controls', absorb(province_id year) vce(cluster `cluster_var')

    if `first_sx' {
        outreg2 using "`sx_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(did_sx) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Shanxi, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`sx_txt'", replace ///
            ctitle(`y') dec(4) ///
            keep(did_sx) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Shanxi, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_sx 0
    }
    else {
        outreg2 using "`sx_xls'", excel append ///
            ctitle(`y') dec(4) ///
            keep(did_sx) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Shanxi, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`sx_txt'", append ///
            ctitle(`y') dec(4) ///
            keep(did_sx) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Shanxi, Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

local first_nmg 1
foreach y of local outcomes {
    di as txt "Running Neimenggu DID for outcome: `y'"
    reghdfe `y' did_nmg `controls', absorb(province_id year) vce(cluster `cluster_var')

    if `first_nmg' {
        outreg2 using "`nmg_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(did_nmg) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Neimenggu, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`nmg_txt'", replace ///
            ctitle(`y') dec(4) ///
            keep(did_nmg) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Neimenggu, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_nmg 0
    }
    else {
        outreg2 using "`nmg_xls'", excel append ///
            ctitle(`y') dec(4) ///
            keep(did_nmg) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Neimenggu, Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`nmg_txt'", append ///
            ctitle(`y') dec(4) ///
            keep(did_nmg) ///
            addtext(Policy breakpoint, `policy_year', Treated province, Neimenggu, Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

di as txt "========================================"
di as result "Heterogeneity DID completed."
di as result "Shanxi results: `sx_xls'"
di as result "Neimenggu results: `nmg_xls'"
di as txt "========================================"
