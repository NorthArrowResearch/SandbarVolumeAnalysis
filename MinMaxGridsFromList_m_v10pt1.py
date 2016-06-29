# MinMaxGridsFromList_cm_v10pt1.py
# Create Min and Max Grids from GRIDS selected from a list
# Tim Andrews
# July 2, 2013
# ArcGIS Version 10.1
# This script requires an input list of GRIDS and
# an output file geodatabase
#
# Parameter list
#                                           Parameter Properties
# Program Name                Display Name              Data type                       Type      Direction
# arcpy.GetParameterAsText(0) inList                    Geodataset                      Required  Input  
# arcpy.GetParameterAsText(1) outFGDB                   Workspace or Feature Dataset    Required  Input
#
import re
import sys
import string
import os
import arcpy

from arcpy import env
from arcpy.sa import *

# Set environment settings, i.e., allow for the overwriting
#  of file geodatabases, if they previously exist
arcpy.env.overwriteOutput = True

# Turn on history logging so that a history log file is written
arcpy.LogHistory = True

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Create a spatial reference object using a factory code
# spatialRef = arcpy.SpatialReference()
# spatialRef.factoryCode = 26949
# spatialRef.create()

# Use the projection file as input to the SpatialReference class
prjFile = r"C:\ArcGIS\Desktop10.1\Coordinate Systems\USGS_Favorites\NAD 1983 (2011) StatePlane Arizona Central FIPS 0202 (Meters).prj"
spatialRef = arcpy.SpatialReference(prjFile)

# Set the environment output Coordinate System
arcpy.env.outputCoordinateSystem = spatialRef
arcpy.AddMessage("Set Output Spatial Reference to NAD 1983 (2011) StatePlane Arizona Central FIPS 0202 (Meters)")
arcpy.AddMessage("")

# Acquire Input Parameters defined above
inList = arcpy.GetParameterAsText(0)
outFGDB = arcpy.GetParameterAsText(1)

arcpy.AddMessage("")

try:

  count = 0

  # Parse out first raster and its date
  inputlist = inList.split(";")

  # Temp Lists start with first raster
  inList = inputlist[0].replace("\\","/")
  tmpMaxList = inList
  tmpMinList = inList
  arcpy.AddMessage("First Input Raster is " + str(tmpMaxList))

  # Date is known to be the last 6 characters
  # We only want a 4 digits of 6 digit date (yr and month)
  lentmpList = len(tmpMaxList)
  initDate = str(tmpMaxList[lentmpList - 6:lentmpList - 2])
  arcpy.AddMessage("Initial Date is " + initDate)
  arcpy.AddMessage("")
  
  # Parse out file geodatabase and workspace
  out_FGDB = outFGDB.replace("\\","/")
  tmp_path = tmpMaxList.replace("\\","/")
  tmp_fgdb = os.path.split(tmp_path)[0]
  out_wksp = os.path.split(out_FGDB)[0]
  # out_fgdb = tmp_fgdb + "/"

  arcpy.AddMessage("Output Workspace is: " + out_wksp)  
  arcpy.Workspace = str(out_wksp)
  arcpy.AddMessage("Output File Geodatabase is: " + out_FGDB)
  arcpy.AddMessage("")
 
  for input in inputlist:
    if count > 0:
      inputFix = input.replace("\\","/")
      tmpMaxList += (";" + inputFix)
      tmpMinList += (";" + inputFix)        
      arcpy.AddMessage("tmpMinList is " + str(tmpMinList))
      arcpy.AddMessage("tmpMaxList is " + str(tmpMaxList))        
      lencurInput = len(input)
      lastDate = str(input[lencurInput - 6:lencurInput - 2])
      arcpy.AddMessage("Last Date is " + lastDate)
      arcpy.AddMessage("")
      
      # outMAXGrid = (out_FGDB + "mx_" + initDate + "_" + lastDate)
      # outMINGrid = (out_FGDB + "mn_" + initDate + "_" + lastDate)
      
      outMAXGrid = ("mx_" + initDate + "_" + lastDate)
      outMINGrid = ("mn_" + initDate + "_" + lastDate)
      
      arcpy.AddMessage("Output MAX Grid Name is is " + outMAXGrid)
      arcpy.AddMessage("Output MIN Grid Name is is " + outMINGrid)
      arcpy.AddMessage("")

      # Process: MosaicToNew
      # Usage: MosaicToNewRaster_management(inputs;inputs..., output_location, raster_dataset_name_with_extension, {coordinate_system_for_the_raster}
      #   8_BIT_UNSIGNED | 1_BIT | 2_BIT | 4_BIT | 8_BIT_SIGNED | 16_BIT_UNSIGNED | 16_BIT_SIGNED | 32_BIT_FLOAT
      #   32_BIT_UNSIGNED | 32_BIT_SIGNED | | 64_BIT {cellsize} number_of_bands {LAST | FIRST | BLEND  | MEAN 
      #   | MINIMUM | MAXIMUM} {FIRST | REJECT | LAST | MATCH}
      arcpy.MosaicToNewRaster_management(str(tmpMaxList), (str(out_FGDB) + "/"), str(outMAXGrid), spatialRef, "32_BIT_FLOAT", "1","1", "MAXIMUM", "#")
      arcpy.AddMessage("Created Maximum GRID = " + str(outMAXGrid))
      arcpy.MosaicToNewRaster_management(str(tmpMinList), (str(out_FGDB) + "/"), str(outMINGrid), spatialRef, "32_BIT_FLOAT", "1","1", "MINIMUM", "#")
      arcpy.AddMessage("Created Minimum GRID = " + str(outMINGrid))
      arcpy.AddMessage("")
      tmpMinList = ""
      tmpMaxList = ""      
      tmpMaxList = (out_FGDB + "/" + outMAXGrid) 
      tmpMinList = (out_FGDB + "/" + outMINGrid)
        
    count = count + 1
    arcpy.AddMessage("Count = " + str(count))
    arcpy.AddMessage("")

  # Build output names
  difGrid = (out_FGDB + "/" + "max_min")
  rasMax = (out_FGDB + "/" + outMAXGrid)
  rasMin = (out_FGDB + "/" + outMINGrid)
  
  # Process: Minus (requires Spatial Analyst)
  outMinus = Minus(rasMax, rasMin)
  arcpy.AddMessage("")  
  arcpy.AddMessage("Created Difference GRID = " + str(rasMax) + " - " + str(rasMin))
  
  # Save the output 
  outMinus.save(difGrid)
  arcpy.AddMessage("")  
  arcpy.AddMessage("Saved Difference GRID = " + str(difGrid))

  # Use MakeFeatureLayer to create a selectable layer
  #arcpy.MakeFeatureLayer(fc, "dissolveLYR")
   
  # Check in the ArcGIS Spatial Analyst extension license
  arcpy.CheckInExtension("Spatial")
  
except:
  # If an error occurred while running a tool, then print the messages.
  print arcpy.GetMessages()
