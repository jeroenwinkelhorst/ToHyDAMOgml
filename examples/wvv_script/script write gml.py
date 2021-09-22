"""



Make sure the working directory is the folder where this file is located
"""
import sys
import os

# Relative path to root folder of script
sys.path.append(r"../../")
from tohydamogml.hydamo_table import HydamoObject

# path to json files
path_json = os.path.join("json")

# Optional: filepath to a python file with attributes functions. In the json files is referred to these functions.
attr_function = os.path.join(os.getcwd(), path_json, "attribute_functions.py")

# path to export gml files
export_path = os.path.join("output")

# Optional: select a part of the sourcedata by a shape
# mask = r"00_Brondata/shp/clip_pilot_loc1.shp"

# list with json objects to loop through
json_objects = [
    os.path.join(path_json, "hydroobject.json"),
    # os.path.join(path_json, "stuw.json"),
    # os.path.join(path_json, "duikersifonhevel.json"),
    # os.path.join(path_json, "afsluitmiddel.json"),
    # os.path.join(path_json, "brug.json"),
    # os.path.join(path_json, "brug_dwp.json"),
    # os.path.join(path_json, "dwarsprofiel_bovenstrooms_legger.json"),
    # os.path.join(path_json, "gemaal.json"),
    # os.path.join(path_json, "pomp.json"),

    # os.path.join(path_json, "sturing.json"),
    # os.path.join(path_json, "bodemval.json"),
    # os.path.join(path_json, "meetlocatie.json"),
]

for json_object in json_objects:
    obj = HydamoObject(json_object, file_attribute_functions=attr_function)
    # if mask:
    # obj = HydamoObject(json_object, mask=mask, file_attribute_functions=attr_function)

    obj.validate_gml(write_error_log=True)
    obj.write_gml(export_path, ignore_errors=True, skip_validation=True)
