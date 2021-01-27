# -*- coding: utf-8 -*-

"""
ArcGIS Python Toolbox with geoprocessing tools for Denali NPP.

Written for Python 2.7; should work with Python 3.x.
Requires the Esri ArcGIS arcpy module.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os.path

import arcpy


class Toolbox(object):
    """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""

    # This class is specified by esri's Toolbox framework
    # pylint: disable=useless-object-inheritance,too-few-public-methods

    def __init__(self):
        self.label = "DENA 2013 Tools"
        self.alias = "GP Tools for Denali"

        # List of tool classes associated with this toolbox
        self.tools = [ShapeImport]


class ShapeImport(object):
    """GP Tool to import a group of shapefiles."""

    # A GP Tool class structure is specified by esri's Toolbox framework.
    # https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/defining-a-tool-in-a-python-toolbox.htm
    # pylint: disable=useless-object-inheritance,invalid-name,no-self-use,unused-argument

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ShapeImport"
        self.description = "Adds a shapefile to a GDB with a column for the shape name"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Set up the input form with the parameter list and options."""

        param0 = arcpy.Parameter(
            displayName="Shapefile",
            name="shapefile",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input",
        )

        param1 = arcpy.Parameter(
            displayName="GDB Feature Class",
            name="geodatabase",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
        )

        param2 = arcpy.Parameter(
            displayName="Name Field",
            name="name_field",
            datatype="Field",
            parameterType="Required",
            direction="Input",
        )

        # param2 must be a text field from param1
        param2.parameterDependencies = [param1.name]
        param2.filter.list = ["Text"]

        param3 = arcpy.Parameter(
            displayName="Field Mapping",
            name="field_mapping",
            datatype="GPFieldMapping",
            parameterType="Optional",
            direction="Input",
        )

        return [param0, param1, param2, param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # set default field name - this does not work.  Can't set the parameter to a field object
        if parameters[1].value:
            if not parameters[2].altered:
                for field in arcpy.Describe(parameters[1].value).fields:
                    if field.type == "String" and field.name.lower() == "filename":
                        # parameters[2].valueAsText = field.name  #can't set ValueAsText
                        # parameters[2].value = field.name  #Validation error field.Name
                        # is text, not field object
                        parameters[2].value = field  # Leaves value as null
                        break

        # Setup field mapping
        if not parameters[0].hasBeenValidated:
            join_features = parameters[0].value
            field_mappings = arcpy.FieldMappings()
            if join_features:
                field_mappings.addTable(join_features)
            parameters[3].value = field_mappings.exportToString()

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # check that geometries match
        if parameters[0].value and parameters[1].value:
            if (
                arcpy.Describe(parameters[0].value).shapeType
                != arcpy.Describe(parameters[1].value).shapeType
            ):
                parameters[1].setErrorMessage("Geometry does not match Shapefile.")

    def execute(self, parameters, messages):
        """The source code of the tool."""
        shapefile = parameters[0].valueAsText
        feature_class = parameters[1].value
        filename_fieldname = parameters[2].valueAsText
        field_mapping = parameters[3].value
        add_shapefile(shapefile, feature_class, filename_fieldname, field_mapping)


def add_shapefile(shapefile, feature_class, filename_fieldname, field_mapping):
    """Appends a shapefile to a featureclass, writing the shapefile name into
    the fileNameFieldName field in the featureClass."""

    temp = None
    try:
        # get basename of shapefile without extension
        filename = os.path.splitext(os.path.split(shapefile)[1])[0]
        # copy shapefile to a temp (in-memory) feature class.
        temp = arcpy.FeatureClassToFeatureClass_conversion(
            shapefile, "in_memory", "temp_fc", ""
        )
        # add filename field to temp feature class if it doesn't exist
        if not has_field(temp, filename_fieldname):
            arcpy.AddField_management(temp, filename_fieldname, "TEXT")
            # Add the new field to the user's field mappings.
            # because the filedmappings were created with AddTable(), we cannot call AddFieldMap()
            new_mappings = arcpy.FieldMappings()
            field_map = arcpy.FieldMap()
            field_map.addInputField(temp, filename_fieldname)
            new_mappings.addFieldMap(field_map)
            for oldmap in field_mapping.fieldMappings:
                new_mappings.addFieldMap(oldmap)
            field_mapping = new_mappings
        # write the shapefile filename in all rows of the temp feature class
        arcpy.CalculateField_management(temp, filename_fieldname, '"' + filename + '"')
        # append temp feature class to output feature class, using field mapping.
        arcpy.Append_management([temp], feature_class, "NO_TEST", field_mapping)
    finally:
        # delete temp feature class
        if temp:
            arcpy.Delete_management(temp)


def has_field(feature_class, field_name):
    """Returns true if the feature class has a field named field_name."""

    for field in arcpy.ListFields(feature_class):
        if field.name.lower() == field_name.lower():
            return True
    return False
