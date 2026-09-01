*******************************************************
* File: policy_eval_0518_full_chain.do
* Purpose:
*   Rebuild the empirical chain using the 0518 full panel.
*
* Core design:
*   National 2012 green-credit policy shock interacted with
*   pre-policy coal exposure. Shanxi/Inner Mongolia are kept
*   for descriptive path comparison, not as the sole treatment
*   group.
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
cap mkdir "`tables'/0518_full_chain"
cap mkdir "`figures'/0518_full_chain"

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

ensure_pkg, checkcmd(ftools) installpkg(ftools)
ensure_pkg, checkcmd(reghdfe) installpkg(reghdfe)
ensure_pkg, checkcmd(outreg2) installpkg(outreg2)
ensure_pkg, checkcmd(coefplot) installpkg(coefplot)

*******************************************************
* 2. Read 0518 full panel
*******************************************************

import delimited "`data'/final_data.1.3.4_did_full_0518.csv", ///
    clear varnames(1) encoding(utf8)

tempfile policy_text_panel
preserve
    import delimited "`data'/policy_texts/jinmeng_policy_text_year_panel_2000_2023.csv", ///
        clear varnames(1) encoding(utf8)
    replace province = "Shanxi" if ustrregexm(province, "山西")
    replace province = "Neimenggu" if ustrregexm(province, "内蒙古")
    capture destring year, replace force

    label var policy_count "Policy documents"
    label var docs_with_content "Policy documents with full text"
    label var content_coverage "Full-text coverage"
    label var content_chars "Policy text characters"
    label var green_finance_per_10k_chars "Green-finance policy words per 10k chars"
    label var green_finance_doc_share "Share of policies mentioning green finance"
    label var coal_clean_per_10k_chars "Coal-clean policy words per 10k chars"
    label var coal_clean_doc_share "Share of policies mentioning coal clean-up"
    label var pollution_control_per_10k_chars "Pollution-control words per 10k chars"
    label var pollution_control_doc_share "Share of policies mentioning pollution control"
    label var renewable_per_10k_chars "Renewable policy words per 10k chars"
    label var renewable_doc_share "Share of policies mentioning renewables"

    save `policy_text_panel', replace
restore

merge m:1 province year using `policy_text_panel', nogen keep(master match)

capture confirm numeric variable province_id
if _rc {
    encode province, gen(province_id)
}

capture confirm numeric variable year
if _rc {
    destring year, replace force
}

xtset province_id year

*******************************************************
* 3. Policy and exposure variables
*******************************************************

local policy_year 2012

