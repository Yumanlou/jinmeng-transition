*******************************************************
* File: policy_eval_did_2012.do
* Purpose:
*   Baseline DID with policy breakpoint set to 2012
*   using the existing province-year panel dataset.
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

*******************************************************
* 3. Basic variable checks
*******************************************************

capture confirm numeric variable province_id
if _rc {
    di as error "province_id is not numeric. Please check the input data."
    exit 198
}

capture confirm numeric variable year
if _rc {
    di as error "year is not numeric. Please check the input data."
    exit 198
}

* Use existing treatment coding if available; otherwise rebuild from province names.
capture confirm variable treat
if _rc {
    gen byte treat = inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia")
}
else {
    replace treat = inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia") if missing(treat)
}

xtset province_id year

*******************************************************
* 4. Policy breakpoint = 2012
*******************************************************

local policy_year 2012

capture drop post did
gen byte post = year >= `policy_year'
gen double did = treat * post

label var post "Post-`policy_year'"
label var did  "Treat x Post-`policy_year'"

di as txt "========================================"
di as txt "Policy breakpoint set to `policy_year'"
di as txt "========================================"
tab treat
tab post
tab did

*******************************************************
* 5. Variable lists
*******************************************************

local ylist "sec_pctg coal_share_pctg ln_co2 industrial_so2 industrial_wastewater industrial_solid_waste gtfp_level gml_index"
local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local cluster_var "province_id"

*******************************************************
* 6. Baseline DID regressions
*******************************************************

estimates clear

local out_xls "`tables'/Table_Baseline_DID_2012.xls"
local out_txt "`tables'/Table_Baseline_DID_2012.txt"
cap erase "`out_xls'"
cap erase "`out_txt'"

local first_model 1
foreach y of local ylist {
    di as txt "Running DID for outcome: `y'"
    reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')

    if `first_model' {
        outreg2 using "`out_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            addtext(Policy breakpoint, `policy_year', Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`out_txt'", replace ///
            ctitle(`y') dec(4) ///
            addtext(Policy breakpoint, `policy_year', Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_model 0
    }
    else {
        outreg2 using "`out_xls'", excel append ///
            ctitle(`y') dec(4) ///
            addtext(Policy breakpoint, `policy_year', Province FE, YES, Year FE, YES, Cluster, province_id)
        outreg2 using "`out_txt'", append ///
            ctitle(`y') dec(4) ///
            addtext(Policy breakpoint, `policy_year', Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

*******************************************************
* 7. Save analysis dataset
*******************************************************

save "`data'/final_data.1.3.4_did_analysis_2012.dta", replace

di as txt "========================================"
di as result "DID completed."
di as result "Results saved to: `out_xls'"
di as result "Text table saved to: `out_txt'"
di as result "Analysis dataset saved to: `data'/final_data.1.3.4_did_analysis_2012.dta"
di as txt "========================================"
