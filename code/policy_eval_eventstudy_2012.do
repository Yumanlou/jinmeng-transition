*******************************************************
* File: policy_eval_eventstudy_2012.do
* Purpose:
*   Event-study / parallel-trend test with policy
*   breakpoint set to 2012.
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
ensure_pkg, checkcmd(coefplot) installpkg(coefplot)

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
* 3. Rebuild event-time variables for 2012
*******************************************************

local policy_year 2012
local min_lead   -4
local max_lag     4

capture drop post did event_time_2012 evt_grp
gen byte post = year >= `policy_year'
gen double did = treat * post
gen int event_time_2012 = year - `policy_year'
replace event_time_2012 = . if treat == 0

gen int evt_grp = event_time_2012
replace evt_grp = `min_lead' if event_time_2012 <= `min_lead' & !missing(event_time_2012)
replace evt_grp = `max_lag'  if event_time_2012 >= `max_lag'  & !missing(event_time_2012)

label var event_time_2012 "Event time relative to `policy_year'"
label var evt_grp "Binned event time"

* Manually build event dummies; omit -1 as the base period.
capture drop es_pre4 es_pre3 es_pre2 es_0 es_1 es_2 es_3 es_4
gen byte es_pre4 = (evt_grp == -4 & treat == 1)
gen byte es_pre3 = (evt_grp == -3 & treat == 1)
gen byte es_pre2 = (evt_grp == -2 & treat == 1)
gen byte es_0    = (evt_grp == 0  & treat == 1)
gen byte es_1    = (evt_grp == 1  & treat == 1)
gen byte es_2    = (evt_grp == 2  & treat == 1)
gen byte es_3    = (evt_grp == 3  & treat == 1)
gen byte es_4    = (evt_grp == 4  & treat == 1)

label var es_pre4 "Treat x event<=-4"
label var es_pre3 "Treat x event=-3"
label var es_pre2 "Treat x event=-2"
label var es_0    "Treat x event=0"
label var es_1    "Treat x event=1"
label var es_2    "Treat x event=2"
label var es_3    "Treat x event=3"
label var es_4    "Treat x event>=4"

*******************************************************
* 4. Variable lists
*******************************************************

local outcomes "coal_share_pctg ln_co2 gtfp_level gml_index industrial_so2 industrial_wastewater"
local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local cluster_var "province_id"
local es_terms "es_pre4 es_pre3 es_pre2 es_0 es_1 es_2 es_3 es_4"

*******************************************************
* 5. Event-study regressions
*******************************************************

estimates clear

local es_xls "`tables'/Table_EventStudy_2012.xls"
local es_txt "`tables'/Table_EventStudy_2012.txt"
local pt_txt "`tables'/Table_ParallelTrend_Test_2012.txt"
cap erase "`es_xls'"
cap erase "`es_txt'"
cap erase "`pt_txt'"

capture file close ptfile
file open ptfile using "`pt_txt'", write replace
file write ptfile "Parallel-trend test with policy breakpoint = `policy_year'" _n _n
file close ptfile

local first_model 1

foreach y of local outcomes {
    di as txt "Running event study for outcome: `y'"

    reghdfe `y' `es_terms' `controls', ///
        absorb(province_id year) vce(cluster `cluster_var')

    estimates store es_`y'

    test es_pre4 es_pre3 es_pre2
    local pre_F = r(F)
    local pre_p = r(p)

    if `first_model' {
        outreg2 using "`es_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(`es_terms') ///
            addtext(Policy breakpoint, `policy_year', Base period, -1, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend joint p-value, `pre_p')
        outreg2 using "`es_txt'", replace ///
            ctitle(`y') dec(4) ///
            keep(`es_terms') ///
            addtext(Policy breakpoint, `policy_year', Base period, -1, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend joint p-value, `pre_p')
        local first_model 0
    }
    else {
        outreg2 using "`es_xls'", excel append ///
            ctitle(`y') dec(4) ///
            keep(`es_terms') ///
            addtext(Policy breakpoint, `policy_year', Base period, -1, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend joint p-value, `pre_p')
        outreg2 using "`es_txt'", append ///
            ctitle(`y') dec(4) ///
            keep(`es_terms') ///
            addtext(Policy breakpoint, `policy_year', Base period, -1, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend joint p-value, `pre_p')
    }

    capture file close ptfile
    file open ptfile using "`pt_txt'", write append
    file write ptfile "Outcome: `y'" _n
    file write ptfile "Pre-trend joint test F = `pre_F', p = `pre_p'" _n
    file write ptfile "Rule of thumb: parallel trends look acceptable if pre-period coefficients are individually insignificant and joint p > 0.10" _n _n
    file close ptfile

    coefplot es_`y', ///
        keep(`es_terms') ///
        vertical ///
        yline(0, lpattern(dash) lcolor(gs8)) ///
        xline(3.5, lpattern(shortdash) lcolor(gs10)) ///
        ciopts(recast(rcap) lcolor(navy)) ///
        msymbol(O) mcolor(navy) ///
        levels(95) ///
        coeflabels( ///
            es_pre4 = "<=-4" ///
            es_pre3 = "-3" ///
            es_pre2 = "-2" ///
            es_0    = "0" ///
            es_1    = "1" ///
            es_2    = "2" ///
            es_3    = "3" ///
            es_4    = ">=4" ///
        ) ///
        xtitle("Event Time (base period = -1)") ///
        ytitle("Coefficient and 95% CI") ///
        title("Event Study 2012: `y'")

    graph export "`figures'/EventStudy_2012_`y'.png", replace width(2400)
}

di as txt "========================================"
di as result "Event-study completed."
di as result "Tables saved to: `es_xls' and `pt_txt'"
di as result "Figures saved to: `figures'"
di as txt "========================================"
