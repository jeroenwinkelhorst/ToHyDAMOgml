"""
Dit script is onderdeel van de tool voor conversie van gegevens uit DAMO naar HyDAMO. Deze code is specifiek opgesteld
voor waterschap Vallei en Veluwe. Toelichting voor het gebruik van dit script staat in de readme (zie hoofdmap).

Dit script is opgesteld door Royal HaskoningDHV in opdracht van waterschap Vallei het Veluwe en is vrij te gebruiken
onder de voorwaarden van de XX licentie.
+ Digitale disclaimer RHDHV?

Vragen en opmerkingen met betrekking tot dit script kun je mailen aan jeroen.winkelhorst[a]rhdhv.com
"""

import os
import re
import warnings
from datetime import datetime
import pandas as pd
import geopandas as gpd
import pyproj
from lxml import etree
from fiona.crs import from_epsg

from tohydamogml.config import XSI_NAMESPACE, NHI_NAMESPACE, GML_NAMESPACE, XSD, XSD_PATH, DEFAULT_CRS


class Gml:
    """
    GML generator
    Generates gml file for input gdf

    """

    def __init__(self, gdf, objectname, outputfolder=None):
        # Declare variables
        self.QNAME = {etree.QName(XSI_NAMESPACE, "schemaLocation"): XSD}
        self.NHI = "{%s}" % NHI_NAMESPACE
        self.GML = "{%s}" % GML_NAMESPACE
        self.NSMAP = {"xsi": XSI_NAMESPACE,
                      "gml": GML_NAMESPACE,
                      "nhi": NHI_NAMESPACE
                      }
        self.objectname = objectname
        self.gdf = gdf
        self.FeatureCollection = None
        if self.gdf.crs is None:
            self.crs = DEFAULT_CRS
        elif type(self.gdf.crs) == dict:
            if 'init' in self.gdf.crs.keys():
                self.crs = self.gdf.crs['init']
        elif type(self.gdf.crs) == pyproj.crs.CRS:
            self.crs = self.gdf.crs.srs
        else:
            self.crs = self.gdf.crs
        self._xsd_schema = None
        self._output_folder = outputfolder

        # Generate GML
        self._generate()


    def _generate(self):
        """
        Generates HyDAMO GML (etree format)
        """
        self.FeatureCollection = etree.Element(self.NHI + "FeatureCollection", self.QNAME, nsmap=self.NSMAP)
        boundedBy = etree.SubElement(self.FeatureCollection, self.GML + "boundedBy")
        Box = etree.SubElement(boundedBy, self.GML + "Box", srsName=self.crs)
        coordinates = etree.SubElement(Box, self.GML + "coordinates")
        if 'geometry' in self.gdf.columns:
            coordinates.text = self._get_bounds()
            # drop rows with empty geometry
            drop_mask = self.gdf['geometry'].is_empty
            print(f"The following objects id's in {self.objectname} do not have valid geometry and are removed: {self.gdf.iloc[:,0][drop_mask].to_list()}")
            self.gdf = self.gdf[~drop_mask]

        for index, row in self.gdf.iterrows():
            featureMember = etree.SubElement(self.FeatureCollection, self.GML + "featureMember")
            obj = etree.SubElement(featureMember, self.NHI + self.objectname)
            for key in row.index:
                if key != 'geometry':
                    if not pd.isnull(row[key]):
                        var = etree.SubElement(obj, self.NHI + str(key))
                        if type(row[key]) is pd.Timestamp:
                            var.text = row[key].strftime("%Y%m%d%H%M%S")
                        else:
                            var.text = str(row[key])
            if 'geometry' in self.gdf.columns:
                if row['geometry'].geom_type == "LineString":
                    lineStringProp = etree.SubElement(obj, self.GML + "lineStringProperty")
                    lineString = etree.SubElement(lineStringProp, self.GML + "LineString", srsName=self.crs)
                    coor_line = etree.SubElement(lineString, self.GML + "coordinates")
                    coor_line.text = self._coor_line(row['geometry'])
                if row['geometry'].geom_type == "Point":
                    pointProp = etree.SubElement(obj, self.GML + "pointProperty")
                    point = etree.SubElement(pointProp, self.GML + "Point", srsName=self.crs)
                    coor_point = etree.SubElement(point, self.GML + "coordinates")
                    coor_point.text = self._coor_point(row['geometry'])
                if row['geometry'].geom_type == "Polygon":
                    raise NotImplementedError
                if row['geometry'].geom_type == "MultiPolygon":
                    print(index)
                    if len(row['geometry'].geoms) == 1:
                        polygonProp = etree.SubElement(obj, self.GML + "polygonProperty")
                        polygon = etree.SubElement(polygonProp, self.GML + "Polygon", srsName=self.crs)
                        outerBound = etree.SubElement(polygon, self.GML + "outerBoundaryIs")
                        linearRing = etree.SubElement(outerBound, self.GML + "LinearRing")
                        coor_pol = etree.SubElement(linearRing, self.GML + "coordinates")
                        coor_pol.text = self._coor_polygon(row['geometry'][0])
                    elif len(row['geometry'].geoms) > 1:
                        warnings.warn(f"MultiPolygon with index {index} has more than one part and is excluded")
                    else:
                        # https://shapely.readthedocs.io/en/latest/manual.html#shapely.ops.cascaded_union
                        raise NotImplementedError

        print("GML scheme generated for", self.objectname)

    def print(self):
        """Print GML string"""
        return print(etree.tostring(self.FeatureCollection, pretty_print=True, encoding='unicode'))

    def write(self, export_folder, ignore_errors=False, skip_validation=False, suffix=""):
        """Write GML to folder with name 'objectname.gml' """
        result_validation = False
        if not skip_validation:
            result_validation = self.validate()
        if (result_validation or ignore_errors) or skip_validation:
            etree.ElementTree(self.FeatureCollection).write(os.path.join(export_folder, self.objectname + suffix + ".gml"),
                                                            pretty_print=True,
                                                            xml_declaration="True", encoding="UTF-8")
            print("GML scheme written to file: ", os.path.join(export_folder, self.objectname + suffix + ".gml"))
        else:
            print("GML file not created due to validation errors")

    def validate(self, write_error_log=False):
        """Validate GML with XSD
        Note that validatoin requires an internet connection
        """
        result = self.xsd_schema.validate(self.FeatureCollection)
        if result:
            print("GML scheme", str(self.objectname), "succesfully validated with XSD scheme")
        else:
            print("GML scheme not valid")
            self._assertvalid(write_error_log)
        if write_error_log:
            self._export_gdf()
        return result

    @property
    def xsd_schema(self):
        """Read XSD schema"""
        if self._xsd_schema is None:
            xsd_tree = etree.parse(
                os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../src", XSD_PATH)))
            self._xsd_schema = etree.XMLSchema(xsd_tree)
        return self._xsd_schema

    @property
    def scheme(self):
        """GML scheme"""
        return self.FeatureCollection

    def _assertvalid(self, write_error_log=False):
        """Validate schema and list errors"""
        try:
            self.xsd_schema.assertValid(self.FeatureCollection)
        except etree.DocumentInvalid as e:
            print("Validation error(s) ", str(self.objectname), ":")
            for error in self.xsd_schema.error_log:
                print("  Line {}: {}".format(error.line, error.message))
            if write_error_log:
                self._error_log()

    def _get_bounds(self):
        """Get geometric bounds"""
        minx = self.gdf.bounds['minx'].min()
        miny = self.gdf.bounds['miny'].min()
        maxx = self.gdf.bounds['maxx'].max()
        maxy = self.gdf.bounds['maxy'].max()
        return str(minx) + "," + str(miny) + " " + str(maxx) + "," + str(maxy)

    def _coor_line(self, geom):
        """Get coordinates of line geometry"""
        return self._coordinate_gmlstring(geom.coords)

    def _coor_point(self, geom):
        """Get coordinates of point geometry"""
        if geom.has_z:
            return str(geom.x) + "," + str(geom.y) + "," + str(geom.z) + " "
        else:
            return str(geom.x) + "," + str(geom.y) + ",0 "

    def _coor_polygon(self, geom):
        """
        Get coordinates of polygon geometry
        """
        return self._coordinate_gmlstring(geom.exterior.coords)

    def _coordinate_gmlstring(self, coords):
        """Converts shape coordinate list to GML string"""
        coordinates = ""
        if len(coords.xy) == 3:
            for x, y, z in zip(coords.xy[0], coords.xy[1], coords.xy[2]):
                coordinates += str(x) + "," + str(y) + "," + str(z) + " "
        elif len(coords.xy) == 2:
            for x, y in zip(coords.xy[0], coords.xy[1]):
                coordinates += str(x) + "," + str(y) + ",0 "
        else:
            raise ValueError("Coordinate array has unsupported dimensions")
        return coordinates

    def _error_log(self):
        """Write validation errors to shapefile"""
        code = []
        msg = []
        geom = []
        folder = self.output_folder

        for error in self.xsd_schema.error_log:
            [level_parent, level_FeatureCollection, level_featureMember, *other] = error.path.split(r'/')
            loc_fm = int(re.findall('[0-9]+', level_featureMember)[0])
            featureMember = list(self.FeatureCollection)[loc_fm]
            id = list(featureMember)[0].find("{http://www.nhi.nu/gml}code").text

            code.append(id)
            msg.append(error.message)
            if 'geometry' in self.gdf.columns:
                geom.append(self.gdf[self.gdf['code'] == id]['geometry'].values[0])

        if 'geometry' in self.gdf.columns:
            gdf = gpd.GeoDataFrame(data={"code": code, "error": msg}, index=code, geometry=geom, crs=self.crs)
            filename = os.path.join(folder, str(self.objectname) + "_XSD_errorlog.shp")
            gdf.to_file(filename)
            print(f"Error log written to {filename}")
        else:
            # Write log to csv
            df = pd.DataFrame(data={"code": code, "error": msg}, index=code)
            filename = os.path.join(folder, str(self.objectname) + "_XSD_errorlog.csv")
            df.to_csv(filename)
            print(f"Error log written to {filename}")

    @property
    def output_folder(self):
        """Make dir is not exist"""
        if self._output_folder is None:
            folder = os.path.join('log', datetime.today().strftime("%Y%m%d_%H%M"))
            os.makedirs(folder)
            self._output_folder = folder
        return self._output_folder

    def _export_gdf(self):
        # Create geodateframe and write to shape

        if 'geometry' in self.gdf.columns:
            self.gdf.to_file(os.path.join(self.output_folder, str(self.objectname) + ".gpkg"), driver="GPKG")
            print("Geopackage exported to", os.path.join(self.output_folder, str(self.objectname) + ".gpkg"))
        else:
            # Write log to csv
            self.gdf.to_csv(os.path.join(self.output_folder, str(self.objectname) + ".csv"))
            print("Table exported to", os.path.join(self.output_folder, str(self.objectname) + ".csv"))


if __name__ == '__main__':
    pass
