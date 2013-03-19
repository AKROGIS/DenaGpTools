import arcpy
import os.path


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "DENA 2013 Tools"
        self.alias = "GP Tools for Denali"

        # List of tool classes associated with this toolbox
        self.tools = [ShapeImport]


class ShapeImport(object):
    # For a class definition, see http://resources.arcgis.com/en/help/main/10.1/index.html#/Defining_a_tool_in_a_Python_toolbox/001500000024000000/
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "ShapeImport"
        self.description = "Adds a shapefile to a GDB with a column for the shape name"
        self.canRunInBackground = False

    def getParameterInfo(self):
        #See http://resources.arcgis.com/en/help/main/10.1/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/

        param0 = arcpy.Parameter(
            displayName="Shapefile",
            name="shapefile",
            datatype="DEShapefile",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="GDB Feature Class",
            name="geodatabase",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Name Field",
            name="name_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
            
        #param2 must be a text field from param1
        param2.parameterDependencies = [param1.name]
        param2.filter.list = ["Text"]
        
        param3 = arcpy.Parameter(
            displayName="Field Mapping",
            name="field_mapping",
            datatype="GPFieldMapping",
            parameterType="Optional",
            direction="Input")
        
        return [param0, param1, param2, param3]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        #See http://resources.arcgis.com/en/help/main/10.1/index.html#/Customizing_tool_behavior_in_a_Python_toolbox/00150000002m000000/
        
        #set default field name - this does not work.  Can't set the parameter to a field object
        if parameters[1].value:
            if not parameters[2].altered:
                for field in arcpy.Describe(parameters[1].value).fields:
                    if field.type == "String" and field.name.lower() == "filename":
                        #parameters[2].valueAsText = field.name  #can't set ValueAsText
                        #parameters[2].value = field.name  #Validation error field.Name is text, not field object
                        parameters[2].value = field  # Leaves value as null
                        break
        
        #Setup field mapping
        if (not parameters[0].hasBeenValidated):
            joinFeatures = parameters[0].value
            fieldMappings = arcpy.FieldMappings()
            if joinFeatures:
                fieldMappings.addTable(joinFeatures)
            parameters[3].value = fieldMappings.exportToString()
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        # check that geometries match
        if parameters[0].value and parameters[1].value:
            if arcpy.Describe(parameters[0].value).shapeType != arcpy.Describe(parameters[1].value).shapeType:
                parameters[1].setErrorMessage("Geometry does not match Shapefile.")
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        shapefile = parameters[0].valueAsText
        featureClass = parameters[1].value
        fileNameFieldName = parameters[2].valueAsText
        fieldMapping = parameters[3].value
        AddShapefile(shapefile, featureClass, fileNameFieldName, fieldMapping)
        return

def AddShapefile(shapefile, featureClass, fileNameFieldName, fieldMapping):
    tempShapefile = None
    try:
        # get basename of shapefile without extension
        fileName = os.path.splitext(os.path.split(shapefile)[1])[0]
        # copy shapefile to a temp (in-memory) feature class.
        tempShapefile = arcpy.FeatureClassToFeatureClass_conversion(shapefile, "in_memory", "temp_shapefile", "")
        #tempWorkspace = arcpy.env.scratchGDB
        #tempName = arcpy.CreateUniqueName("addShape", tempWorkspace)
        #tempName = os.path.split(tempName)[1]
        #arcpy.AddWarning("workspace: " + tempWorkspace + " name: " + tempName)
        #tempShapefile = arcpy.FeatureClassToFeatureClass_conversion(shapefile, tempWorkspace, tempName, "")
        # add filename field to temp shapefile if it doesn't exist
        if not hasField(tempShapefile,fileNameFieldName):
            arcpy.AddField_management(tempShapefile, fileNameFieldName, "TEXT")
            if hasField(tempShapefile,fileNameFieldName):
                arcpy.AddWarning("has field")
            else:
                arcpy.AddWarning("no has field")
            #add this new field to the field mapping
            fm = arcpy.FieldMappings()
            fm.addTable(tempShapefile)
            for f in fm.fieldMappings:
                if f.outputField.name == fileNameFieldName:
                    fieldMap = f
            
            #fieldMap = arcpy.FieldMap()
            #fieldMap.addInputField(tempShapefile,fileNameFieldName)
            #fieldMap.addInputField(shapefile,fileNameFieldName)
            #fieldMap.addInputField("in_memory/temp_shapefile",fileNameFieldName)
            #type_name = fieldMap.outputField
            #type_name.name = fileNameFieldName
            #fieldMap.outputField = type_name
            arcpy.AddWarning("field Map:" + str(fieldMap) + " type " + str(type(fieldMap)))
            arcpy.AddWarning("input count " + str(fieldMap.inputFieldCount) + " output field " + fieldMap.outputField.name)
            arcpy.AddWarning("input 1 " + fieldMap.getInputTableName(0) + " " + fieldMap.getInputFieldName(0))
            fieldMapping.addFieldMap(fieldMap)
        # calculate value of filename field in new temp shapefile
        arcpy.CalculateField_management(tempShapefile, fileNameFieldName, '"' + fileName + '"')
        # append shapefile to output FC, using field mapping.
        arcpy.Append_management([tempShapefile], featureClass, "NO_TEST", fieldMapping)
    finally:
        #delete temp shapefile
        if tempShapefile:
            arcpy.Delete_management(tempShapefile)

def hasField(featureClass,fieldName):
    for field in arcpy.ListFields(featureClass):
        if field.name.lower() == fieldName.lower():
            return True
    return False