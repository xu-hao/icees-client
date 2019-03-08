import icees.iceesclient as ic
import sys
import numpy as np
from format import format_tabular
from features import features
import json
from scipy.stats import chisquare, chi2_contingency
import pickle

define_cohort_input = {
    "Prednisone" : {
        "Prednisone": {
            "operator": "=",
            "value": 1
        }
    },
    "TotalEDVisits" : {
        "TotalEDVisits": {
            "operator" : ">=",
            "value": 2
        }
    },
    "TotalEDInpatientVisits" : {
        "TotalEDInpatientVisits": {
            "operator" : ">=",
            "value": 2
        }
    },
    "all" : {}
}

association_to_all_features_input = {
    "Sex2": {
        "feature":{
            "Sex2": {
                "operator": "=",
                "value":"Female"
            }
        },
        "maximum_p_value" : 0.1
    },
    "ObesityDx": {
        "feature":{
            "ObesityDx": {
                "operator": "=",
                "value":0
            }
        },
        "maximum_p_value" : 0.1
    },
    "DiabetesDx": {
        "feature":{
            "DiabetesDx": {
                "operator": "=",
                "value":0
            }
        },
        "maximum_p_value" : 0.1
    },
    "Prednisone" : {
        "feature" : {
            "Prednisone": {
                "operator": "=",
                "value": 0
            }
        },
        "maximum_p_value" : 0.1
    }
}

def run(e, x):
    cohort = ic.define_cohort(define_cohort_input[e])
    
    cohort_id = cohort["return value"]["cohort_id"]
    
#    print(x)
    res = ic.association_to_all_features(x, cohort_id)
#    print("result =", res)
    return res


def dx(row):
    feature_b = row["feature_b"]
    return feature_b["biolink_class"] in ["disease", "disease_or_phenotypic_feature"] and feature_b["feature_name"][-2:] == "Dx"
    

def chemical_substance(row):
    feature_b = row["feature_b"]
    return feature_b["biolink_class"] in ["chemical_substance", "drug"]


def extract_data_from_results(l):
    def extract_data_from_result(x):
        # feature_name = x["feature_b"]["feature_name"]
        # identifiers = ic.identifiers(feature_name.split("_")[0])
        # x["feature_b"].update({
        #     "identifiers": identifiers
        # })
        feature_matrix = x["feature_matrix"]
        if len(feature_matrix) == 2:
            d = feature_matrix[0][0]["frequency"]
            c = feature_matrix[0][1]["frequency"]
            b = feature_matrix[1][0]["frequency"]
            a = feature_matrix[1][1]["frequency"]
            x.update({
                "risk_ratio":  np.float64(a) * (c + d) / (c * (a + b)),
                "odds_ratio": np.float64(a) * d / (b * c)
            })
        return x
    return map(extract_data_from_result, l)


def to_feature_dict(association_to_all_features):
    d = {}
    for x in association_to_all_features:
        feature_name = x["feature_b"]["feature_name"]
        feature_matrix = x["feature_matrix"]
        f00 = feature_matrix[0][0]["frequency"]
        f10 = feature_matrix[0][1]["frequency"]
        f01 = feature_matrix[1][0]["frequency"]
        f11 = feature_matrix[1][1]["frequency"]
        c1x = f10 + f11
        cx1 = f01 + f11
        c0x = f00 + f01
        cx0 = f00 + f10
        c = c1x + c0x
        print("ICEES", feature_name, round(np.float64(f11) / c,2), round(c1x / c,2), round(cx1 / c,2), round(np.log ((np.float64(f11) / c) / ((c1x / c) * (cx1 / c))), 2))
        d[feature_name] = (feature_matrix, to_float(np.log ((np.float64(f11) / c) / ((c1x / c) * (cx1 / c)))))
    return d

def to_feature_dict_cp(ftr, association_to_all_features):
    if ftr == "Sex2":
        i0 = 0
        i1 = 1
    else:
        i0 = 1
        i1 = 0
    d = {}
    c0x = association_to_all_features["cohort count"][i0]["value"]
    c1x = association_to_all_features["cohort count"][i1]["value"]
    def filter_ftr(a):
        for b in a:
            if b in x:
                feature_name = x[b]

        f01 = x["frequency"][i0]
        f11 = x["frequency"][i1]
        f00 = c0x - f01
        f10 = c1x - f11
        cx0 = f00 + f10
        cx1 = f01 + f11
        c = c0x + c1x
        feature_matrix = [
            [{
                "frequency" : f00,
                "row_percentage" : np.float64(f00) / cx0
            }, {
                "frequency": f10,
                "row_percentage": np.float64(f10) / cx0
            }],[{
                "frequency": f01,
                "row_percentage": np.float64(f01) / cx1
            }, {
                "frequency": f11,
                "row_percentage": np.float64(f11) / cx1
            }]
        ]
        _, p = chisquare([f00, f01], [f10, f11])
        if p <= 0.1:
            print("CP", feature_name, round(np.float64(f11) / c, 2), round(c1x / c, 2), round(cx1 / c, 2),
                  round(np.log((np.float64(f11) / c) / ((c1x / c) * (cx1 / c))), 2))
            d[feature_name] = (feature_matrix, to_float(np.log((np.float64(f11) / c) / ((c1x / c) * ( cx1 / c)))))

    for x in association_to_all_features["Dx"]:
        filter_ftr(["Diagnosis", "Feature-name"])
    for x in association_to_all_features["Meds"]:
        filter_ftr(["Medications", "Feature-name"])

    return d