capture drop post2012_main post2016_main coal_exposure did_coal did_coal_late
gen byte post2012_main = year >= `policy_year'
gen byte post2016_main = year >= 2016
gen double coal_exposure = coalexp_pre
gen double did_coal = coalexp_post
gen double did_coal_late = post2016_main * coal_exposure

label var coal_exposure "Pre-policy coal terminal exposure, 2008-2011"
label var did_coal "Post-2012 x pre-policy coal exposure"
label var did_coal_late "Post-2016 x pre-policy coal exposure"

capture drop z_pre_nontherm_cap z_early_wind_cap z_early_wind_gen ///
    lowcarbon_endowment post2012_lowcarbon post2016_lowcarbon ///
    ddd_lowcarbon ddd_lowcarbon_late
egen double z_pre_nontherm_cap = std(pre_nontherm_cap)
egen double z_early_wind_cap   = std(early_wind_cap)
egen double z_early_wind_gen   = std(early_wind_gen)
egen double lowcarbon_endowment = rowmean(z_pre_nontherm_cap z_early_wind_cap z_early_wind_gen)
gen double post2012_lowcarbon = post2012_main * lowcarbon_endowment
gen double post2016_lowcarbon = post2016_main * lowcarbon_endowment
gen double ddd_lowcarbon = post2012_main * coal_exposure * lowcarbon_endowment
gen double ddd_lowcarbon_late = post2016_main * coal_exposure * lowcarbon_endowment

label var z_pre_nontherm_cap "Z-score of pre-policy nonthermal capacity share"
label var z_early_wind_cap "Z-score of early wind capacity share"
label var z_early_wind_gen "Z-score of early wind generation share"
label var lowcarbon_endowment "Low-carbon endowment index"
label var post2012_lowcarbon "Post-2012 x low-carbon endowment"
label var post2016_lowcarbon "Post-2016 x low-carbon endowment"
label var ddd_lowcarbon "Post-2012 x coal exposure x low-carbon endowment"
label var ddd_lowcarbon_late "Post-2016 x coal exposure x low-carbon endowment"

capture drop treat_jm did_jm
gen byte treat_jm = inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia")
gen double did_jm = treat_jm * post2012_main

capture drop nmg_jm nmg_post2012
gen byte nmg_jm = province == "Neimenggu" if treat_jm == 1
gen double nmg_post2012 = nmg_jm * post2012_main
label var nmg_post2012 "Inner Mongolia x post-2012"

*******************************************************
* 4. Controls
*******************************************************

capture drop gdp_pc industrial_share urbanization
gen double gdp_pc = gdp / population if !missing(gdp, population) & population > 0
gen double industrial_share = sec_pctg
gen double urbanization = urbanization_rate

* Baseline controls follow the original do files, but use aliases
* where needed. The full-control sample starts in 2007 because
* environmental fiscal expenditure is unavailable before then.
local controls_full "ln_gdp population industrial_share urbanization env_exp_share market_index"
local controls_core "ln_gdp population industrial_share market_index"
local cluster_var "province_id"

*******************************************************
* 5. Helper: run one block and append outreg2 tables
*******************************************************

capture program drop run_block
program define run_block
    syntax, OUTCOMES(string) RHS(string) KEEP(string) OUTNAME(string) TITLE(string) [CONTROLS(string)]

    local out_xls "`c(pwd)'/result/tables/0518_full_chain/`outname'.xls"
    cap erase "`out_xls'"

    local first_model 1
    foreach y of local outcomes {
        capture confirm variable `y'
        if _rc {
            di as error "Outcome `y' not found; skipped."
            continue
        }

        di as txt "Running `title': outcome = `y'"
        quietly reghdfe `y' `rhs' `controls', absorb(province_id year) vce(cluster province_id)

        if `first_model' {
            outreg2 using "`out_xls'", excel replace ///
                ctitle(`y') dec(4) keep(`keep') ///
                addtext(Design, "`title'", Policy breakpoint, 2012, Province FE, YES, Year FE, YES, Cluster, province_id)
            local first_model 0
        }
        else {
            outreg2 using "`out_xls'", excel append ///
                ctitle(`y') dec(4) keep(`keep') ///
                addtext(Design, "`title'", Policy breakpoint, 2012, Province FE, YES, Year FE, YES, Cluster, province_id)
        }
    }
end

*******************************************************
* 6. Main chain: efficiency, pollution, structure
*******************************************************

local y_eff "gtfp_level gml_index energy5_int coalterm_int"
run_block, ///
    outcomes("`y_eff'") ///
    rhs("did_coal") ///
    keep("did_coal") ///
    outname("Table_0518_1_Efficiency") ///
    title("Continuous DID: efficiency repair") ///
    controls("`controls_full'")

local y_poll_main "industrial_so2 nox_total"
run_block, ///
    outcomes("`y_poll_main'") ///
    rhs("did_coal") ///
    keep("did_coal") ///
    outname("Table_0518_2_Pollution_Main") ///
    title("Continuous DID: pollution treatment") ///
    controls("`controls_full'")

local y_poll_appendix "pm_total industrial_solid_waste industrial_wastewater"
run_block, ///
    outcomes("`y_poll_appendix'") ///
    rhs("did_coal") ///
    keep("did_coal") ///
    outname("Table_0518_2b_Pollution_Appendix") ///
    title("Continuous DID: pollution appendix") ///
    controls("`controls_full'")

local y_structure "coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh"
run_block, ///
    outcomes("`y_structure'") ///
    rhs("did_coal") ///
    keep("did_coal") ///
    outname("Table_0518_3_Structure_Lockin") ///
    title("Continuous DID: structural lock-in") ///
    controls("`controls_full'")

*******************************************************
* 7. Low-carbon endowment moderation
*******************************************************

local lowcarbon_file "`tables'/0518_full_chain/Table_0518_4_LowCarbon_Moderation.xls"
cap erase "`lowcarbon_file'"

local first_low 1

