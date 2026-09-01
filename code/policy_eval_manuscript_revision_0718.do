*******************************************************
* File: policy_eval_manuscript_revision_0718.do
* Purpose:
*   Add the diagnostics required by the manuscript audit.
*   The script does not replace the reported 0518 estimates.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data"
local out  "`root'/result/tables/0718_manuscript_revision"
local fig  "`root'/result/figures/0718_manuscript_revision"

cap mkdir "`root'/result/tables/0718_manuscript_revision"
cap mkdir "`root'/result/figures/0718_manuscript_revision"
log using "`out'/policy_eval_manuscript_revision_0718.log", text replace

foreach cmd in reghdfe coefplot {
    capture which `cmd'
    if _rc {
        di as error "Required command not installed: `cmd'"
        exit 199
    }
}

import delimited "`data'/final_data.1.3.4_did_full_resource_v2_credit_greencredit_0716.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm numeric variable province_id
if _rc encode province, gen(province_id)
capture confirm numeric variable year
if _rc destring year, replace force
xtset province_id year

capture drop post2012_main post2016_main coal_exposure did_coal
gen byte post2012_main = year >= 2012
gen byte post2016_main = year >= 2016
gen double coal_exposure = coalexp_pre
gen double did_coal = post2012_main * coal_exposure

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local outcomes "gtfp_level gml_index energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh"

*******************************************************
* 1. Baseline estimates with confidence intervals and
*    actual estimation windows.
*******************************************************

tempname base
postfile `base' str32 outcome double b se p ci_low ci_high N r2 year_min year_max ///
    using "`out'/baseline_results.dta", replace

foreach y of local outcomes {
    quietly reghdfe `y' did_coal `controls', absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    scalar crit = invttail(e(df_r), .025)
    quietly summarize year if e(sample), meanonly
    post `base' ("`y'") (_b[did_coal]) (_se[did_coal]) (p) ///
        (_b[did_coal] - crit * _se[did_coal]) ///
        (_b[did_coal] + crit * _se[did_coal]) ///
        (e(N)) (e(r2)) (r(min)) (r(max))
}
postclose `base'

preserve
    use "`out'/baseline_results.dta", clear
    export delimited using "`out'/Table_0718_1_Baseline_CI_Windows.csv", replace
restore

*******************************************************
* 2. Descriptive statistics.
*******************************************************

local descvars "coal_exposure gtfp_level gml_index energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh nontherm_gen_sh wind_gen_sh windsolar_gen_sh wind_cap_sh green_credit_proxy resdep_pre"
tempname desc
postfile `desc' str40 variable double N mean sd p25 median p75 min max ///
    using "`out'/descriptive_statistics.dta", replace

foreach v of local descvars {
    quietly summarize `v', detail
    post `desc' ("`v'") (r(N)) (r(mean)) (r(sd)) (r(p25)) (r(p50)) ///
        (r(p75)) (r(min)) (r(max))
}
postclose `desc'

preserve
    use "`out'/descriptive_statistics.dta", clear
    export delimited using "`out'/Table_0718_2_Descriptive_Statistics.csv", replace
restore

*******************************************************
* 3. Continuous-exposure event studies.
*    Base period: 2011. The first bin is <= 2008.
*******************************************************

capture drop exp_m4 exp_m3 exp_m2 exp_0 exp_1 exp_2 exp_3 exp_4
gen double exp_m4 = coal_exposure * (year <= 2008)
gen double exp_m3 = coal_exposure * (year == 2009)
gen double exp_m2 = coal_exposure * (year == 2010)
gen double exp_0  = coal_exposure * (year == 2012)
gen double exp_1  = coal_exposure * (year == 2013)
gen double exp_2  = coal_exposure * (year == 2014)
gen double exp_3  = coal_exposure * (year == 2015)
gen double exp_4  = coal_exposure * (year >= 2016)

local es_terms "exp_m4 exp_m3 exp_m2 exp_0 exp_1 exp_2 exp_3 exp_4"
local es_outcomes "energy5_int coalterm_int coalshare5 industrial_so2"
tempname es
postfile `es' str32 outcome str12 event_term double b se p ci_low ci_high pretrend_p N ///
    using "`out'/event_study_results.dta", replace

