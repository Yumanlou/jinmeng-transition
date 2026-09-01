*******************************************************
* File: policy_eval_core_analysis.do
* Purpose:
*   Core empirical analysis for evaluating the 2010
*   Opinions on Investment and Financing Policies to
*   Support the Development of Circular Economy
*   (发改环资〔2010〕801号)
*
* Identification focus:
*   This do-file does NOT define the 2010 policy as a
*   "transition finance policy" ex ante. Instead, it
*   tests whether the policy changed financial resource
*   allocation and whether such financial reallocation
*   promoted structural transition outcomes, thereby
*   exhibiting a transition-oriented financial mechanism.
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
local code    "`root'/code"
local result  "`root'/result"

cap mkdir "`result'"
cap mkdir "`result'/tables"
cap mkdir "`result'/figures"

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
            di as error "Installation failed or was interrupted: `installpkg'."
            di as error "Please run manually in Stata: ssc install `installpkg', replace"
        }
        else {
            di as result "Installed successfully: `installpkg'"
        }
    }
    else {
        di as result "`checkcmd' already available."
    }
end

ensure_pkg, checkcmd(reghdfe) installpkg(reghdfe)
ensure_pkg, checkcmd(ftools) installpkg(ftools)
ensure_pkg, checkcmd(coefplot) installpkg(coefplot)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)

*******************************************************
* 2. Read data and basic checks
*******************************************************

import delimited "`data'/final_data.1.3.4_did.csv", ///
    clear varnames(1) encoding(utf8)

display "=============================="
display "Variable structure check"
display "=============================="
describe
codebook province_id year treat, compact

display "=============================="
display "Missing value check"
display "=============================="
misstable summarize

xtset province_id year

*******************************************************
* 3. Variable lists and consistency handling
*******************************************************

* Baseline outcomes
local y_structure  "sec_pctg coal_share_pctg"
local y_environment "ln_co2 industrial_so2 industrial_wastewater industrial_solid_waste"
local y_efficiency "gtfp_level gml_index"

* Event-study outcomes: prioritize gf_index if available, otherwise use gml_index.
cap confirm variable gf_index
if _rc == 0 {
    local y_event "ln_co2 coal_share_pctg gtfp_level gf_index"
}
else {
    local y_event "ln_co2 coal_share_pctg gtfp_level gml_index"
}

local controls "ln_gdp population urbanization_rate env_exp_share market_index"
local finance_vars "credit bond investment insurance equity fund carbon_finance gf_index"
local cluster_var "province_id"

display "=============================="
display "Descriptive statistics"
display "=============================="
capture log close descstat_log
log using "`result'/tables/descriptive_statistics.smcl", name(descstat_log) replace
tabstat ///
    sec_pctg coal_share_pctg ///
    ln_co2 industrial_so2 industrial_wastewater industrial_solid_waste ///
    gtfp_level gml_index ///
    credit bond investment insurance equity fund carbon_finance gf_index ///
    `controls' treat, ///
    statistics(n mean sd min p50 max) columns(statistics)
log close descstat_log

*******************************************************
* 4. Construct policy variables
*******************************************************

capture drop post did
gen post = year >= 2010
gen did  = treat * post

display "=============================="
display "Policy variable tabulations"
display "=============================="
tab treat
tab post
tab did

*******************************************************
* 5. Baseline DID regressions
*******************************************************

estimates clear

local baseline_xls "`result'/tables/Table_Baseline_DID.xls"
cap erase "`baseline_xls'"
local first_baseline 1

foreach y of local y_structure {
    reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store `y'
    if `first_baseline' {
        outreg2 using "`baseline_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_baseline 0
    }
    else outreg2 using "`baseline_xls'", excel append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