foreach spec in ///
    "nontherm_gen_sh did_coal_late post2016_lowcarbon ddd_lowcarbon_late Low-carbon-endowment-post2016" ///
    "wind_gen_sh did_coal_late post2016_lowcarbon ddd_lowcarbon_late Low-carbon-endowment-post2016" ///
    "windsolar_gen_sh did_coal_late post2016_lowcarbon ddd_lowcarbon_late Low-carbon-endowment-post2016" ///
    "wind_cap_sh did_coal_late post2016_lowcarbon ddd_lowcarbon_late Low-carbon-endowment-post2016" {

    gettoken y rest : spec
    gettoken base rest : rest
    gettoken lower rest : rest
    gettoken triple label : rest

    di as txt "Running low-carbon moderation: outcome = `y', base = `base', lower = `lower', triple = `triple'"
    quietly reghdfe `y' `base' `lower' `triple' `controls_full', ///
        absorb(province_id year) vce(cluster `cluster_var')

    if `first_low' {
        outreg2 using "`lowcarbon_file'", excel replace ///
            ctitle(`y') dec(4) keep(`base' `lower' `triple') ///
            addtext(Design, "Continuous DID plus low-carbon endowment", Endowment proxy, "`label'", Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_low 0
    }
    else {
        outreg2 using "`lowcarbon_file'", excel append ///
            ctitle(`y') dec(4) keep(`base' `lower' `triple') ///
            addtext(Design, "Continuous DID plus low-carbon endowment", Endowment proxy, "`label'", Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

*******************************************************
* 8. Continuous-exposure event-study check
*    Base period: 2011.
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

label var exp_m4 "Exposure x event<=-4"
label var exp_m3 "Exposure x event=-3"
label var exp_m2 "Exposure x event=-2"
label var exp_0  "Exposure x event=0"
label var exp_1  "Exposure x event=1"
label var exp_2  "Exposure x event=2"
label var exp_3  "Exposure x event=3"
label var exp_4  "Exposure x event>=4"

local es_terms "exp_m4 exp_m3 exp_m2 exp_0 exp_1 exp_2 exp_3 exp_4"
local es_outcomes "gtfp_level gml_index industrial_so2 coalshare5 therm_gen_sh windsolar_gen_sh"

local es_xls "`tables'/0518_full_chain/Table_0518_5_EventStudy_ContinuousExposure.xls"
local pt_txt "`tables'/0518_full_chain/Table_0518_5_Pretrend_Tests.txt"
cap erase "`es_xls'"
cap erase "`pt_txt'"

capture file close ptfile
file open ptfile using "`pt_txt'", write replace
file write ptfile "Continuous-exposure event-study; base period = 2011" _n _n
file close ptfile

local first_es 1
foreach y of local es_outcomes {
    di as txt "Running continuous event study for outcome: `y'"
    quietly reghdfe `y' `es_terms' `controls_full', ///
        absorb(province_id year) vce(cluster `cluster_var')

    estimates store es0518_`y'

    test exp_m4 exp_m3 exp_m2
    local pre_F = r(F)
    local pre_p = r(p)

    if `first_es' {
        outreg2 using "`es_xls'", excel replace ///
            ctitle(`y') dec(4) keep(`es_terms') ///
            addtext(Policy breakpoint, 2012, Base period, 2011, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend p-value, `pre_p')
        local first_es 0
    }
    else {
        outreg2 using "`es_xls'", excel append ///
            ctitle(`y') dec(4) keep(`es_terms') ///
            addtext(Policy breakpoint, 2012, Base period, 2011, Province FE, YES, Year FE, YES, Cluster, province_id, Pre-trend p-value, `pre_p')
    }

    capture file close ptfile
    file open ptfile using "`pt_txt'", write append
    file write ptfile "Outcome: `y'" _n
    file write ptfile "Pre-trend joint test F = `pre_F', p = `pre_p'" _n _n
    file close ptfile

    coefplot es0518_`y', ///
        keep(`es_terms') vertical ///
        yline(0, lpattern(dash) lcolor(gs8)) ///
        xline(3.5, lpattern(shortdash) lcolor(gs10)) ///
        ciopts(recast(rcap) lcolor(navy)) ///
        msymbol(O) mcolor(navy) ///
        coeflabels( ///
            exp_m4 = "<=-4" ///
            exp_m3 = "-3" ///
            exp_m2 = "-2" ///
            exp_0  = "0" ///
            exp_1  = "1" ///
            exp_2  = "2" ///
            exp_3  = "3" ///
            exp_4  = ">=4" ///
        ) ///
        xtitle("Event time, base = 2011") ///
        ytitle("Coefficient on pre-policy coal exposure") ///
        title("Continuous Exposure Event Study: `y'")

    graph export "`figures'/0518_full_chain/EventStudy_0518_`y'.png", replace width(2400)
}

*******************************************************
* 9. Shanxi and Inner Mongolia descriptive path
*******************************************************

preserve
    keep if inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia")
    keep province year gtfp_level gml_index industrial_so2 nox_total ///
        coalshare5 ln_co2 therm_cap_sh therm_gen_sh nontherm_gen_sh ///
        wind_cap_sh solar_cap_sh windsolar_cap_sh wind_gen_sh ///
        solar_gen_sh windsolar_gen_sh ///
        policy_count docs_with_content content_coverage content_chars ///
        green_finance_per_10k_chars green_finance_doc_share ///
        coal_clean_per_10k_chars coal_clean_doc_share ///
        pollution_control_per_10k_chars pollution_control_doc_share ///
        renewable_per_10k_chars renewable_doc_share
    export delimited using "`tables'/0518_full_chain/Table_0518_6_JinMeng_Path_Data.csv", replace
restore

preserve
    keep if inlist(province, "Shanxi", "Neimenggu", "Inner Mongolia")
    gen byte period_pre = year < 2012
    gen byte period_mid = inrange(year, 2012, 2016)
    gen byte period_late = year >= 2017
    gen str12 period = ""
    replace period = "pre_2000_2011" if period_pre == 1
    replace period = "mid_2012_2016" if period_mid == 1
    replace period = "late_2017_2023" if period_late == 1
    collapse (mean) gtfp_level gml_index industrial_so2 nox_total ///
        coalshare5 ln_co2 therm_cap_sh therm_gen_sh nontherm_gen_sh ///
        wind_cap_sh solar_cap_sh windsolar_cap_sh wind_gen_sh ///
        solar_gen_sh windsolar_gen_sh ///
        policy_count docs_with_content content_coverage content_chars ///
        green_finance_per_10k_chars green_finance_doc_share ///
        coal_clean_per_10k_chars coal_clean_doc_share ///
        pollution_control_per_10k_chars pollution_control_doc_share ///
        renewable_per_10k_chars renewable_doc_share, by(province period)
    export delimited using "`tables'/0518_full_chain/Table_0518_6_JinMeng_Period_Means.csv", replace
restore

*******************************************************
* 9b. Jin-Meng policy-text path regressions
*     These are case-path regressions for the two resource
*     provinces only, not part of the national DID identification.
*******************************************************

local text_file "`tables'/0518_full_chain/Table_0518_7_JinMeng_Policy_Text_Path.xls"
cap erase "`text_file'"

local first_text 1
local text_outcomes ///
    green_finance_per_10k_chars green_finance_doc_share ///
    coal_clean_per_10k_chars coal_clean_doc_share ///
    pollution_control_per_10k_chars pollution_control_doc_share ///
    renewable_per_10k_chars renewable_doc_share

foreach y of local text_outcomes {
    capture confirm variable `y'
    if _rc {
        di as error "Policy-text outcome `y' not found; skipped."
        continue
    }

    di as txt "Running Jin-Meng policy-text path regression: outcome = `y'"
    quietly reghdfe `y' nmg_post2012 if treat_jm == 1 & !missing(`y'), ///
        absorb(province_id year) vce(robust)

    if `first_text' {
        outreg2 using "`text_file'", excel replace ///
            ctitle(`y') dec(4) keep(nmg_post2012) ///
            addtext(Design, "Two-province text path", Interpretation, "Inner Mongolia relative to Shanxi after 2012", Province FE, YES, Year FE, YES, Inference, "Descriptive only")
        local first_text 0
    }
    else {
        outreg2 using "`text_file'", excel append ///
            ctitle(`y') dec(4) keep(nmg_post2012) ///
            addtext(Design, "Two-province text path", Interpretation, "Inner Mongolia relative to Shanxi after 2012", Province FE, YES, Year FE, YES, Inference, "Descriptive only")
    }
}

*******************************************************
* 10. Save analysis dataset
*******************************************************

save "`data'/final_data.1.3.4_did_full_0518_analysis.dta", replace

di as txt "========================================"
di as result "0518 full empirical chain completed."
di as result "Tables saved to: `tables'/0518_full_chain"
di as result "Figures saved to: `figures'/0518_full_chain"
di as result "Analysis dataset saved to: `data'/final_data.1.3.4_did_full_0518_analysis.dta"
di as txt "========================================"
