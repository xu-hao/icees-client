import icees.iceesclient as ic
import sys
import numpy as np
from format import format_tabular

e = sys.argv[1]
f = sys.argv[2]

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
    }
}

cohort = ic.define_cohort(define_cohort_input[e])

cohort_id = cohort["return value"]["cohort_id"]

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
    }
}

def run(x):
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
        feature_name = x["feature_b"]["feature_name"]
        identifiers = ic.identifiers(feature_name.split("_")[0])
        x["feature_b"].update({
            "identifiers": identifiers
        })
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


def run_f(f):
    association_to_all_features = run(association_to_all_features_input[f])

    association_to_dx = filter(dx, association_to_all_features["return value"])
    print(format_tabular("dx", list(extract_data_from_results(association_to_dx))))

    association_to_chemical_substance = filter(chemical_substance, association_to_all_features["return value"])
    print(format_tabular("chemical substance", list(extract_data_from_results(association_to_chemical_substance))))


run_f(f)
