version 17.0
clear all
macro drop _all
set more off
set linesize 255
capture log close

local root "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
local data "`root'/data/green_finance_pilot_city_wind"
local outdir "`root'/result/tables/0718_green_finance_pilot_city"
cap mkdir "`outdir'"
log using "`outdir'/green_finance_pilot_city_ddd_0718.log", text replace

foreach package in reghdfe ftools outreg2 {
    capture which `package'
    if _rc ssc install `package', replace
}

use "`data'/green_finance_pilot_city_panel_2005_2022.dta", clear
xtset city_id year

* Complete prefecture-level pilot units only. Ganjiang and Gui'an new areas
* are not mapped to whole cities. Province-by-year FE make comparisons within
* Zhejiang, Guangdong, and Xinjiang in the same year.
local sample "inrange(year, 2005, 2022)"

tempname results
postfile `results' str32 specification str24 outcome double b se p N clusters r2 ///
    using "`outdir'/green_finance_pilot_city_results.dta", replace

cap erase "`outdir'/Table_0718_CityPilot_DID_DDD.xls"
local firstcol 1

* Baseline city DID. This is estimable for GDP but pollution coverage is sparse.
foreach y in ln_gdp ln_so2 ln_so2_per_gdp {
    capture quietly reghdfe `y' pilot_post2017 if `sample', ///
        absorb(city_id province_year_id) vce(cluster city_id)
    if _rc continue
    scalar pvalue = 2 * ttail(e(df_r), abs(_b[pilot_post2017] / _se[pilot_post2017]))
    post `results' ("DID") ("`y'") (_b[pilot_post2017]) (_se[pilot_post2017]) ///
        (pvalue) (e(N)) (e(N_clust)) (e(r2))
    if `firstcol' {
        outreg2 using "`outdir'/Table_0718_CityPilot_DID_DDD.xls", excel replace ///
            keep(pilot_post2017) dec(4) ctitle("DID `y'") ///
            addtext(City FE, Yes, Province-Year FE, Yes, Cluster, City)
        local firstcol 0
    }
    else {
        outreg2 using "`outdir'/Table_0718_CityPilot_DID_DDD.xls", excel append ///
            keep(pilot_post2017) dec(4) ctitle("DID `y'") ///
            addtext(City FE, Yes, Province-Year FE, Yes, Cluster, City)
    }
}

* GDP event study over 2012-2022, with 2016 as the omitted year.
tempname event
postfile `event' int event_time double b se p pre_f pre_p N ///
    using "`outdir'/green_finance_pilot_city_gdp_event.dta", replace
foreach k in 5 4 3 2 {
    gen evt_m`k' = pilot_city * (year - 2017 == -`k')
}
foreach k in 0 1 2 3 4 5 {
    gen evt_p`k' = pilot_city * (year - 2017 == `k')
}
quietly reghdfe ln_gdp evt_m5 evt_m4 evt_m3 evt_m2 ///
    evt_p0 evt_p1 evt_p2 evt_p3 evt_p4 evt_p5 ///
    if inrange(year, 2012, 2022), absorb(city_id province_year_id) vce(cluster city_id)
quietly test evt_m5 evt_m4 evt_m3 evt_m2
scalar pre_f = r(F)
scalar pre_p = r(p)
foreach k in 5 4 3 2 {
    scalar pvalue = 2 * ttail(e(df_r), abs(_b[evt_m`k'] / _se[evt_m`k']))
    post `event' (-`k') (_b[evt_m`k']) (_se[evt_m`k']) (pvalue) ///
        (pre_f) (pre_p) (e(N))
}
foreach k in 0 1 2 3 4 5 {
    scalar pvalue = 2 * ttail(e(df_r), abs(_b[evt_p`k'] / _se[evt_p`k']))
    post `event' (`k') (_b[evt_p`k']) (_se[evt_p`k']) (pvalue) ///
        (pre_f) (pre_p) (e(N))
}
postclose `event'

* Resource-dependence DDD. The pilot-city x resource term is time invariant and
* absorbed by city FE; post2017 itself is absorbed by province-by-year FE.
foreach y in ln_gdp ln_so2 ln_so2_per_gdp {
    capture quietly reghdfe `y' pilot_post2017 post_resource pilot_post_resource ///
        if `sample' & !missing(resource_share_2016_z), ///
        absorb(city_id province_year_id) vce(cluster city_id)
    if _rc continue
    scalar pvalue = 2 * ttail(e(df_r), abs(_b[pilot_post_resource] / _se[pilot_post_resource]))
    post `results' ("DDD_resource") ("`y'") ///
        (_b[pilot_post_resource]) (_se[pilot_post_resource]) (pvalue) ///
        (e(N)) (e(N_clust)) (e(r2))
    outreg2 using "`outdir'/Table_0718_CityPilot_DID_DDD.xls", excel append ///
        keep(pilot_post2017 post_resource pilot_post_resource) dec(4) ///
        ctitle("DDD `y'") ///
        addtext(City FE, Yes, Province-Year FE, Yes, Cluster, City)
}

postclose `results'
use "`outdir'/green_finance_pilot_city_results.dta", clear
export delimited using "`outdir'/Table_0718_CityPilot_DID_DDD.csv", replace
list, noobs clean

use "`outdir'/green_finance_pilot_city_gdp_event.dta", clear
export delimited using "`outdir'/Table_0718_CityPilot_GDP_Event.csv", replace
list, noobs clean

log close
