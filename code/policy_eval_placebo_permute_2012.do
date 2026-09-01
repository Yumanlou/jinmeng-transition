*******************************************************
* File: policy_eval_placebo_permute_2012.do
* Purpose:
*   Random-permutation placebo test for the 2012 DID.
*   In each repetition, randomly select 2 provinces as
*   fake treated units and compare placebo estimates with
*   the actual DID coefficient.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close
set seed 20260323

*******************************************************
* 0. Paths
*******************************************************

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local result  "`root'/result"
local tables  "`result'/tables"
local figures "`result'/figures"

cap mkdir "`result'"
cap mkdir "`tables'"
cap mkdir "`figures'"

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
* 2. Read data and define actual treatment
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

local policy_year 2012
gen byte post = year >= `policy_year'
gen double did = treat * post

xtset province_id year

local outcomes "ln_co2 gtfp_level gml_index industrial_so2"
local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local cluster_var "province_id"
local reps 1000

*******************************************************
* 3. Save base data and actual DID coefficients
*******************************************************

tempfile base province_pool actual_coefs placebo_store
save `base', replace

preserve
keep province_id province
duplicates drop
sort province_id
save `province_pool', replace
restore

postfile actual_handle str24 outcome double beta_actual se_actual using `actual_coefs', replace
foreach y of local outcomes {
    quietly reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    post actual_handle ("`y'") (_b[did]) (_se[did])
}
postclose actual_handle

*******************************************************
* 4. Random-permutation placebo
*******************************************************

postfile placebo_handle str24 outcome int rep double beta_placebo using `placebo_store', replace

forvalues r = 1/`reps' {
    quietly {
        use `province_pool', clear
        gen double u = runiform()
        sort u
        keep in 1/2
        keep province_id
        gen byte placebo_treat = 1
        tempfile fake_treated
        save `fake_treated', replace

        use `base', clear
        merge m:1 province_id using `fake_treated', nogen
        replace placebo_treat = 0 if missing(placebo_treat)
        gen double placebo_did = placebo_treat * post

        foreach y of local outcomes {
            capture noisily reghdfe `y' placebo_did `controls', ///
                absorb(province_id year) vce(cluster `cluster_var')
            if _rc == 0 {
                post placebo_handle ("`y'") (`r') (_b[placebo_did])
            }
        }
    }

    if mod(`r', 100) == 0 {
        di as txt "Completed placebo repetition `r' / `reps'"
    }
}

postclose placebo_handle

*******************************************************
* 5. Summarize placebo distribution
*******************************************************

use `placebo_store', clear
save "`tables'/Placebo_Permutation_Draws_2012.dta", replace

tempfile summary
postfile summary_handle str24 outcome double beta_actual placebo_mean placebo_sd empirical_p using `summary', replace

levelsof outcome, local(outcome_list)
foreach y of local outcome_list {
    preserve
    keep if outcome == "`y'"
    quietly summarize beta_placebo
    local mean_p = r(mean)
    local sd_p   = r(sd)
    count if abs(beta_placebo) >= .
    restore

    preserve
    use `actual_coefs', clear
    keep if outcome == "`y'"
    local actual = beta_actual[1]
    restore

    preserve
    keep if outcome == "`y'"
    count
    local total_n = r(N)
    count if abs(beta_placebo) >= abs(`actual')
    local tail_n = r(N)
    local p_emp = `tail_n' / `total_n'
    post summary_handle ("`y'") (`actual') (`mean_p') (`sd_p') (`p_emp')
    restore
}
postclose summary_handle

use `summary', clear
export delimited using "`tables'/Table_Placebo_Permutation_2012.txt", delimiter(tab) replace
save "`tables'/Table_Placebo_Permutation_2012.dta", replace
tempfile summary_data
save `summary_data', replace

*******************************************************
* 6. Export XML-style table
*******************************************************

capture file close xmlfile
file open xmlfile using "`tables'/Table_Placebo_Permutation_2012.xml", write replace
file write xmlfile ///
"<?xml version=""1.0"" encoding=""UTF-8""?>" ///
"<?mso-application progid=""Excel.Sheet""?>" ///
"<Workbook xmlns=""urn:schemas-microsoft-com:office:spreadsheet"" xmlns:ss=""urn:schemas-microsoft-com:office:spreadsheet""><Worksheet ss:Name=""Placebo""><Table>" _n
file write xmlfile ///
"<Row><Cell><Data ss:Type=""String"">outcome</Data></Cell><Cell><Data ss:Type=""String"">beta_actual</Data></Cell><Cell><Data ss:Type=""String"">placebo_mean</Data></Cell><Cell><Data ss:Type=""String"">placebo_sd</Data></Cell><Cell><Data ss:Type=""String"">empirical_p</Data></Cell></Row>" _n

quietly count
forvalues i = 1/`r(N)' {
    local outcome_i = outcome[`i']
    local beta_actual_i : display %9.4f beta_actual[`i']
    local placebo_mean_i : display %9.4f placebo_mean[`i']
    local placebo_sd_i   : display %9.4f placebo_sd[`i']
    local empirical_p_i  : display %9.4f empirical_p[`i']
    file write xmlfile ///
    "<Row><Cell><Data ss:Type=""String"">`outcome_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`beta_actual_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`placebo_mean_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`placebo_sd_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`empirical_p_i'</Data></Cell></Row>" _n
}

file write xmlfile "</Table></Worksheet></Workbook>" _n
file close xmlfile

*******************************************************
* 7. Plot placebo distributions
*******************************************************

foreach y of local outcome_list {
    use `summary_data', clear
    keep if outcome == "`y'"
    local actual = beta_actual[1]

    use "`tables'/Placebo_Permutation_Draws_2012.dta", clear
    keep if outcome == "`y'"
    quietly summarize beta_placebo, meanonly
    local binw = (r(max) - r(min)) / 30
    if `binw' <= 0 {
        local binw = 0.01
    }

    histogram beta_placebo, ///
        width(`binw') ///
        color(gs12) ///
        xline(`actual', lcolor(maroon) lwidth(medthick)) ///
        xtitle("Placebo coefficient") ///
        ytitle("Frequency") ///
        title("Permutation placebo: `y'") ///
        note("Red line = actual DID coefficient")

    graph export "`figures'/Placebo_Permutation_2012_`y'.png", replace width(2400)
}

*******************************************************
* 8. Display completion info
*******************************************************

di as txt "========================================"
di as result "Permutation placebo test completed."
di as result "Summary table: `tables'/Table_Placebo_Permutation_2012.txt"
di as result "Placebo draws: `tables'/Placebo_Permutation_Draws_2012.dta"
di as result "Figures saved to: `figures'"
di as txt "========================================"
