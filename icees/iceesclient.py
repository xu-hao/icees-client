import requests
import json
import argparse
import logging
requests.packages.urllib3.disable_warnings()

tabular_headers = {"Content-Type" : "application/json", "accept": "text/tabular"}
json_headers = {"Content-Type" : "application/json", "accept": "application/json"}

logger = logging.getLogger (__name__)

# # These two lines enable debugging at httplib level (requests->urllib3->http.client)
# # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# # The only thing missing will be the response.body which is not logged.
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

class FeatureFilter:
    
    def __init__(self, feature, value, operator):
        self.feature = feature
        self.value = value
        self.operator = operator
    

def identifiers(feature, version="1.0.0", table="patient"):
    return ICEES().get_identifiers(feature, version=version, table=table)
    
class Bionames:

    def __init__(self):
        """ Initialize the operator. """
        self.url = "https://bionames.renci.org/lookup/{input}/{type}/"
    
    def get_ids (self, name, type_name):
        url = self.url.format (**{
            "input" : name,
            "type"  : type_name
        })
        logger.debug (f"url: {url}")
        result = None
        response = requests.get(
            url = url,
            headers = {
                'accept': 'application/json'
            })
        if response.status_code == 200 or response.status_code == 202:
            result = response.json ()
        else:
            raise ValueError (response.text)
        logger.debug (f"bionames result {result}")
        return result
    
class ICEES:
    
    def __init__(self):
        """ Initalize ICEES API. """
        self.bionames = Bionames ()
        self.drug_suffix = [ "one", "ide", "ol", "ine", "min", "map", "exposure" ]
        self.drug_names = [ "Prednisone", "Fluticasone", "Mometasone", "Budesonide", "Beclomethasone",
                            "Ciclesonide", "Flunisolide", "Albuterol", "Metaproterenol", "Diphenhydramine",
                            "Fexofenadine", "Cetirizine", "Ipratropium", "Salmeterol", "Arformoterol",
                            "Formoterol", "Indacaterol", "Theophylline", "Omalizumab", "Mepolizumab", "Metformin" ]
        self.diagnoses = [ "CroupDx", "ReactiveAirwayDx", "CoughDx", "PneumoniaDx", "ObesityICD", "ObesityBMI" ]
        self.def_cohort = DefineCohort ()
        self.all_features = AssociationToAllFeatures ()
        
    def get_cohort(self, feature, value, operator):
        """ Get a cohort by a single feature spec. """
        return self.run_define_cohort(feature, value, operator)
    
    def feature_to_all_features (self, feature, value, operator, max_p_val, cohort_id):
        """ Get association from one feature to all other features within a cohort. """
        return self.all_features.run_association_to_all_features (
            feature = feature,
            value = value,
            operator = operator,
            maximum_p_value = max_p_val,
            cohort_id = cohort_id)

    def get_identifiers (self, feature, version="1.0.0", table="patient"):
        query = f"https://icees.renci.org/{version}/{table}/{feature}/identifiers"
        response = requests.get (query, verify=False).json ()
        ret = response['return value']
        if isinstance(ret, dict):
            return ret['identifiers']
        else:
            return []

    def build_associations (self, feature, type_name, target_id, p_value, edges, nodes):
        identifiers = self.get_identifiers (feature)
        print (identifiers)
        if len(identifiers) > 0:
            logger.debug (f"Got ids for {feature}: {identifiers}")
            for an_id in identifiers:
                nodes.append ({
                    "id" : an_id,
                    "type" : type_name
                })
                edges.append ({
                    "type" : "associated_with",
                    "source_id" : an_id,
                    "target_id" : target_id,
                    "attributes" : {
                        "p_val" : p_value
                    }
                })

    def parse_1_x_N (self, response, target_types=[ 'chemical_substance' ]):
        """
        This is a stop-gap measure in which we overlay semantic information over ICEES data.
        Biolink-model concepts are mapped, provisionally, to data elements retuned from the association service.
        """
        asthma_id = "MONDO:0004979"
        nodes = [ {
            "id" : asthma_id,
            "type" : "disease"
        }]
        edges = []
        print (f"{json.dumps(response, indent=2)}")
        if 'return value' in response:
            for value in response['return value']:
                logger.debug (f" value {value}")
                if 'feature_b' in value:
                    feature_name = value['feature_b'].get ('feature_name', None)
                    if feature_name is None:
                        continue
                    logger.debug (f"feature_name: {feature_name}")

                    for type_name in target_types:
                        if type_name == 'chemical_substance':
                            # Handle drugs 
                            if any([ v for v in self.drug_suffix if feature_name.endswith (v) ]):
                                self.build_associations (
                                    feature=feature_name, type_name=type_name,
                                    target_id=asthma_id, p_value=value['p_value'],
                                    edges=edges, nodes=nodes)
                        elif type_name == 'disease':
                            # Handle disease diagnoses
                            if feature_name in self.diagnoses:
                                self.build_associations (
                                    feature=feature_name, type_name=type_name,
                                    target_id=asthma_id, p_value=value['p_value'],
                                    edges = edges, nodes=nodes)
                        else:
                            logger.debug (f"ignoring unhanlded type name: {type_name}")
                                    
                            '''
                                chem_type = 'chemical_substance'
                                ids = self.bionames.get_ids (feature_name,
                                                             type_name=chem_type)
                                """ This is a temporary measure until the ICEES API returns identifiers, and hopefully a biolink-model type 
                                with the responses to feature association requests. For now, we look up names that look like chemicals and 
                                and call them chemical substances if we get ids back from bionames. """
                                if len(ids) > 0:
                                    logger.debug (f"Got ids for {feature_name}: {ids}")
                                    for v in ids:
                                        v['name'] = v['label']
                                        del v['label']
                                        v['type'] = chem_type
                                        edges.append ({
                                            "type" : "associated_with",
                                            "source_id" : v['id'],
                                            "target_id" : asthma_id,
                                            "attributes" : {
                                                "p_val" : value['p_value']
                                            }
                                        })
                                        nodes = nodes + ids
                        elif type_name == 'disease':
                            # Handle disease diagnoses
                            if feature_name and any([
                                    v for v in self.drug_suffix if feature_name.endswith (v) ]):
                                chem_type = 'chemical_substance'
                            '''

        return {
            "nodes" : nodes,
            "edges" : edges
        }
    
