"""
Dit script is onderdeel van de tool voor conversie van gegevens uit DAMO naar HyDAMO. Deze code is specifiek opgesteld
voor waterschap Vallei en Veluwe. Toelichting voor het gebruik van dit script staat in de readme (zie hoofdmap).

Dit script is opgesteld door Royal HaskoningDHV in opdracht van waterschap Vallei het Veluwe en is vrij te gebruiken
onder de voorwaarden van de BSD licentie.

Vragen en opmerkingen met betrekking tot dit script kun je mailen aan jeroen.winkelhorst[a]rhdhv.com
"""

import os
import sys
import json
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely import ops
from tohydamogml.gml import Gml
from tohydamogml.read_database import read_filegdb, read_featureserver



class HydamoObject:
    """
    Creates geopandas dataframe for a HyDAMO object with all the required attributes
    """

    def __init__(self, path_json: str, print_gml=True, mask: str = None, file_attribute_functions=None):
        """

        :param path_json: str, path to JSON input file
        :param print_gml: bool, print GML in output window
        :param mask: string, path to shapefile with 1 polygon
        """

        # load attribute functions
        if file_attribute_functions:
            fname_ext = os.path.basename(file_attribute_functions)
            dirname = os.path.dirname(file_attribute_functions)
            sys.path.append(dirname)
            self.ws = __import__(os.path.splitext(fname_ext)[0])

        with open(path_json) as f:
            obj = json.load(f)

        self.obj = obj
        self.objectname = obj['object']
        self.gdf = None
        self.attr_dtype = {}
        self.attr_required = {}
        self.attr_damo = {}
        self.attr_dummy = {}
        self._gml = None
        self.mask = None
        self._read_attributes_to_dicts(obj)

        if mask:
            mask_tbl = gpd.read_file(mask)
            if len(mask_tbl) == 1:
                self.mask = mask_tbl["geometry"][0]
            else:
                print("mask has more than one record and is therefore not valid!")

        self._create_object(obj, self.mask)

        if print_gml:
            self.print_gml()

    def _create_object(self, obj, mask):
        """
        Create gdf for hydroobject
        """
        # Load Data
        gdf_src = self._create_gdf_from_gdb()

        gdf_src = self._create_gdf_from_gdb(obj["source"]["layer"], obj["source"]["path"], obj["index"]['name'],
                                            filter_dict=obj["source"]["filter"], filter_type=obj["source"]["filter_type"],
                                            index_col_src=obj["index"]["src_col"], mask=mask, query=obj["source"]["query"])

        # join related table
        if obj['related_data']["path"]:
            gdf_src = self._add_related(gdf_src, rel_path=obj['related_data']['path'],
                                        rel_layer=obj['related_data']['layer'],
                                        mapping_col_src=obj['related_data']['mapping_col_src'],
                                        mapping_col_rel=obj['related_data']['mapping_col_rel'],
                                        replace_index_col=obj['related_data']['replace_index_col'],
                                        index_name=obj["index"]['name'])

        self.gdf = self._create_empty_gdf(gdf_src)

        for attr in self.obj['attributes']:
            self._add_attribute(attr, gdf_src)

        # Geometry operations
        if self.obj["geometry"]["func"]:
            func = eval("self.ws." + self.obj["geometry"]["func"])
            self.gdf["geometry"] = pd.DataFrame(data={"geometry": func(damo_gdf=gdf_src, obj=self.obj)})

        if self.obj["geometry"]["drop"] is True:
            self.gdf = self.gdf.drop(['geometry'], axis=1)
            self.gdf.crs = None
        else:
            self._linemerge()
            self._multipoint_to_point()

    def _add_attribute(self, attr, gdf):
        """
        Add attribute to gdf
        """
        if attr['src_col'] or attr['func']:
            if attr['func']:
                func = eval("self.ws." + attr['func'])
            else:
                func = None
            self._add_src_attr(attr['name'], gdf, func)
        elif attr['default'] != "":
            self._add_fixed_value_attr(attr['name'], attr['default'])
        else:
            print("Attribute ", attr, " not added")

    def _add_related(self, gdf_src, rel_path, rel_layer, mapping_col_src, mapping_col_rel, replace_index_col=None,
                     index_name=None, prefix="rel_"):
        # env.workspace = rel_path
        gdf_rel = read_filegdb(rel_path, rel_layer)
        gdf_rel = gdf_rel.add_prefix(prefix)

        gdf_src = gdf_src.merge(gdf_rel, how="left", left_on=mapping_col_src, right_on=mapping_col_rel)
        if replace_index_col:
            gdf_src.set_index(replace_index_col, append=False, inplace=True)
            gdf_src.index.names = [index_name]
        return gdf_src[gdf_src.index.notnull()]

    @property
    def gml(self):
        """
        Get GML
        """
        if self._gml is None:
            self._gml = Gml(self.gdf.reset_index(), self.objectname)
        return self._gml

    def print_gml(self):
        """
        Print GML tags (string format)
        """
        return self.gml.print()

    def write_gml(self, export_folder, ignore_errors=False, skip_validation=False, suffix: str = ""):
        """
        Write GML file to .gml file
        """
        return self.gml.write(export_folder, ignore_errors, skip_validation, suffix=suffix)

    def validate_gml(self, write_error_log=False):
        """
        Validate GML with XSD (XSD loc defined in config file)
        """
        return self.gml.validate(write_error_log)

    def _create_gdf_from_gdb(self, layer: str, filegdb: str, index_name: str, filter_dict: dict = None,
                             filter_type: str = None, index_col_src: str = None, mask=None, query=None):
        """
        Create geodataframe from database. Optionally filter rows

        :param layer: name of the layer to load from the database
        :param filegdb: path to database
        :param index_name: new name of the index column
        :param filter_dict: dict, {"column_name": [values] }
        :param filter_type: str, include or exclude
        :param index_col_src: column name of the index
        :param mask: shapely polygon. Only the features that intersect the polygon will be loaded
        :return: geodataframe
        """

        gdf = read_filegdb(filegdb, layer)

        if mask and (gdf.geometry[0] is not None):
            gdf = gdf[gdf.intersects(mask)]
        if filter_dict:
            gdf = self._filter_gdf(gdf, filter_dict, filter_type)
        if query:
            gdf = gdf.query(query, engine="python")

        gdf.reset_index(inplace=True)
        gdf.set_index(index_col_src, inplace=True, drop=False)
        gdf.index.names = [index_name]

        # remove objects without a unique code
        gdf = gdf[gdf.index.notnull()]

        return gdf

    def _create_gdf_from_featureserver(self, url: str, layer_name: str, layer_index: int, filter_dict: dict = None,
                                filter_type: str = None, index_col_src: str = None, mask=None, query=None):
        """
        Create geodataframe from arcgis featureserver. Optionally filter rows

        :param url: path to the url of the featureserver. Typically looks like:
                    "https://maps.XX.com/arcgis/rest/services/XX/XX/FeatureServer"
        :param layer_name: name of the layer
        :param layer_index: index of the layer within the Feature Server
        :param filter_dict: dict, {"column_name": [values] }
        :param filter_type: str, include or exclude
        :param index_col_src: column name of the index
        :param mask: shapely polygon. Only the features that intersect the polygon will be loaded
        :return: geodataframe
        """

        gdf = read_featureserver(url, layer_index)

        if mask and (gdf.geometry[0] is not None):
            gdf = gdf[gdf.intersects(mask)]
        if filter_dict:
            gdf = self._filter_gdf(gdf, filter_dict, filter_type)
        if query:
            gdf = gdf.query(query, engine="python")

        gdf.reset_index(inplace=True)
        gdf.set_index(index_col_src, inplace=True, drop=False)
        gdf.index.names = [index_name]

        # remove objects without a unique code
        gdf = gdf[gdf.index.notnull()]

        return gdf

    def _filter_gdf(self, gdf, filter_dict, filter_type):
        """Filter geodataframe. Return filtered gdf.
        filter: dict, {"column_name": [values] }
        filter_type: str, include or exclude
        """
        # Filter data
        if filter_dict is not None and filter_type == "include":
            mask = pd.DataFrame()
            for key, value in filter_dict.items():
                mask[key] = gdf[key].isin(value)
            mask = mask.any(axis=1)
            gdf = gdf[mask]
        if filter_dict is not None and filter_type == "exclude":
            mask = pd.DataFrame()
            for key, value in filter_dict.items():
                mask[key] = gdf[key].isin(value)
            mask = ~mask.max(axis=1)
            gdf = gdf[mask]

        return gdf

    def _read_attributes_to_dicts(self, obj):
        """
        Read  HyDAMO attributes from JSON
        """
        for attr in obj["attributes"]:
            index = attr["name"]
            self.attr_dtype[index] = self._interpret_dtype(attr["type"])
            self.attr_required[index] = attr["required"]
            if attr['src_col']:
                self.attr_damo[index] = attr['src_col']
            if attr['default']:
                self.attr_dummy[index] = attr['default']

    def _interpret_dtype(self, input_dtype: str):
        """
        Converts datatype in text format to numpy format
        """
        if input_dtype.lower() in ["string"]:
            return np.object
        if input_dtype.lower() in ["shape"]:
            return "geometry"
        if input_dtype.lower() in ["integer"]:
            return np.int64
        if input_dtype.lower() in ["double", "float"]:
            return np.float64
        if input_dtype.lower() in ["date"]:
            return np.datetime64

    def _create_empty_gdf(self, gdf):
        """
        Remove all the columns of the dataframe except the geometry
        """
        gdf = gdf[['geometry']].copy()

        # Raise error if geodataframe has no rows
        if len(gdf) == 0:
            raise ValueError(f'geodataframe {self.objectname} is empty. Check your input.')

        return gdf

    def _add_src_attr(self, attr, src_gdf, func=None):
        """
        General method to add Attributes to gdf.
        If an attribute is required and unknown, a dummy value added
        """
        if func is not None:
            tmp_attr = pd.DataFrame(data={attr: func(damo_gdf=src_gdf, obj=self.obj)})
        else:
            tmp_attr = pd.DataFrame(src_gdf[self.attr_damo[attr]])
            tmp_attr.rename(columns={self.attr_damo[attr]: attr}, inplace=True)

        tmp_attr = self._fill_na_if_required(attr, tmp_attr)
        tmp_attr = self._set_datatype(attr, tmp_attr)

        self.gdf[attr] = tmp_attr

    def _add_fixed_value_attr(self, attr, value):
        """
        General method to add a fixed value attribute
        TODO: validate datatype
        """
        self.gdf[attr] = value

    def _linemerge(self):
        """
        merge multiline to line
        """
        self.gdf['geometry'] = self.gdf['geometry'].apply(
            lambda x: ops.linemerge(x) if x.type == 'MultiLineString' else x)

    def _multipoint_to_point(self):
        """
        Convert multipoint geometry to point geometry
        """
        self.gdf['geometry'] = self.gdf['geometry'].apply(lambda x: x[0] if x.type == "MultiPoint" else x)

    def _fill_na_if_required(self, attr, tmp_attr):
        """Fill NA values if attribute is required"""
        if self.attr_required[attr]:
            tmp_attr[attr] = tmp_attr[attr].apply(lambda x: self.attr_dummy[attr] if pd.isnull(x) else x)
        else:
            tmp_attr = tmp_attr[tmp_attr[attr].notna()]
        return tmp_attr

    def _set_datatype(self, attr, tmp_attr):
        """set datatype of series
        convert int datatype to string"""
        if self.attr_dtype[attr] is np.int64:
            # int dtype can't handle NaN values, therefore converted to string
            to_int = tmp_attr.astype(self.attr_dtype[attr])
            return to_int.astype('object')
        else:
            return tmp_attr.astype(self.attr_dtype[attr])

    # def _table_to_data_frame(self, in_table, input_fields=None, where_clause=None, prefix="rel_"):
    #     """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    #     input fields using an arcpy.da.SearchCursor."""
    #     OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    #     if input_fields:
    #         final_fields = [OIDFieldName] + input_fields
    #     else:
    #         final_fields = [field.name for field in arcpy.ListFields(in_table)]
    #     data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    #     fc_dataframe = pd.DataFrame(data, columns=final_fields)
    #     fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    #     if prefix:
    #         fc_dataframe = fc_dataframe.add_prefix(prefix)
    #     return fc_dataframe



if __name__ == '__main__':
    pass
