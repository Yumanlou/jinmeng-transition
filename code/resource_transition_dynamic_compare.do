*******************************************************
* File: resource_transition_dynamic_compare.do
* Purpose:
*   Identify whether resource-based regions mainly show
*   efficiency transition or structural transition.
*
* Core idea:
*   Since treat is time-invariant and absorbed by province FE,
*   identification should come from differential trends and
*   dynamic interactions between treat and time.
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

local root   "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data   "`root'/data"
local result "`root'/result"

cap mkdir "`result'"
cap mkdir "`result'/tables"
cap mkdir "`result'/figures"

*******************************************************
* 1. Packages
*******************************************************

capture program drop ensure_pkg
program define ensure_pkg
    syntax, CHECKCMD(string) INSTALLPKG(string)
    cap which `checkcmd'
    if _rc {
        cap noi ssc install `installpkg', replace
    }
end

ensure_pkg, checkcmd(ftools) installpkg(ftools)
ensure_pkg, checkcmd(reghdfe) installpkg(reghdfe)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)
ensure_pkg, checkcmd(coefplot) installpkg(coefplot)

*******************************************************
* 2. Import data and panel setup
*******************************************************

import delimited "`data'/final_data.1.3.4_did.csv", clear varnames(1) encoding(utf8)

capture drop province_id_num
capture confirm numeric variable province_id
if _rc == 0 gen province_id_num = province_id
else encode province, gen(province_id_num)

capture drop treat
gen byte treat = (province == "Shanxi" | province == "Inner Mongolia")
label define treat_lbl 0 "Other provinces" 1 "Shanxi/Inner Mongolia"
label values treat treat_lbl

xtset province_id_num year

*******************************************************
* 3. Control variable mapping
*******************************************************

capture confirm variable gdp_pc
if _rc {
    capture confirm variable gdp
    capture confirm variable population
    if _rc == 0 gen gdp_pc = gdp / population
}

capture confirm variable industrial_share
if _rc {
    capture confirm variable sec_pctg
    if _rc == 0 gen industrial_share = sec_pctg
}

capture confirm variable urbanization
if _rc {
    capture confirm variable urbanization_rate
    if _rc == 0 gen urbanization = urbanization_rate
}

local controls ""
foreach v in gdp_pc population industrial_share urbanization energy_intensity {
    capture confirm variable `v'
    if _rc == 0 local controls "`controls' `v'"
}

*******************************************************
* 4. Outcome blocks
*******************************************************

local y_eff "gtfp_level gml_index"
local y_str "coal_share_pctg ln_co2 sec_pctg"
local y_poll "industrial_so2 industrial_wastewater"

*******************************************************
* 5. Differential linear trend model
*******************************************************

capture drop year_centered treat_trend
summ year, meanonly
gen year_centered = year - r(min)
gen treat_trend = treat * year_centered

local trend_file "`result'/tables/Table_Transition_Trend_Compare.txt"
cap erase "`trend_file'"
local first_trend 1