class DefineCohort ():
    def __init__(self):
        pass
    
    def make_cohort_definition(self, feature, value, operator):
        feature_variables = '{{"{0}": {{ "value": {1}, "operator": "{2}"}}}}'.format(feature, value, operator)
        return feature_variables
    
    def define_cohort_query(self, feature_variables, year=2010, table='patient', version='1.0.0'): # year, table, and version are hardcoded for now
        define_cohort_response = requests.post('https://icees.renci.org/{0}/{1}/{2}/cohort'.format(version, table, year), data=feature_variables, headers = json_headers, verify = False)               
        return define_cohort_response

    def run_define_cohort (self, feature, value, operator):
        feature_variables = self.make_cohort_definition(feature, value, operator)
        define_cohort_query = self.define_cohort_query(feature_variables)
        define_cohort_query_json = define_cohort_query.json()
        return define_cohort_query_json

def define_cohort (data, year=2010, table="patient", version="2.0.0"):
    define_cohort_query = DefineCohort().define_cohort_query(json.dumps(data), year=year, table=table, version=version)
    define_cohort_query_json = define_cohort_query.json()
    return define_cohort_query_json

class GetCohortDefinition():
    def __init__(self):
        pass
    
    def get_cohort_definition_query(self, cohort_id, year=2010, table='patient', version='1.0.0'):
        cohort_definition_response = requests.get('https://icees.renci.org/{0}/{1}/{2}/cohort/{3}'.format(version, table, year, cohort_id), headers = json_headers, verify = False)               
        return cohort_definition_response

    def run_get_cohort_definition(self, cohort_id):
        cohort_definition_query = self.get_cohort_definition_query(cohort_id)
        cohort_definition_query_json = cohort_definition_query.json()
        return cohort_definition_query_json
    
class GetFeatures():
    def __init__(self):
        pass

    def get_features_query(self, cohort_id, year=2010, table='patient', version='1.0.0'):
        features_response = requests.get('https://icees.renci.org/{0}/{1}/{2}/cohort/{3}/features'.format(version, table, year, cohort_id), headers=json_headers, verify=False)
        return features_response

    def run_get_features(self, cohort_id):
        features_query = self.get_features_query(cohort_id)
        features_query_json = features_query.json()
        return features_query_json

