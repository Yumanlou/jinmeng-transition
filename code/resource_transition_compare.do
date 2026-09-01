*******************************************************
* File: resource_transition_compare.do
* Purpose:
*   Compare efficiency transition vs structural transition
*   in resource-based regions (Shanxi and Inner Mongolia)
*   using Chinese province-year panel data.
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
* 1. Install required packages
*******************************************************

capture program drop ensure_pkg
program define ensure_pkg
    syntax, CHECKCMD(string) INSTALLPKG(string)
    cap which `checkcmd'
    if _rc {
        di as txt "Installing `installpkg' from SSC ..."
        cap noi ssc install `installpkg', replace
        cap which `checkcmd'
        if _rc {
            di as error "Package not available: `installpkg'"
            di as error "Please run manually: ssc install `installpkg', replace"
        }
    }
end

ensure_pkg, checkcmd(ftools) installpkg(ftools)
ensure_pkg, checkcmd(reghdfe) installpkg(reghdfe)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)

*******************************************************
* 2. Import data and build panel structure
*******************************************************

import delimited "`data'/final_data.1.3.4_did.csv", clear varnames(1) encoding(utf8)

* Generate a numeric province id from province names.
capture drop province_id_num
capture confirm numeric variable province_id
if _rc == 0 {
    gen province_id_num = province_id
}
else {
    encode province, gen(province_id_num)
}

* Reset treatment exactly as requested by the research design.
capture drop treat
gen byte treat = (province == "Shanxi" | province == "Inner Mongolia")
label define treat_lbl 0 "Other provinces" 1 "Resource-based regions"
label values treat treat_lbl

xtset province_id_num year

*******************************************************
* 3. Variable compatibility mapping
*******************************************************

* The raw file does not include all user-specified controls directly.
* This block creates comparable variables when feasible.

capture confirm variable gdp_pc
if _rc {
    capture confirm variable gdp
    capture confirm variable population
    if _rc == 0 {
        gen gdp_pc = gdp / population
        label var gdp_pc "GDP per capita"
    }
}

capture confirm variable industrial_share
if _rc {
    capture confirm variable sec_pctg
    if _rc == 0 {
        gen industrial_share = sec_pctg
        label var industrial_share "Industrial share proxy (sec_pctg)"
    }
}

capture confirm variable urbanization
if _rc {
    capture confirm variable urbanization_rate
    if _rc == 0 {
        gen urbanization = urbanization_rate
        label var urbanization "Urbanization proxy (urbanization_rate)"
    }
}

* The dataset does not contain a direct energy_intensity measure.
capture confirm variable energy_intensity
if _rc {
    di as error "Warning: energy_intensity is not available in the dataset and will be omitted."
}

local controls ""
foreach v in gdp_pc population industrial_share urbanization energy_intensity {
    capture confirm variable `v'
    if _rc == 0 local controls "`controls' `v'"
}

di as txt "Controls used in regressions: `controls'"

*******************************************************
* 4. Descriptive statistics
*******************************************************

capture log close desc_log
log using "`result'/tables/Descriptive_Statistics.smcl", replace name(desc_log)
tabstat gtfp_level gml_index coal_share_pctg ln_co2 sec_pctg industrial_so2 industrial_wastewater, ///
    statistics(n mean sd min p50 max) columns(statistics)
log close desc_log

*******************************************************
* 5. Group trend plots: resource-based vs other provinces
*******************************************************

preserve
collapse (mean) gtfp_level gml_index coal_share_pctg ln_co2, by(year treat)

twoway ///
    (line gtfp_level year if treat == 1, lcolor(navy) lwidth(medthick)) ///
    (line gtfp_level year if treat == 0, lcolor(maroon) lpattern(dash) lwidth(medthick)), ///
    title("Trend of GTFP Level") ///
    legend(order(1 "Resource-based regions" 2 "Other provinces")) ///
    xtitle("Year") ytitle("gtfp_level")
graph export "`result'/figures/Trend_gtfp_level.png", replace width(2200)

twoway ///
    (line gml_index year if treat == 1, lcolor(navy) lwidth(medthick)) ///
    (line gml_index year if treat == 0, lcolor(maroon) lpattern(dash) lwidth(medthick)), ///
    title("Trend of GML Index") ///
    legend(order(1 "Resource-based regions" 2 "Other provinces")) ///
    xtitle("Year") ytitle("gml_index")
graph export "`result'/figures/Trend_gml_index.png", replace width(2200)