foreach y in `y_eff' `y_str' `y_poll' {
    reghdfe `y' treat_trend `controls', absorb(province_id_num year) vce(cluster province_id_num)
    if `first_trend' {
        outreg2 using "`trend_file'", replace ///
            ctitle(`y') dec(4) keep(treat_trend) ///
            addtext(Model, Differential linear trend, Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_trend 0
    }
    else outreg2 using "`trend_file'", append ///
        ctitle(`y') dec(4) keep(treat_trend) ///
        addtext(Model, Differential linear trend, Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

*******************************************************
* 6. Period-comparison model
*    Compare whether resource-based regions moved more
*    in the later phase of green transition.
*******************************************************

capture drop post2013 post2016 treat_post2013 treat_post2016
gen byte post2013 = year >= 2013
gen byte post2016 = year >= 2016
gen treat_post2013 = treat * post2013
gen treat_post2016 = treat * post2016

local period_file "`result'/tables/Table_Transition_Period_Compare.txt"
cap erase "`period_file'"
local first_period 1

foreach y in `y_eff' `y_str' `y_poll' {
    reghdfe `y' treat_post2013 treat_post2016 `controls', absorb(province_id_num year) vce(cluster province_id_num)
    if `first_period' {
        outreg2 using "`period_file'", replace ///
            ctitle(`y') dec(4) keep(treat_post2013 treat_post2016) ///
            addtext(Model, Later-period interactions, Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_period 0
    }
    else outreg2 using "`period_file'", append ///
        ctitle(`y') dec(4) keep(treat_post2013 treat_post2016) ///
        addtext(Model, Later-period interactions, Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

*******************************************************
* 7. Dynamic event-time style path comparison
*    Base year: 2010
*******************************************************

local dyn_file "`result'/tables/Table_Transition_Dynamic_Path.txt"
cap erase "`dyn_file'"

foreach k in 2011 2013 2016 2019 2023 {
    capture drop d`k' treat_d`k'
    gen byte d`k' = year == `k'
    gen treat_d`k' = treat * d`k'
}

local dyn_terms "treat_d2011 treat_d2013 treat_d2016 treat_d2019 treat_d2023"
local first_dyn 1

foreach y in `y_eff' `y_str' {
    reghdfe `y' `dyn_terms' `controls', absorb(province_id_num year) vce(cluster province_id_num)
    estimates store dyn_`y'
    if `first_dyn' {
        outreg2 using "`dyn_file'", replace ///
            ctitle(`y') dec(4) keep(`dyn_terms') ///
            addtext(Model, Dynamic path comparison (base 2010), Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_dyn 0
    }
    else outreg2 using "`dyn_file'", append ///
        ctitle(`y') dec(4) keep(`dyn_terms') ///
        addtext(Model, Dynamic path comparison (base 2010), Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

*******************************************************
* 8. Dynamic coefficient plots
*******************************************************

foreach y in gtfp_level gml_index coal_share_pctg ln_co2 sec_pctg {
    coefplot dyn_`y', ///
        keep(`dyn_terms') vertical ///
        yline(0, lpattern(dash) lcolor(gs8)) ///
        ciopts(recast(rcap) lcolor(navy)) ///
        msymbol(O) mcolor(navy) ///
        coeflabels( ///
            treat_d2011 = "2011" ///
            treat_d2013 = "2013" ///
            treat_d2016 = "2016" ///
            treat_d2019 = "2019" ///
            treat_d2023 = "2023" ///
        ) ///
        xtitle("Year (base = 2010)") ///
        ytitle("Differential effect for resource-based regions") ///
        title("Dynamic Transition Path: `y'")
    graph export "`result'/figures/DynamicPath_`y'.png", replace width(2200)
}

*******************************************************
* 9. Finance and transition comparison
*******************************************************

local finance_file "`result'/tables/Table_Finance_Transition_Compare.txt"
cap erase "`finance_file'"

reghdfe gtfp_level credit bond equity fund carbon_finance insurance gf_index `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", replace ///
    ctitle(gtfp_level_efficiency) dec(4) ///
    addtext(Model, Finance to efficiency, Province FE, YES, Year FE, YES, Cluster, province_id_num)

reghdfe gml_index credit bond equity fund carbon_finance insurance gf_index `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", append ///
    ctitle(gml_index_efficiency) dec(4) ///
    addtext(Model, Finance to efficiency, Province FE, YES, Year FE, YES, Cluster, province_id_num)

reghdfe ln_co2 credit bond equity fund carbon_finance insurance gf_index `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", append ///
    ctitle(ln_co2_structural) dec(4) ///
    addtext(Model, Finance to structural transition, Province FE, YES, Year FE, YES, Cluster, province_id_num)

reghdfe coal_share_pctg credit bond equity fund carbon_finance insurance gf_index `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", append ///
    ctitle(coal_share_structural) dec(4) ///
    addtext(Model, Finance to structural transition, Province FE, YES, Year FE, YES, Cluster, province_id_num)

*******************************************************
* 10. Summary comparison sheet
*******************************************************

capture log close summary_log
log using "`result'/tables/Transition_Reading_Guide.smcl", replace name(summary_log)
display "Interpretation guide:"
display "1. Efficiency transition is stronger if treat_trend / dynamic coefficients are more positive for gtfp_level and gml_index."
display "2. Structural transition is stronger if resource-based regions show falling coal_share_pctg, falling ln_co2, and falling sec_pctg."
display "3. If efficiency indicators improve but structural indicators do not, transition is mainly efficiency-led rather than structure-led."
log close summary_log

save "`data'/final_data.1.3.4_did_dynamic_transition.dta", replace

display "========================================"
display "Dynamic transition analysis completed."
display "Main tables:"
display "  `trend_file'"
display "  `period_file'"
display "  `dyn_file'"
display "  `finance_file'"
display "Figures: `result'/figures/DynamicPath_*.png"
display "========================================"