def to_int(a):
    if np.isnan(a):
        return None
    else:
        return int(a)


def to_float(a):
    if np.isnan(a):
        return None
    else:
        return float(a)


def to_feature_dict_cohd(ftr):
    with open(f"WF5_COHD_{ftr}.pkl", "rb") as f:
        [df] = pickle.load(f)

    if ftr == "Sex2":
        df = df[["name", "observed_count_female", "observed_count_male", "significant", "ln_ratio_female_vs_male"]]
    else:
        df = df[["name", "observed_count", "significant", "ln_ratio"]]

    dfl = df.values.tolist()

    d = {}

    def filter_ftr(a):
        if ftr == "Sex2":
            if a[3]:
                feature_matrix = [
                    [{
                        "frequency": None,
                        "row_percentage": None
                    }, {
                        "frequency": None,
                        "row_percentage": None
                    }], [{
                        "frequency": to_int(a[1]),
                        "row_percentage": to_float(np.float64(a[1]) / (a[1] + a[2]))
                    }, {
                        "frequency": to_int(a[2]),
                        "row_percentage": to_float(np.float64(a[2]) / (a[1] + a[2]))
                    }]
                ]
                d[a[0]] = (feature_matrix, a[3])
        else:
            if a[2]:
                feature_matrix = [
                    [{
                        "frequency" : None,
                        "row_percentage" : None
                    }, {
                        "frequency": None,
                        "row_percentage": None
                    }],[{
                        "frequency": None,
                        "row_percentage": None
                    }, {
                        "frequency": to_int(a[1]),
                        "row_percentage": None
                    }]
                ]
                d[a[0]] = (feature_matrix, a[3])

    for x in dfl:
        filter_ftr(x)

    return d

def to_perc(a):
    return str(round(a * 100, 2)) + "\\%"

def run_e(cohort, ftr):
    association_to_all_features = run(cohort, association_to_all_features_input[ftr])
    with open(f"WF5_ICEES_{cohort}_{ftr}.json", "w") as f:
        json.dump(association_to_all_features, f)

    
def run_f(cohort, ftr, fmt):
    with open(f"WF5_ICEES_{cohort}_{ftr}.json") as f:
        association_to_all_features = json.load(f)
    association_to_dx = filter(dx, association_to_all_features["return value"])
    association_to_chemical_substance = filter(chemical_substance, association_to_all_features["return value"])
    if fmt == "latex":
        with open(f"WF5_CP_{cohort}_{ftr}.json") as f:
            cp = json.load(f)

        feature_dict = to_feature_dict(association_to_all_features["return value"])
        feature_dict_cp = to_feature_dict_cp(ftr, cp)
        feature_dict_cohd = to_feature_dict_cohd(ftr)
        output = "\\documentclass{standalone}\n\\usepackage{multirow}\n\\begin{document}\n\\begin{tabular}{|c | c c | c c|c |c c|c c|c |c c|c c|c|}\n"
        output += "\\hline\n"
        output += " & \\multicolumn{5}{c|}{ICEES}  & \\multicolumn{5}{c|}{ClinicalProfile}  & \\multicolumn{5}{c|}{COHD (GP)} \\\\\n\\hline\n"
        if ftr == "Sex2":
            output += "& \multicolumn{5}{c|}{Sex} " * 3 + "\\\\\n\\hline\n" + "& \\multicolumn{2}{c|}{Female} & \\multicolumn{2}{c|}{Male} & log ratio" * 3 + " \\\\\n"
        else:
            output += ("& \multicolumn{5}{c|}{" + ftr + "}") * 3 + "\\\\\n\\hline\n" + "& \\multicolumn{2}{c|}{0} & \\multicolumn{2}{c|}{1} & log ratio" * 3 + " \\\\\n"
        icees_features = []
        for f, _, _, b in features["patient"]:
            if f.endswith("Dx") or b == "Drug":
                icees_features.append(f)

        for f in icees_features:
            output += "\\hline\n" + f
            for fd in [feature_dict, feature_dict_cp, feature_dict_cohd]:
                output += " & "
                if f in fd:
                    (feature_matrix, log_ratio) = fd[f]
                    if feature_matrix[1][0]["frequency"]:
                        a = str(feature_matrix[1][0]["frequency"])
                    else:
                        a = ""
                    if feature_matrix[1][0]["row_percentage"]:
                        b = to_perc(feature_matrix[1][0]["row_percentage"])
                    else:
                        b = ""
                    if feature_matrix[1][1]["frequency"]:
                        c = str(feature_matrix[1][1]["frequency"])
                    else:
                        c = ""
                    if feature_matrix[1][1]["row_percentage"]:
                        d = to_perc(feature_matrix[1][1]["row_percentage"])
                    else:
                        d = ""
                    if log_ratio:
                        e = str(round(log_ratio, 2))
                    else:
                        e = ""

                    output += a + " & " + b + " & " + c + " & " + d + " & " + e
                else:
                    output += "\\multicolumn{5}{c|}{ns}"
            output += "\\\\\n"
        output += "\\hline\n"
        output += "\\end{tabular}\n\\end{document}\n"
    else:
        output = format_tabular("dx", list(extract_data_from_results(association_to_dx)), fmt)

        output += format_tabular("chemical substance", list(extract_data_from_results(association_to_chemical_substance)), fmt)

    with open(f"WF5_{cohort}_{ftr}.{fmt}", "w") as f:
        f.write(output)


if __name__ == "main":
    e = sys.argv[1]
    f = sys.argv[2]
    fmt = sys.argv[3]
    print(run_f(e, f, fmt))