foreach y of local es_outcomes {
    quietly reghdfe `y' `es_terms' `controls', absorb(province_id year) vce(cluster province_id)
    estimates store es0718_`y'
    quietly test exp_m4 exp_m3 exp_m2
    scalar pre_p = r(p)
    scalar crit = invttail(e(df_r), .025)

    foreach term of local es_terms {
        scalar term_p = 2 * ttail(e(df_r), abs(_b[`term'] / _se[`term']))
        post `es' ("`y'") ("`term'") (_b[`term']) (_se[`term']) (term_p) ///
            (_b[`term'] - crit * _se[`term']) ///
            (_b[`term'] + crit * _se[`term']) (pre_p) (e(N))
    }

    local outcome_title ""
    if "`y'" == "energy5_int" local outcome_title "Five-energy final intensity"
    if "`y'" == "coalterm_int" local outcome_title "Final-coal intensity"
    if "`y'" == "coalshare5" local outcome_title "Five-energy coal share"
    if "`y'" == "industrial_so2" local outcome_title "Industrial SO2 emissions"

    capture noisily coefplot es0718_`y', keep(`es_terms') vertical ///
        yline(0, lpattern(dash) lcolor(gs8)) ///
        ciopts(recast(rcap) lcolor(navy)) msymbol(O) mcolor(navy) ///
        coeflabels(exp_m4="<=2008" exp_m3="2009" exp_m2="2010" ///
                   exp_0="2012" exp_1="2013" exp_2="2014" ///
                   exp_3="2015" exp_4=">=2016") ///
        xtitle("Year bin; 2011 omitted") ytitle("Coal-exposure coefficient") ///
        title("`outcome_title'") graphregion(color(white)) legend(off)
    capture graph export "`fig'/EventStudy_`y'.pdf", replace
    capture graph export "`fig'/EventStudy_`y'.png", width(2000) replace
}
postclose `es'

preserve
    use "`out'/event_study_results.dta", clear
    export delimited using "`out'/Table_0718_3_Event_Studies.csv", replace
restore

*******************************************************
* 4. Alternative, predetermined exposure measures.
*    These avoid directly reusing coal terminal consumption.
*******************************************************

bysort province_id: egen double pre_thermal_gen_0811 = ///
    mean(cond(inrange(year, 2008, 2011), therm_gen_sh, .))
egen double coalexp_z = std(coal_exposure)
egen double pre_thermal_gen_z = std(pre_thermal_gen_0811)

capture drop post_coalexp_z post_thermal_gen_z post_coalprod_z post_cpbuild_z
gen double post_coalexp_z = post2012_main * coalexp_z
gen double post_thermal_gen_z = post2012_main * pre_thermal_gen_z
gen double post_coalprod_z = post2012_main * coal_production_share_z
gen double post_cpbuild_z = post2012_main * cpbuild_vintage_z

local alt_outcomes "energy5_int coalterm_int industrial_so2 coalshare5 ln_co2 therm_cap_sh therm_gen_sh"
tempname alt
postfile `alt' str32 outcome str28 exposure double b se p N r2 ///
    using "`out'/alternative_exposure_results.dta", replace

foreach y of local alt_outcomes {
    foreach spec in ///
        "post_coalexp_z coal_consumption_share" ///
        "post_thermal_gen_z thermal_generation_share" ///
        "post_coalprod_z coal_production_share" ///
        "post_cpbuild_z recent_coal_power_vintage" {

        gettoken x label : spec
        quietly reghdfe `y' `x' `controls' if !missing(`x'), ///
            absorb(province_id year) vce(cluster province_id)
        scalar p = 2 * ttail(e(df_r), abs(_b[`x'] / _se[`x']))
        post `alt' ("`y'") ("`label'") (_b[`x']) (_se[`x']) (p) (e(N)) (e(r2))
    }
}
postclose `alt'

preserve
    use "`out'/alternative_exposure_results.dta", clear
    export delimited using "`out'/Table_0718_4_Alternative_Exposures.csv", replace
restore

*******************************************************
* 5. Province-specific linear trends and exclusion of
*    five major coal-producing provinces.
*******************************************************

local robust_outcomes "energy5_int coalterm_int industrial_so2 coalshare5 ln_co2 therm_cap_sh therm_gen_sh"
tempname robust
postfile `robust' str32 outcome str28 specification double b se p N r2 ///
    using "`out'/robustness_results.dta", replace

