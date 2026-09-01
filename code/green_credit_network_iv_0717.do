clear all
set more off
set linesize 255

global ROOT "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
global DATA "$ROOT/data/green_credit_network_iv"
global OUT "$ROOT/result/tables/0717_green_credit_network_iv"

capture mkdir "$ROOT/result/tables/0717_green_credit_network_iv"
capture log close
log using "$OUT/green_credit_network_iv_0717.log", replace text

use "$DATA/green_credit_network_iv_panel_2005_2022.dta", clear
encode province, gen(province_id)
xtset province_id year

capture which outreg2
if _rc ssc install outreg2, replace
capture erase "$OUT/Table_0717_Network_IV_FirstStage.xls"

tempname results
postfile `results' str32 specification str40 instrument double b se fstat pvalue n r2 ///
    using "$OUT/network_iv_first_stage_results.dta", replace

local instruments z_iv_network_post2012 z_iv_network_national_level ///
    z_iv_network_national_change z_iv_network_national_dev2011
local labels policy_network national_level national_change national_dev2011

local i = 1
foreach z of local instruments {
    local label : word `i' of `labels'
    quietly areg green_credit_level `z' i.year, absorb(province_id) vce(cluster province_id)
    estimates store fs_`label'
    test `z'
    local fstat = r(F)
    local pvalue = r(p)
    local b = _b[`z']
    local se = _se[`z']
    local n = e(N)
    local r2 = e(r2)
    local fdisplay : display %6.2f `fstat'
    post `results' ("`label'") ("`z'") (`b') (`se') (`fstat') (`pvalue') (`n') (`r2')

    if `i' == 1 {
        outreg2 using "$OUT/Table_0717_Network_IV_FirstStage.xls", excel replace ///
            keep(`z') dec(4) ctitle("`label'") ///
            addtext(Province FE, Yes, Year FE, Yes, SE, Province clustered, Excluded-IV F, `fdisplay')
    }
    else {
        outreg2 using "$OUT/Table_0717_Network_IV_FirstStage.xls", excel append ///
            keep(`z') dec(4) ctitle("`label'") ///
            addtext(Province FE, Yes, Year FE, Yes, SE, Province clustered, Excluded-IV F, `fdisplay')
    }
    local ++i
}
postclose `results'

preserve
use "$OUT/network_iv_first_stage_results.dta", clear
export delimited using "$OUT/Table_0717_Network_IV_FirstStage_Diagnostics.csv", replace
list, noobs clean
restore

log close
