import icees.iceesclient as ic
import json
import sys
import numpy as np

f = sys.argv[1]

cohort = ic.define_cohort({
    "Prednisone": {
        "operator": "=",
        "value":1
    }
})

cohort_id = cohort["return value"]["cohort_id"]

association_to_all_features_input = {
    "Sex": { 
        "feature":{
            "Sex": {
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
                "value":1
            }
        },
        "maximum_p_value" : 0.1
    },
    "DiabetesDx": {
        "feature":{
            "DiabetesDx": {
                "operator": "=",
                "value":1
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
        feature_matrix = x["feature_matrix"]
        a = feature_matrix[0][0]["frequency"]
        b = feature_matrix[0][1]["frequency"]
        c = feature_matrix[1][0]["frequency"]
        d = feature_matrix[1][1]["frequency"]
        feature_name = x["feature_b"]["feature_name"]
        identifiers = ic.identifiers(feature_name.split("_")[0])
        return {
            "feature_name": feature_name,
            "identifiers" : identifiers,
            "p_value": x["p_value"],
            "feature_matrix": [[a,b],[c,d]],
            "risk_ratio":  np.float64(a) * (c + d) / (b * (a + b)),
            "odds_ration": np.float64(a) * d / (b * c)
        }
    return map(extract_data_from_result, l)


def run_f(f):
    association_to_all_features = run(association_to_all_features_input[f])
    # print(k)
    association_to_dx = filter(dx, association_to_all_features["return value"])
    print(json.dumps(list(extract_data_from_results(association_to_dx))))
    
    association_to_chemical_substance = filter(chemical_substance, association_to_all_features["return value"])
    print(json.dumps(list(extract_data_from_results(association_to_chemical_substance))))

run_f(f)
