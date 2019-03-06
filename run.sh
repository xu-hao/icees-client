#!/bin/bash
cohort2=$1 || "Prednisone TotalEDVisits TotalEDInpatientVisits"
feature2=$2 || "Sex2 ObesityDx DiabetesDx"
for cohort in $cohort2
do
    for ftr in $feature2
    do
	echo cohort: $cohort ftr: $ftr
        python tidbit.py $cohort $ftr > WF5_ICEES_${cohort}_${ftr}
    done
done
