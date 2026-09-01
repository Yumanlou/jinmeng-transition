clear all
set more off
set linesize 255

global ROOT "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型"
global DATA "$ROOT/data/green_credit_category_loo_iv"
global OUT "$ROOT/result/tables/0717_green_credit_category_loo_iv"

capture mkdir "$ROOT/result/tables/0717_green_credit_category_loo_iv"
capture log close
log using "$OUT/green_credit_category_loo_iv_0717.log", replace text

use "$DATA/green_credit_category_loo_iv_panel_2005_2022.dta", clear
encode province, gen(province_id)
xtset province_id year

capture which outreg2
if _rc ssc install outreg2, replace
capture erase "$OUT/Table_0717_Category_LOO_IV_FirstStage.xls"

tempname results
postfile `results' str48 specification str64 instrument double b se fstat pvalue n r2 ///
    using "$OUT/category_loo_iv_first_stage_results.dta", replace

local instruments iv_assets_assets_growth_loo iv_outlets_assets_growth_loo ///
    iv_assets_outlets_growth_loo iv_outlets_outlets_growth_loo ///
    iv_assets_assets_cum2011_loo iv_outlets_assets_cum2011_loo ///
    iv_assets_outlets_cum2011_loo iv_outlets_outlets_cum2011_loo ///
    iv_aw_acum_post iv_ow_acum_post iv_aw_ocum_post iv_ow_ocum_post
local labels assetW_assetG outletW_assetG assetW_outletG outletW_outletG ///
    assetW_assetCum outletW_assetCum assetW_outletCum outletW_outletCum ///
    assetW_assetCum_post outletW_assetCum_post assetW_outletCum_post outletW_outletCum_post

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
        outreg2 using "$OUT/Table_0717_Category_LOO_IV_FirstStage.xls", excel replace ///
            keep(`z') dec(4) ctitle("`label'") ///
            addtext(Province FE, Yes, Year FE, Yes, SE, Province clustered, Excluded-IV F, `fdisplay')
    }
    else {
        outreg2 using "$OUT/Table_0717_Category_LOO_IV_FirstStage.xls", excel append ///
            keep(`z') dec(4) ctitle("`label'") ///
            addtext(Province FE, Yes, Year FE, Yes, SE, Province clustered, Excluded-IV F, `fdisplay')
    }
    local ++i
}
postclose `results'

preserve
use "$OUT/category_loo_iv_first_stage_results.dta", clear
export delimited using "$OUT/Table_0717_Category_LOO_IV_FirstStage_Diagnostics.csv", replace
list, noobs clean
restore

log close