class FeatureAssociation():
    def __init__(self):
        pass

    def make_feature_association(self, feature_a, feature_a_operator, feature_a_value, feature_b, feature_b_operator, feature_b_value):
        feature_assoc_variables = '{{"feature_a":{{"{0}":{{"operator":"{1}","value":{2}}}}},"feature_b":{{"{3}":{{"operator":"{4}","value":{5}}}}}}}'.format(feature_a, feature_a_operator, feature_a_value, feature_b, feature_b_operator, feature_b_value)
        return feature_assoc_variables

    def feature_association_query(self, feature_assoc_variables, cohort_id, year=2010, table='patient', version='1.0.0'):
        feature_association_response = requests.post('https://icees.renci.org/{0}/{1}/{2}/cohort/{3}/feature_association'.format(version, table, year, cohort_id), data=feature_assoc_variables, headers=json_headers, verify=False)
        return feature_association_response

    def run_feature_association(self, feature_a, feature_a_operator, feature_a_value, feature_b, feature_b_operator, feature_b_value, cohort_id):
        feature_assoc_variables = self.make_feature_association(feature_a, feature_a_operator, feature_a_value, feature_b, feature_b_operator, feature_b_value)
        feature_assoc_query = self.feature_association_query(feature_assoc_variables, cohort_id)
        feature_assoc_query_json = feature_assoc_query.json()
        return feature_assoc_query_json

def association_to_all_features(data, cohort_id, year=2010, table="patient", version="2.0.0"):
    association_to_all_features_query = AssociationToAllFeatures().association_to_all_features_query(json.dumps(data), cohort_id, year=year, table=table, version=version)
    association_to_all_features_query_json = association_to_all_features_query.json()
    return association_to_all_features_query_json
    
    
class AssociationToAllFeatures():
    def __init__(self):
        pass
    
    def make_association_to_all_features(self, feature, value, operator, maximum_p_value):
        feature_variable_and_p_value = '{{"feature":{{"{0}":{{"operator":"{2}","value":{1}}}}},"maximum_p_value":{3}}}'.format(feature, value, operator, maximum_p_value)
        return feature_variable_and_p_value

    def association_to_all_features_query(self, feature_variable_and_p_value, cohort_id, year=2010, table='patient', version='1.0.0'):
        assoc_to_all_features_response = requests.post('https://icees.renci.org/{0}/{1}/{2}/cohort/{3}/associations_to_all_features'.format(version, table, year, cohort_id), data=feature_variable_and_p_value, headers= json_headers, verify=False)
        return assoc_to_all_features_response

    def run_association_to_all_features(self, feature, value, operator, maximum_p_value, cohort_id):
        feature_variable_and_p_value = self.make_association_to_all_features(feature, value, operator, maximum_p_value)
        print (json.dumps (feature_variable_and_p_value, indent=2))
        print (json.dumps (json.loads(feature_variable_and_p_value), indent=2))
        assoc_to_all_features_query = self.association_to_all_features_query(feature_variable_and_p_value, cohort_id)
        assoc_to_all_features_query_json = assoc_to_all_features_query.json()
        return assoc_to_all_features_query_json

class GetDictionary():
    def __init__(self):
        pass

    def get_dictionary_query(self, year=2010, table='patient', version='1.0.0'):
        dictionary_response = requests.get('https://icees.renci.org/{0}/{1}/{2}/cohort/dictionary'.format(version, table, year), headers = json_headers, verify = False) 
        return dictionary_response

    def run_get_dictionary(self):
        dictionary_query = self.get_dictionary_query()
        dictionary_query_json = dictionary_query.json()
        return dictionary_query_json


# You can use the work below to treat this module as a CLI utility. Currently, it is configured to accept inputs for and
# return values from the simplest input, "DefineCohort"... feel free to copy/fork and customize for your own purposes!


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-ftr", "--feature", help="feature name")
    parser.add_argument("-v", "--value", help="feature value")
    parser.add_argument("-op", "--operator", help="feature operator")
    args = parser.parse_args()

    import sys
    if len(sys.argv) > 3:
        icees_define_cohort = DefineCohort()
        output = icees_define_cohort.run_define_cohort(args.feature, args.value, args.operator)
        #if 'cohort_id' in str(output):
        print()
        print ('Cohort definition accepted')
        print(output['return value'])
        print()
    else:
        print("Expected script call is of the form: $python3 icees_caller.py -ftr <feature> -val <value> -op \<operator>")
