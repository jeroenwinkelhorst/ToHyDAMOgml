"""



Make sure the working directory is the folder where this file is located
"""
import sys
import os
import logging
from codecs import ignore_errors
from datetime import datetime


# Make folder for logging
folder = os.path.join('log', datetime.today().strftime("%Y%m%d_%H%M"))
if not os.path.exists(folder):
    os.makedirs(folder)

logging.basicConfig(filename=os.path.join(folder, 'logging.log'), level=logging.INFO)
logging.info('Started')


# Relative path to root folder of script
sys.path.append(r"../../")
from tohydamogml.hydamo_table import HydamoObject

# path to json files
path_json = os.path.join(r"json")

# Optional: filepath to a python file with attributes functions. In the json files is referred to these functions.
attr_function = os.path.join(os.getcwd(), path_json, "attribute_functions.py")

# path to export gml files
export_path = os.path.join("output", "GML januari")
if not os.path.exists(export_path):
    os.makedirs(export_path)

# Optional: select a part of the sourcedata by a shape
# mask = r"c:\local\TKI_WBD\aanvullende_data\Aa_of_Weerijs_v2.shp"
mask = r'c:\Users\908367\Box\BH8519 WBD DHYDRO\BH8519 WBD DHYDRO WIP\04_GIS\modelgebied_edit.shp'

# list with json objects to loop through
json_objects = [
    os.path.join(path_json, "hydroobject.json"),
    os.path.join(path_json, "stuw.json"),
    os.path.join(path_json, "duikersifonhevel.json"),
    os.path.join(path_json, "afsluitmiddel.json"),
    os.path.join(path_json, "brug.json"),
    os.path.join(path_json, "brug_dwp.json"),
    os.path.join(path_json, "gemaal.json"),
    os.path.join(path_json, "pomp.json"),
    os.path.join(path_json, "randvoorwaarden.json"),
    os.path.join(path_json, "profiel_legger.json")
]

for json_object in json_objects:
    logging.info(f'Object path: {str(json_object)}')

    if mask:
        obj = HydamoObject(json_object, mask=mask, file_attribute_functions=attr_function, outputfolder=folder)
    else:
        obj = HydamoObject(json_object, file_attribute_functions=attr_function, outputfolder=folder)
    obj.validate_gml(write_error_log=True)
    obj.write_gml(export_path, ignore_errors=True, skip_validation=True)

# bodemval als stuw met suffix
json_object = os.path.join(path_json, "bodemval_stuw.json")
logging.info(f'Object path: {str(json_object)}')
obj = HydamoObject(json_object, mask=mask, file_attribute_functions=attr_function, outputfolder=folder)
obj.validate_gml(write_error_log=True)
obj.write_gml(export_path, ignore_errors=True, skip_validation=True, suffix='_bodemval')

# brug_dwp met suffix
json_object = os.path.join(path_json, "brug_dwp.json")
logging.info(f'Object path: {str(json_object)}')
obj = HydamoObject(json_object, mask=mask, file_attribute_functions=attr_function, outputfolder=folder)
obj.validate_gml(write_error_log=True)
obj.write_gml(export_path, ignore_errors=True, skip_validation=True, suffix='_brug')

import geopandas as gpd
gdf_prof = gpd.read_file(os.path.join(export_path, 'dwarsprofiel.gml'))
gdf_dwp = gpd.read_file(os.path.join(export_path, 'dwarsprofiel_brug.gml'))
gdf_both = gdf_prof.append(gdf_dwp)
gdf_both = gdf_both[~gdf_both.profielcode.isin(['KBR02615'])]
gdf_both.to_file(os.path.join(export_path, 'both_profiles.gml'), driver='GML')

logging.info('Finished')