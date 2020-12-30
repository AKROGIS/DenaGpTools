# Denali Geoprocessing Tools

An ArcGIS python toolbox created for Denali NPP.
The tool box has the following tools

* **ShapeImport** - Appends a shapefile to an existing
feature class in a geodatabase
(file, personal or enterprise). An existing text field
in the destination feature class is selected to contain
the name of the shapefile.  This is useful for aggregating
a collection of similar shapefiles (for example the same
data is collected every year in a new shapefile named with
the year).

## Build

The toolbox does not need to be "built" to be used.
It is dependent on python 2.7.x,
[arcpy](https://desktop.arcgis.com/en/arcmap/latest/analyze/arcpy/what-is-arcpy-.htm)
and a licensed copy of ArcGIS Desktop 10.x.

## Deploy

Copy `DenaGPTools.pyt` to any folder accessible to
ArcGIS Desktop 10.x

## Using

In ArcMap or ArcCatalog

* Open the Geoprocessing Toolbox window.
* Right click and `Add Toolbox...`.
* Browse to and select the file `DenaGPTools.pyt`.
* Expand the toolbox.
* Open the tool of your choice.
* Each input parameter is documented to explain how
  to properly use the tool.