foreach y of local robust_outcomes {
    quietly reghdfe `y' did_coal `controls', ///
        absorb(province_id year province_id#c.year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    post `robust' ("`y'") ("province_linear_trends") ///
        (_b[did_coal]) (_se[did_coal]) (p) (e(N)) (e(r2))

    quietly reghdfe `y' did_coal `controls' ///
        if !inlist(province, "Shanxi", "Neimenggu", "Shaanxi", "Xinjiang", "Ningxia"), ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    post `robust' ("`y'") ("exclude_five_coal_provinces") ///
        (_b[did_coal]) (_se[did_coal]) (p) (e(N)) (e(r2))
}
postclose `robust'

preserve
    use "`out'/robustness_results.dta", clear
    export delimited using "`out'/Table_0718_5_Robustness.csv", replace
restore

*******************************************************
* 6. Financial-side diagnostic using the observable
*    green-credit proxy. These are associations, not IV
*    or causal estimates.
*******************************************************

quietly summarize green_credit_proxy if !missing(green_credit_proxy)
gen double green_credit_proxy_z = (green_credit_proxy - r(mean)) / r(sd)
gen double lag_green_credit_proxy_z = L.green_credit_proxy_z

tempname gcresponse gcassoc
postfile `gcresponse' str20 sample double b se p N r2 ///
    using "`out'/green_credit_response_results.dta", replace

foreach sample in full no2017 {
    local condition "!missing(green_credit_proxy)"
    if "`sample'" == "no2017" local condition "!missing(green_credit_proxy) & year != 2017"
    quietly reghdfe green_credit_proxy did_coal `controls' if `condition', ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    post `gcresponse' ("`sample'") (_b[did_coal]) (_se[did_coal]) (p) (e(N)) (e(r2))
}
postclose `gcresponse'

local gc_outcomes "energy5_int coalterm_int industrial_so2 coalshare5 ln_co2 therm_cap_sh therm_gen_sh windsolar_gen_sh"
postfile `gcassoc' str32 outcome str18 timing double b se p N r2 ///
    using "`out'/green_credit_association_results.dta", replace

foreach y of local gc_outcomes {
    quietly reghdfe `y' green_credit_proxy_z `controls' if !missing(green_credit_proxy_z), ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[green_credit_proxy_z] / _se[green_credit_proxy_z]))
    post `gcassoc' ("`y'") ("contemporaneous") ///
        (_b[green_credit_proxy_z]) (_se[green_credit_proxy_z]) (p) (e(N)) (e(r2))

    quietly reghdfe `y' lag_green_credit_proxy_z `controls' if !missing(lag_green_credit_proxy_z), ///
        absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[lag_green_credit_proxy_z] / _se[lag_green_credit_proxy_z]))
    post `gcassoc' ("`y'") ("lagged") ///
        (_b[lag_green_credit_proxy_z]) (_se[lag_green_credit_proxy_z]) (p) (e(N)) (e(r2))
}
postclose `gcassoc'

preserve
    use "`out'/green_credit_response_results.dta", clear
    export delimited using "`out'/Table_0718_6_Green_Credit_Response.csv", replace
restore

preserve
    use "`out'/green_credit_association_results.dta", clear
    export delimited using "`out'/Table_0718_7_Green_Credit_Associations.csv", replace
restore

*******************************************************
* 7. Energy quantities in logs, controlling for GDP.
*    This avoids putting nominal GDP directly in the
*    denominator of the outcome.
*******************************************************

gen double ln_energy5_terminal = ln(energy5_terminal_10k_tce_approx) ///
    if energy5_terminal_10k_tce_approx > 0
gen double ln_coal_terminal = ln(coal_terminal_10k_tce_approx) ///
    if coal_terminal_10k_tce_approx > 0

tempname logenergy
postfile `logenergy' str32 outcome str28 specification double b se p pretrend_p N r2 ///
    using "`out'/log_energy_results.dta", replace

foreach y in ln_energy5_terminal ln_coal_terminal {
    quietly reghdfe `y' did_coal `controls', absorb(province_id year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    post `logenergy' ("`y'") ("baseline") (_b[did_coal]) (_se[did_coal]) (p) (.) (e(N)) (e(r2))

    quietly reghdfe `y' `es_terms' `controls', absorb(province_id year) vce(cluster province_id)
    quietly test exp_m4 exp_m3 exp_m2
    scalar pre_p = r(p)
    scalar post_b = _b[exp_4]
    scalar post_se = _se[exp_4]
    scalar post_p = 2 * ttail(e(df_r), abs(post_b / post_se))
    post `logenergy' ("`y'") ("event_long_run") (post_b) (post_se) (post_p) (pre_p) (e(N)) (e(r2))

    quietly reghdfe `y' did_coal `controls', ///
        absorb(province_id year province_id#c.year) vce(cluster province_id)
    scalar p = 2 * ttail(e(df_r), abs(_b[did_coal] / _se[did_coal]))
    post `logenergy' ("`y'") ("province_linear_trends") ///
        (_b[did_coal]) (_se[did_coal]) (p) (.) (e(N)) (e(r2))
}
postclose `logenergy'

preserve
    use "`out'/log_energy_results.dta", clear
    export delimited using "`out'/Table_0718_8_Log_Energy_Quantities.csv", replace
restore

log close
