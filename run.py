import tidbit
import sys

cmd = sys.argv[1]

if cmd == "icees":
    if len(sys.argv) > 2:
        cohorts = sys.argv[2].split(",")
    else:
        cohorts = tidbit.define_cohort_input.keys()

    if len(sys.argv) > 3:
        features = sys.argv[3].split(",")
    else:
        features = tidbit.association_to_all_features_input.keys()
    
    for cohort in cohorts:
        for ftr in features:
            print(cohort, ftr)
            tidbit.run_e(cohort, ftr)

elif cmd == "format":
    if len(sys.argv) > 2:
        fmt = sys.argv[2]
    else:
        fmt = "grid"

    if len(sys.argv) > 3:
        cohorts = sys.argv[3].split(",")
    else:
        cohorts = tidbit.define_cohort_input.keys()

    if len(sys.argv) > 4:
        features = sys.argv[4].split(",")
    else:
        features = tidbit.association_to_all_features_input.keys()
    
    for cohort in cohorts:
        for ftr in features:
            print(cohort, ftr)
            tidbit.run_f(cohort, ftr, fmt)