twoway ///
    (line coal_share_pctg year if treat == 1, lcolor(navy) lwidth(medthick)) ///
    (line coal_share_pctg year if treat == 0, lcolor(maroon) lpattern(dash) lwidth(medthick)), ///
    title("Trend of Coal Share") ///
    legend(order(1 "Resource-based regions" 2 "Other provinces")) ///
    xtitle("Year") ytitle("coal_share_pctg")
graph export "`result'/figures/Trend_coal_share_pctg.png", replace width(2200)

twoway ///
    (line ln_co2 year if treat == 1, lcolor(navy) lwidth(medthick)) ///
    (line ln_co2 year if treat == 0, lcolor(maroon) lpattern(dash) lwidth(medthick)), ///
    title("Trend of Log CO2 Emissions") ///
    legend(order(1 "Resource-based regions" 2 "Other provinces")) ///
    xtitle("Year") ytitle("ln_co2")
graph export "`result'/figures/Trend_ln_co2.png", replace width(2200)

restore

*******************************************************
* 6. Core two-way fixed effects regressions
*******************************************************

* Note:
* treat is time-invariant within province, so under province FE
* its coefficient will be absorbed. The model is still estimated
* exactly as requested to keep the specification transparent.

local y_efficiency "gtfp_level gml_index"
local y_structural "coal_share_pctg ln_co2 sec_pctg"
local y_pollution "industrial_so2 industrial_wastewater"

local eff_file "`result'/tables/Table_Efficiency_Model.txt"
local str_file "`result'/tables/Table_Structural_Model.txt"
cap erase "`eff_file'"
cap erase "`str_file'"

local first_eff 1
foreach y of local y_efficiency {
    reghdfe `y' treat `controls', absorb(province_id_num year) vce(cluster province_id_num)
    if `first_eff' {
        outreg2 using "`eff_file'", replace ///
            ctitle(`y') dec(4) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_eff 0
    }
    else outreg2 using "`eff_file'", append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

local first_str 1
foreach y of local y_structural {
    reghdfe `y' treat `controls', absorb(province_id_num year) vce(cluster province_id_num)
    if `first_str' {
        outreg2 using "`str_file'", replace ///
            ctitle(`y') dec(4) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_str 0
    }
    else outreg2 using "`str_file'", append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

foreach y of local y_pollution {
    reghdfe `y' treat `controls', absorb(province_id_num year) vce(cluster province_id_num)
    outreg2 using "`str_file'", append ///
        ctitle(`y') dec(4) ///
        addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

*******************************************************
* 7. Trend-difference analysis
*******************************************************

capture drop year_centered treat_year_trend
summ year, meanonly
gen year_centered = year - r(min)
gen treat_year_trend = treat * year_centered

local trend_file "`result'/tables/Table_Trend_Difference.txt"
cap erase "`trend_file'"
local first_trend 1

foreach y in gtfp_level gml_index coal_share_pctg ln_co2 sec_pctg industrial_so2 industrial_wastewater {
    reghdfe `y' treat treat_year_trend `controls', absorb(province_id_num year) vce(cluster province_id_num)
    if `first_trend' {
        outreg2 using "`trend_file'", replace ///
            ctitle(`y') dec(4) ///
            keep(treat treat_year_trend) ///
            addtext(Model, Trend difference, Province FE, YES, Year FE, YES, Cluster, province_id_num)
        local first_trend 0
    }
    else outreg2 using "`trend_file'", append ///
        ctitle(`y') dec(4) ///
        keep(treat treat_year_trend) ///
        addtext(Model, Trend difference, Province FE, YES, Year FE, YES, Cluster, province_id_num)
}

*******************************************************
* 8. Finance-channel regressions
*******************************************************

local finance_file "`result'/tables/Table_Finance_Channel.txt"
cap erase "`finance_file'"

reghdfe gtfp_level credit bond equity fund carbon_finance `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", replace ///
    ctitle(gtfp_level) dec(4) ///
    addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)

reghdfe ln_co2 credit bond equity fund carbon_finance `controls', ///
    absorb(province_id_num year) vce(cluster province_id_num)
outreg2 using "`finance_file'", append ///
    ctitle(ln_co2) dec(4) ///
    addtext(Province FE, YES, Year FE, YES, Cluster, province_id_num)

*******************************************************
* 9. Save analysis-ready dataset
*******************************************************

save "`data'/final_data.1.3.4_did_resource_transition.dta", replace

di as result "========================================"
di as result "Analysis finished."
di as result "Tables:"
di as result "  `eff_file'"
di as result "  `str_file'"
di as result "  `finance_file'"
di as result "  `trend_file'"
di as result "Figures saved to `result'/figures"
di as result "========================================"

