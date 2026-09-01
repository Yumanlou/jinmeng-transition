*******************************************************
* File: policy_eval_scm_structure_2012.do
* Purpose:
*   Synthetic control for structural-transition variables
*   under the 2012 green credit policy.
*   Treated units: Shanxi and Neimenggu
*   Outcomes: coal_share_pctg, sec_pctg
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
local figures "`result'/figures"

cap mkdir "`result'"
cap mkdir "`tables'"
cap mkdir "`figures'"

*******************************************************
* 1. Packages
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

ensure_pkg, checkcmd(synth)   installpkg(synth)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)

*******************************************************
* 2. Load data
*******************************************************

import delimited "`data'/final_data.1.3.4_did.csv", ///
    clear varnames(1) encoding(utf8)

xtset province_id year

local idvar   province_id
local timevar year
local tr_year 2012

* Use a relatively clean pre-period window.
local t_start   2005
local pre_start 2005
local pre_end   2011

* Predictors for structural SCM.
local X "ln_gdp population urbanization_rate market_index"

*******************************************************
* 3. Output setup
*******************************************************

tempfile results_dta
postfile scm_handle ///
    str16 treated ///
    str20 outcome ///
    double post_gap_mean ///
    double pre_rmspe ///
    double post_rmspe ///
    double gap_reg_beta ///
    double gap_reg_se ///
    using `results_dta', replace

*******************************************************
* 4. Run SCM by province and outcome
*******************************************************

local treated_ids "11 3"
local outcomes "coal_share_pctg sec_pctg"

foreach y of local outcomes {
    foreach treated_id of local treated_ids {
        local treated_name "Shanxi"
        if `treated_id' == 3 local treated_name "Neimenggu"
        local current_t_end 2023
        if "`y'" == "coal_share_pctg" local current_t_end 2022

        di as txt "========================================"
        di as txt "Running SCM for `treated_name' | Outcome: `y'"
        di as txt "========================================"

        preserve
        keep if inrange(`timevar', `t_start', `current_t_end')

        * Province-level completeness in pre-period.
        tempvar ok
        gen byte `ok' = 1
        foreach v of local X {
            replace `ok' = 0 if inrange(`timevar', `pre_start', `pre_end') & missing(`v')
        }
        replace `ok' = 0 if inrange(`timevar', `pre_start', `pre_end') & missing(`y')
        bysort `idvar': egen keep_prov = min(`ok')

        count if `idvar' == `treated_id' & keep_prov == 1
        if r(N) == 0 {
            di as error "Treated unit `treated_name' fails pre-period completeness for `y'. Skipping."
            restore
            continue
        }

        keep if keep_prov == 1
        drop `ok' keep_prov

        tempfile scm_keep
        synth `y' `X', ///
            trunit(`treated_id') trperiod(`tr_year') ///
            unitvariable(`idvar') timevariable(`timevar') ///
            special(`y'(2005) `y'(2008) `y'(2011)) ///
            keep("`scm_keep'") replace

        use "`scm_keep'", clear
        keep if !missing(_time)
        rename _time year

        capture confirm variable _Y_treated
        if _rc {
            di as error "_Y_treated not found for `treated_name' / `y'."
            restore
            continue
        }
        capture confirm variable _Y_synthetic
        if _rc {
            di as error "_Y_synthetic not found for `treated_name' / `y'."
            restore
            continue
        }

        gen gap_scm = _Y_treated - _Y_synthetic
        gen post2012 = (year >= `tr_year')
        gen gap_sq = gap_scm^2

        quietly summarize gap_scm if post2012 == 1, meanonly
        local post_gap_mean = r(mean)
        quietly summarize gap_sq if post2012 == 0, meanonly
        local pre_rmspe = sqrt(r(mean))
        quietly summarize gap_sq if post2012 == 1, meanonly
        local post_rmspe = sqrt(r(mean))

        quietly reg gap_scm post2012, vce(robust)
        local gap_beta = _b[post2012]
        local gap_se   = _se[post2012]

        post scm_handle ///
            ("`treated_name'") ///
            ("`y'") ///
            (`post_gap_mean') ///
            (`pre_rmspe') ///
            (`post_rmspe') ///
            (`gap_beta') ///
            (`gap_se')

        twoway ///
            (line _Y_treated year, lcolor(navy) lwidth(medthick)) ///
            (line _Y_synthetic year, lcolor(maroon) lpattern(dash) lwidth(medthick)), ///
            xline(`tr_year', lpattern(shortdash)) ///
            title("SCM Path: `treated_name'") ///
            subtitle("Outcome: `y'") ///
            legend(order(1 "Actual" 2 "Synthetic")) ///
            ytitle("`y'") xtitle("Year")
        graph export "`figures'/SCM_`treated_name'_`y'_path.png", replace width(2400)

        twoway ///
            (line gap_scm year, lcolor(navy) lwidth(medthick)), ///
            xline(`tr_year', lpattern(shortdash)) ///
            yline(0, lpattern(dot)) ///
            title("SCM Gap: `treated_name'") ///
            subtitle("Outcome: `y' | Actual - Synthetic") ///
            ytitle("Gap") xtitle("Year")
        graph export "`figures'/SCM_`treated_name'_`y'_gap.png", replace width(2400)

        restore
    }
}

postclose scm_handle

*******************************************************
* 5. Export summary table
*******************************************************

use `results_dta', clear
sort outcome treated
save "`tables'/Table_SCM_Structure_2012.dta", replace
export delimited using "`tables'/Table_SCM_Structure_2012.txt", delimiter(tab) replace

capture file close xmlfile
file open xmlfile using "`tables'/Table_SCM_Structure_2012.xml", write replace
file write xmlfile ///
"<?xml version=""1.0"" encoding=""UTF-8""?>" ///
"<?mso-application progid=""Excel.Sheet""?>" ///
"<Workbook xmlns=""urn:schemas-microsoft-com:office:spreadsheet"" xmlns:ss=""urn:schemas-microsoft-com:office:spreadsheet""><Worksheet ss:Name=""SCM_Structure""><Table>" _n
file write xmlfile ///
"<Row><Cell><Data ss:Type=""String"">treated</Data></Cell><Cell><Data ss:Type=""String"">outcome</Data></Cell><Cell><Data ss:Type=""String"">post_gap_mean</Data></Cell><Cell><Data ss:Type=""String"">pre_rmspe</Data></Cell><Cell><Data ss:Type=""String"">post_rmspe</Data></Cell><Cell><Data ss:Type=""String"">gap_reg_beta</Data></Cell><Cell><Data ss:Type=""String"">gap_reg_se</Data></Cell></Row>" _n

quietly count
forvalues i = 1/`r(N)' {
    local treated_i      = treated[`i']
    local outcome_i      = outcome[`i']
    local post_gap_i     : display %9.4f post_gap_mean[`i']
    local pre_rmspe_i    : display %9.4f pre_rmspe[`i']
    local post_rmspe_i   : display %9.4f post_rmspe[`i']
    local gap_beta_i     : display %9.4f gap_reg_beta[`i']
    local gap_se_i       : display %9.4f gap_reg_se[`i']
    file write xmlfile ///
    "<Row><Cell><Data ss:Type=""String"">`treated_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""String"">`outcome_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`post_gap_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`pre_rmspe_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`post_rmspe_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`gap_beta_i'</Data></Cell>" ///
    "<Cell><Data ss:Type=""Number"">`gap_se_i'</Data></Cell></Row>" _n
}
file write xmlfile "</Table></Worksheet></Workbook>" _n
file close xmlfile

*******************************************************
* 6. Completion info
*******************************************************

di as txt "========================================"
di as result "SCM for structural outcomes completed."
di as result "Summary table: `tables'/Table_SCM_Structure_2012.txt"
di as result "Figures saved to: `figures'"
di as txt "========================================"
