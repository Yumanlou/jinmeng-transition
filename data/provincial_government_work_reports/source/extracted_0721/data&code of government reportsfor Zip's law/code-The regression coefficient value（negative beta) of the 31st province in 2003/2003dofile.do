cd   "e:\f2003\"

// 先在e盘建一个f2003文件夹

clear all
 import excel "e:\wordfreq2003.xlsx", sheet("Sheet1")

// excel的原始数据放在e:\盘，其他的都放在e:\f2003\下

drop A
stack B-BWI,into(word wordfreq)
save "e:\f2003\2003data"

//    上述是将word文件整理为dta文件


clear all
use  "e:\f2003\2003data"
gen var3=_n
forvalues id=31(31)30938{
          preserve
                 capture{
                         keep if var3==`id'
	         save `id'.dta,replace
                         }
          restore
             
}


//    上述是将每个省提取出来，1表示第1个省


clear all

use  31.dta, clear
forvalues j=62(31)30938{
     
             append using `j'.dta
           
}
save "e:\f2003\2003data-31"

//   上面 

clear all

use "e:\f2003\2003data-31"

duplicates drop wordfreq,force

drop var3
gen rank=_n

gen lnwordfreq=log(wordfreq)
gen lnrank=log(rank)

reg  lnrank lnwordfreq
twoway scatter lnrank lnwordfreq


