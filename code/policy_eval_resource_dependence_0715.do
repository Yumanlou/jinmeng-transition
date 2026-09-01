*******************************************************
* File: policy_eval_resource_dependence_0715.do
* Purpose:
*   Test whether pre-policy resource dependence moderates
*   the effect of the 2012 green-credit policy shock in
*   coal-exposed provinces.
*******************************************************

version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root    "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data    "`root'/data"
local outdir  "`root'/result/tables/0715_resource_dependence"
cap mkdir "`root'/result/tables/0715_resource_dependence"

log using "`outdir'/policy_eval_resource_dependence_0715.log", text replace

capture which reghdfe
if _rc {
    ssc install reghdfe, replace
}
capture which outreg2
if _rc {
    ssc install outreg2, replace
}

import delimited "`data'/final_data.1.3.4_did_full_resource_0715.csv", ///
    clear varnames(1) encoding(utf8)

capture confirm numeric variable province_id
if _rc {
    encode province, gen(province_id)
}
capture confirm numeric variable year
if _rc {
    destring year, replace force
}
xtset province_id year

capture drop post2016_main coalexp_post16 post16_resdep ddd_resdep16
gen byte post2016_main = year >= 2016
gen double coalexp_post16 = post2016_main * coalexp_pre
gen double post16_resdep = post2016_main * resdep_pre
gen double ddd_resdep16 = post2016_main * coalexp_pre * resdep_pre

foreach dim in emp asset tax soe fisc {
    capture drop post16_resdep_`dim'_z ddd_resdep16_`dim'_z
    gen double post16_resdep_`dim'_z = post2016_main * resdep_`dim'_z
    gen double ddd_resdep16_`dim'_z = post2016_main * coalexp_pre * resdep_`dim'_z
}

label var coalexp_post "Post-2012 x pre-policy coal exposure"
label var post_resdep "Post-2012 x pre-policy resource dependence"
label var ddd_resdep "Post-2012 x coal exposure x resource dependence"

local controls "ln_gdp population sec_pctg urbanization_rate env_exp_share market_index"
local rhs_main "coalexp_post post_resdep ddd_resdep"
local outcomes_2012 "energy5_int coalterm_int industrial_so2 nox_total industrial_solid_waste coalshare5 coal_share_pctg ln_co2 therm_cap_sh therm_gen_sh"
local outcomes_2016 "wind_gen_sh windsolar_gen_sh wind_cap_sh"

*******************************************************
* 1. Composite resource-dependence index
* Lower-order interactions included:
*   post x coal exposure; post x resource dependence.
* coal exposure x resource dependence is time invariant and
* is absorbed by province fixed effects.
*******************************************************

local table_main "`outdir'/Table_0715_1_ResourceDependence_DDD.xls"
cap erase "`table_main'"