foreach y of local y_environment {
    reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store `y'
    outreg2 using "`baseline_xls'", excel append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

foreach y of local y_efficiency {
    reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store `y'
    outreg2 using "`baseline_xls'", excel append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

*******************************************************
* 6. Event-study regressions and plots
*******************************************************

estimates clear
local event_xls "`result'/tables/Table_Event_Study.xls"
cap erase "`event_xls'"
local first_event 1

foreach y of local y_event {
    reghdfe `y' did_pre2 did_post0 did_post1 did_post2 `controls', ///
        absorb(province_id year) vce(cluster `cluster_var')
    estimates store es_`y'
    if `first_event' {
        outreg2 using "`event_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(did_pre2 did_post0 did_post1 did_post2) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_event 0
    }
    else outreg2 using "`event_xls'", excel append ///
        ctitle(`y') dec(4) ///
        keep(did_pre2 did_post0 did_post1 did_post2) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)

    coefplot es_`y', ///
        keep(did_pre2 did_post0 did_post1 did_post2) ///
        vertical ///
        yline(0, lpattern(dash) lcolor(gs8)) ///
        xline(2.5, lpattern(shortdash) lcolor(gs10)) ///
        ciopts(recast(rcap) lcolor(navy)) ///
        msymbol(O) mcolor(navy) ///
        levels(95) ///
        coeflabels( ///
            did_pre2 = "-2" ///
            did_post0 = "0" ///
            did_post1 = "1" ///
            did_post2 = "2" ///
        ) ///
        xtitle("Event Time (base period = -1)") ///
        ytitle("Coefficient and 95% CI") ///
        title("Event Study: `y'")
    graph export "`result'/figures/EventStudy_`y'.png", replace width(2400)
}

*******************************************************
* 7. Mechanism I: Did policy change financial allocation?
*******************************************************

estimates clear
local mech1_xls "`result'/tables/Table_Mechanism_FinanceAllocation.xls"
cap erase "`mech1_xls'"
local first_mech1 1

foreach f of local finance_vars {
    reghdfe `f' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store m1_`f'
    if `first_mech1' {
        outreg2 using "`mech1_xls'", excel replace ///
            ctitle(`f') dec(4) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_mech1 0
    }
    else outreg2 using "`mech1_xls'", excel append ///
        ctitle(`f') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

*******************************************************
* 8. Mechanism II: Do financial variables promote transition?
*******************************************************

estimates clear
local mech2_xls "`result'/tables/Table_Mechanism_TransitionChannel.xls"
cap erase "`mech2_xls'"
local first_mech2 1

* Single-channel models with credit
foreach y in ln_co2 coal_share_pctg gtfp_level {
    reghdfe `y' credit `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store credit_`y'
    if `first_mech2' {
        outreg2 using "`mech2_xls'", excel replace ///
            ctitle(`y'_credit) dec(4) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_mech2 0
    }
    else outreg2 using "`mech2_xls'", excel append ///
        ctitle(`y'_credit) dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

* Joint financial channel model
reghdfe ln_co2 credit bond fund equity carbon_finance `controls', ///
    absorb(province_id year) vce(cluster `cluster_var')
estimates store multi_ln_co2
outreg2 using "`mech2_xls'", excel append ///
    ctitle(ln_co2_multi_finance) dec(4) ///
    addtext(Province FE, YES, Year FE, YES, Cluster, province_id)

*******************************************************
* 9. Heterogeneity: transition-oriented effects
*******************************************************

* Construct high-carbon indicator using province-level pre-policy mean.
capture drop pre_coal_mean pre_coal_median high_carbon did_highcarbon
bysort province_id: egen pre_coal_mean = mean(cond(year < 2010, coal_share_pctg, .))
egen pre_coal_median = median(pre_coal_mean)
gen high_carbon = pre_coal_mean > pre_coal_median if !missing(pre_coal_mean)
replace high_carbon = 0 if missing(high_carbon)
gen did_highcarbon = did * high_carbon

tab high_carbon

estimates clear
local hetero_xls "`result'/tables/Table_Heterogeneity_HighCarbon.xls"
cap erase "`hetero_xls'"
local first_hetero 1

foreach y in ln_co2 coal_share_pctg gtfp_level {
    reghdfe `y' did high_carbon did_highcarbon `controls', ///
        absorb(province_id year) vce(cluster `cluster_var')
    estimates store het_`y'
    if `first_hetero' {
        outreg2 using "`hetero_xls'", excel replace ///
            ctitle(`y') dec(4) ///
            keep(did high_carbon did_highcarbon) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_hetero 0
    }
    else outreg2 using "`hetero_xls'", excel append ///
        ctitle(`y') dec(4) ///
        keep(did high_carbon did_highcarbon) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
}

*******************************************************
* 10. Optional combined coefficient plot for heterogeneity
*******************************************************

coefplot ///
    (het_ln_co2, keep(did_highcarbon) label("ln_co2")) ///
    (het_coal_share_pctg, keep(did_highcarbon) label("coal_share_pctg")) ///
    (het_gtfp_level, keep(did_highcarbon) label("gtfp_level")), ///
    xline(0, lpattern(dash) lcolor(gs8)) ///
    ciopts(recast(rcap)) ///
    msymbol(D) ///
    title("Heterogeneous Policy Effects in High-Carbon Regions") ///
    xtitle("Coefficient on did x high_carbon") ///
    ytitle("")
graph export "`result'/figures/Heterogeneity_HighCarbon.png", replace width(2400)

*******************************************************
* 11. Robustness checks
*******************************************************

estimates clear
local robust_xls "`result'/tables/Table_Robustness.xls"
cap erase "`robust_xls'"
local first_robust 1

* 10.1 Alternative dependent variables
foreach y in co2_emissions gml_index industrial_so2 {
    reghdfe `y' did `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store alt_`y'
    if `first_robust' {
        outreg2 using "`robust_xls'", excel replace ///
            ctitle(alt_`y') dec(4) ///
            addtext(Specification, Alternative DV, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_robust 0
    }
    else outreg2 using "`robust_xls'", excel append ///
        ctitle(alt_`y') dec(4) ///
        addtext(Specification, Alternative DV, Province FE, YES, Year FE, YES, Cluster, province_id)
}

* 10.2 Add green finance pilot as an additional control
foreach y in ln_co2 coal_share_pctg gtfp_level {
    reghdfe `y' did green_finance_pilot `controls', ///
        absorb(province_id year) vce(cluster `cluster_var')
    estimates store pilot_`y'
    outreg2 using "`robust_xls'", excel append ///
        ctitle(pilot_`y') dec(4) ///
        addtext(Specification, Add green_finance_pilot, Province FE, YES, Year FE, YES, Cluster, province_id)
}

* 10.3 Placebo test with fake policy year = 2008
capture drop post_placebo did_placebo
gen post_placebo = year >= 2008
gen did_placebo  = treat * post_placebo

foreach y in ln_co2 coal_share_pctg gtfp_level {
    reghdfe `y' did_placebo `controls', absorb(province_id year) vce(cluster `cluster_var')
    estimates store placebo_`y'
    outreg2 using "`robust_xls'", excel append ///
        ctitle(placebo_`y') dec(4) ///
        addtext(Specification, Placebo 2008, Province FE, YES, Year FE, YES, Cluster, province_id)
}

*******************************************************
* 12. Save cleaned analysis dataset
*******************************************************

save "`data'/final_data.1.3.4_did_analysis.dta", replace

display "========================================"
display "All analyses completed successfully."
display "Tables saved to: `result'/tables"
display "Figures saved to: `result'/figures"
display "========================================"