tempname main_results
postfile `main_results' str32 outcome int breakpoint double b_coal se_coal p_coal ///
    b_postres se_postres p_postres b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/resource_dependence_main_results.dta", replace

local first 1
foreach y of local outcomes_2012 {
    quietly reghdfe `y' `rhs_main' `controls' if !missing(resdep_pre), ///
        absorb(province_id year) vce(cluster province_id)

    scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post] / _se[coalexp_post]))
    scalar p_postres = 2 * ttail(e(df_r), abs(_b[post_resdep] / _se[post_resdep]))
    scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_resdep] / _se[ddd_resdep]))
    post `main_results' ("`y'") (2012) ///
        (_b[coalexp_post]) (_se[coalexp_post]) (p_coal) ///
        (_b[post_resdep]) (_se[post_resdep]) (p_postres) ///
        (_b[ddd_resdep]) (_se[ddd_resdep]) (p_ddd) ///
        (e(N)) (e(r2))

    if `first' {
        outreg2 using "`table_main'", excel replace ctitle(`y') dec(4) ///
            keep(coalexp_post post_resdep ddd_resdep) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
        local first 0
    }
    else {
        outreg2 using "`table_main'", excel append ctitle(`y') dec(4) ///
            keep(coalexp_post post_resdep ddd_resdep) ///
            addtext(Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}

foreach y of local outcomes_2016 {
    quietly reghdfe `y' coalexp_post16 post16_resdep ddd_resdep16 `controls' ///
        if !missing(resdep_pre), absorb(province_id year) vce(cluster province_id)

    scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post16] / _se[coalexp_post16]))
    scalar p_postres = 2 * ttail(e(df_r), abs(_b[post16_resdep] / _se[post16_resdep]))
    scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_resdep16] / _se[ddd_resdep16]))
    post `main_results' ("`y'") (2016) ///
        (_b[coalexp_post16]) (_se[coalexp_post16]) (p_coal) ///
        (_b[post16_resdep]) (_se[post16_resdep]) (p_postres) ///
        (_b[ddd_resdep16]) (_se[ddd_resdep16]) (p_ddd) ///
        (e(N)) (e(r2))

    outreg2 using "`table_main'", excel append ctitle(`y') dec(4) ///
        keep(coalexp_post16 post16_resdep ddd_resdep16) ///
        addtext(Policy breakpoint, 2016, Province FE, YES, Year FE, YES, Cluster, province_id)
}
postclose `main_results'

preserve
    use "`outdir'/resource_dependence_main_results.dta", clear
    export delimited using "`outdir'/Table_0715_1_ResourceDependence_DDD_coefficients.csv", replace
restore

*******************************************************
* 2. Standardized component decomposition
*******************************************************

local key_outcomes "energy5_int industrial_so2 nox_total industrial_solid_waste coalshare5 ln_co2 therm_cap_sh windsolar_gen_sh"
local dimensions "emp asset tax soe fisc"
local table_components "`outdir'/Table_0715_2_ResourceDependence_Components.xls"
cap erase "`table_components'"

tempname component_results
postfile `component_results' str32 outcome str12 dimension int breakpoint double ///
    b_coal se_coal p_coal b_postres se_postres p_postres ///
    b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/resource_dependence_component_results.dta", replace

local first_component 1
foreach dim of local dimensions {
    local postvar "post_resdep_`dim'_z"
    local triple "ddd_resdep_`dim'_z"
    local prevar "resdep_`dim'_z"

    foreach y of local key_outcomes {
        local breakpoint 2012
        local basevar "coalexp_post"
        if "`y'" == "windsolar_gen_sh" {
            local breakpoint 2016
            local basevar "coalexp_post16"
            local postvar "post16_resdep_`dim'_z"
            local triple "ddd_resdep16_`dim'_z"
        }

        quietly reghdfe `y' `basevar' `postvar' `triple' `controls' ///
            if !missing(`prevar'), absorb(province_id year) vce(cluster province_id)

        scalar p_coal = 2 * ttail(e(df_r), abs(_b[`basevar'] / _se[`basevar']))
        scalar p_postres = 2 * ttail(e(df_r), abs(_b[`postvar'] / _se[`postvar']))
        scalar p_ddd = 2 * ttail(e(df_r), abs(_b[`triple'] / _se[`triple']))
        post `component_results' ("`y'") ("`dim'") (`breakpoint') ///
            (_b[`basevar']) (_se[`basevar']) (p_coal) ///
            (_b[`postvar']) (_se[`postvar']) (p_postres) ///
            (_b[`triple']) (_se[`triple']) (p_ddd) ///
            (e(N)) (e(r2))

        if `first_component' {
            outreg2 using "`table_components'", excel replace ctitle(`y'_`dim') dec(4) ///
                keep(`basevar' `postvar' `triple') ///
                addtext(Resource dimension, `dim', Policy breakpoint, `breakpoint', Province FE, YES, Year FE, YES, Cluster, province_id)
            local first_component 0
        }
        else {
            outreg2 using "`table_components'", excel append ctitle(`y'_`dim') dec(4) ///
                keep(`basevar' `postvar' `triple') ///
                addtext(Resource dimension, `dim', Policy breakpoint, `breakpoint', Province FE, YES, Year FE, YES, Cluster, province_id)
        }
    }
}
postclose `component_results'

preserve
    use "`outdir'/resource_dependence_component_results.dta", clear
    export delimited using "`outdir'/Table_0715_2_ResourceDependence_Components_coefficients.csv", replace
restore

*******************************************************
* 3. Early interprovincial power-export condition
* The 2015 proxy uses Jan-Nov output over annual generation;
* interpret as a supplementary relative infrastructure measure.
*******************************************************

local grid_outcomes "therm_cap_sh therm_gen_sh wind_cap_sh wind_gen_sh windsolar_gen_sh"
local table_grid "`outdir'/Table_0715_3_EarlyPowerExport_DDD.xls"
cap erase "`table_grid'"

tempname grid_results
postfile `grid_results' str32 outcome double ///
    b_coal se_coal p_coal b_postgrid se_postgrid p_postgrid ///
    b_ddd se_ddd p_ddd N r2 ///
    using "`outdir'/early_power_export_results.dta", replace

local first_grid 1
foreach y of local grid_outcomes {
    quietly reghdfe `y' coalexp_post16 post16_grid_export_z ddd_grid_export16_z `controls' ///
        if !missing(grid_export_pre16_z), absorb(province_id year) vce(cluster province_id)

    scalar p_coal = 2 * ttail(e(df_r), abs(_b[coalexp_post16] / _se[coalexp_post16]))
    scalar p_postgrid = 2 * ttail(e(df_r), abs(_b[post16_grid_export_z] / _se[post16_grid_export_z]))
    scalar p_ddd = 2 * ttail(e(df_r), abs(_b[ddd_grid_export16_z] / _se[ddd_grid_export16_z]))
    post `grid_results' ("`y'") ///
        (_b[coalexp_post16]) (_se[coalexp_post16]) (p_coal) ///
        (_b[post16_grid_export_z]) (_se[post16_grid_export_z]) (p_postgrid) ///
        (_b[ddd_grid_export16_z]) (_se[ddd_grid_export16_z]) (p_ddd) ///
        (e(N)) (e(r2))

    if `first_grid' {
        outreg2 using "`table_grid'", excel replace ctitle(`y') dec(4) ///
            keep(coalexp_post16 post16_grid_export_z ddd_grid_export16_z) ///
            addtext(Condition, 2015 early power export proxy, Policy breakpoint, 2016, Province FE, YES, Year FE, YES, Cluster, province_id)
        local first_grid 0
    }
    else {
        outreg2 using "`table_grid'", excel append ctitle(`y') dec(4) ///
            keep(coalexp_post16 post16_grid_export_z ddd_grid_export16_z) ///
            addtext(Condition, 2015 early power export proxy, Policy breakpoint, 2016, Province FE, YES, Year FE, YES, Cluster, province_id)
    }
}
postclose `grid_results'

preserve
    use "`outdir'/early_power_export_results.dta", clear
    export delimited using "`outdir'/Table_0715_3_EarlyPowerExport_DDD_coefficients.csv", replace
restore

log close
