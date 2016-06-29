# -*- coding: cp1252 -*-
# VolumePerSite_vFeb2014.py
# Calculate Volumes per site from a folder of Topo XYZ files.
# Tim Andrews
# February 12, 2014
# ESRI ArcGIS Version 10.1
#
# Parameter list
# 
# Program Variable Name       Display Name              Data type                       Type      Direction ObtainedFrom    Filter
# arcpy.GetParameterAsText(0) outFGDB                   Workspace or Feature Dataset    Required  Input
# arcpy.GetParameterAsText(1) inFolder                  Folder                          Required  Input
# arcpy.GetParameterAsText(2) Minimum Surface(GRID)     Raster Dataset      Required  Input
# arcpy.GetParameterAsText(3) Channel Boundary        Feature Class     Required  Input
# arcpy.GetParameterAsText(4) Eddy Boundary       Feature Class     Required  Input
# arcpy.GetParameterAsText(5) StageLUTable          Table       Required  Input
# arcpy.GetParameterAsText(6) Aggregation Distance  Double              Required  Input
# arcpy.GetParameterAsText(7) Stage               Field       Required  Input     StageLUTable    Field(double)
# arcpy.GetParameterAsText(8) Site                String        Required  Input                     Value List
# arcpy.GetParameterAsText(9) Bin Size                Double        Required  Input                     Value List
# arcpy.GetParameterAsText(10) Delete Points?   Boolean       Required  Input
# arcpy.GetParameterAsText(11) Delete AggBoundary?  Boolean       Required  Input

def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
    "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('(-*\d+\.\d*)' , s) ]

def unique_values(table, field):
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor})

def unique_values_2(table, field):
    data = arcpy.da.TableToNumPyArray(table, [field])
    return numpy.unique(data[field])

def twodigityr_fourdigityr(inYr, nowYr):
    if int(inYr) > int(nowYr):
        # Site YR is > than Current YR so add 1900
        return (int(inYr) + 1900)
    else:
        # Site YR is <=  Current YR so add 2000
        return (int(inYr) + 2000)

def calcVolume(inBoundary, volFilename, wsl, inTIN, fltBinSize, blnAboveWSL):

    field1 = "Z_MAX"
    field2 = "Z_MIN"

    # Pass both boundaries and use the absolute Zmax of the two boundaries

    try:
        with arcpy.da.SearchCursor(inBoundary, (field1,field2)) as cursor:
            for row in cursor:
                ZmaxTIN = row[0]
                ZminTIN = row[1]
                #arcpy.AddMessage("TIN Z_MAX = " + str(ZmaxTIN))
                #arcpy.AddMessage("TIN Z_MIN = " + str(ZminTIN))
                arcpy.AddMessage(" ")
                
                if ((ZmaxTIN <= 0) or (ZminTIN <= 0)):
                    arcpy.AddMessage("Cannot get boundary values from " + inBoundary + ". Skipping volume calculation!")
                    arcpy.AddMessage("")
                    return False
                else:
                    processVol = True
                        
        if (processVol == True):
            
            numBinsBelowWSL = (wsl - ZminTIN) / (fltBinSize)
            numLoBins = math.ceil(numBinsBelowWSL)
            baseZ = (wsl - (numLoBins * fltBinSize))                    
            numBinsAboveWSL = (ZmaxTIN - wsl) / (fltBinSize)
            numHiBins = math.ceil(numBinsAboveWSL)           
            ceilingZ = (wsl + ((numHiBins + 1) * fltBinSize))
            #arcpy.AddMessage("Ceiling Z = " + str(ceilingZ))

            if (blnAboveWSL == True):
                zCurrent = round(wsl, 2)
                # arcpy.AddMessage("Start Elevation = water surface level = " + str(zCurrent))
            else:
                zCurrent = baseZ
                # arcpy.AddMessage("Start Elevation = " + str(zCurrent))
            
            # arcpy.AddMessage("WSL Elevation = " + str(wsl))
            # arcpy.AddMessage("Number of Bins below 8k wsl = " + str(numLoBins))
            # arcpy.AddMessage("Number of Bins above 8k wsl = " + str(numHiBins))
            # arcpy.AddMessage("Base Elevation = " + str(baseZ))
            # arcpy.AddMessage("Ceiling Elevation = " + str(ceilingZ))
    
            loopcount = 0
    
            while zCurrent <= ceilingZ:
                # Process: Surface Volume...
                arcpy.SurfaceVolume_3d(str(inTIN), volFilename, "ABOVE", zCurrent, "")
                loopcount = loopcount + 1
                zCurrent = zCurrent + fltBinSize

            arcpy.AddMessage("Wrote " + str(loopcount) + "  volume calculation iterations to " + volFilename)
            arcpy.AddMessage(" ")
            return True
            
    except:
        print arcpy.GetMessages()
    

import sys
from os import path
import re
import string
import os
import glob
import fileinput
import csv
import exceptions, sys, traceback
import datetime
import math
import numpy
import arcpy
from arcpy import env
from arcpy.sa import *

# Set environment settings, i.e., allow for the overwriting
# of file geodatabases, if they previously exist
arcpy.env.overwriteOutput = True

# Use the projection file as input to the SpatialReference class
# Check if this FILE EXISTS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# prjFile = r"C:\ArcGIS\Desktop10.1\Coordinate Systems\USGS_Favorites\NAD 1983 (2011) StatePlane Arizona Central FIPS 0202 (Meters).prj"
prjFile = r"C:\ArcGIS\Desktop10.1\Coordinate Systems\USGS_Favorites\NAD 1983 StatePlane Arizona Central FIPS 0202 (Meters).prj"
spatialRef = arcpy.SpatialReference(prjFile)

# Set the environment output Coordinate System
arcpy.env.outputCoordinateSystem = spatialRef

# arcpy.AddMessage("Set Output Spatial Reference to NAD 1983 (2011) StatePlane Arizona Central FIPS 0202 (Meters)")
arcpy.AddMessage("")

# Turn on history logging so that a history log file is written
arcpy.LogHistory = True

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")

# Obtain a license for the ArcGIS 3D Analyst extension
# arcpy.CheckOutExtension("3D")

# Local variables...
inFolder = ""
outFolder = ""
inSide = ""
InField = "POINT_Z"
count = int(0)
blnDelauny = bool(1)
processVol = False
cur4digitYR = datetime.date.today().year
# arcpy.AddMessage("Current 4 digit Year = " + str(cur4digitYR))
cur2digitYR = str(cur4digitYR)[2:4]
# arcpy.AddMessage("Current 2 Digit Year = " + str(cur2digitYR))

# create empty FC output list for deleting temp point FC's
outPointFCList = []

# create empty AggPointFC output list for deleting temp point FC's
aggPointFCList = []

# create empty TIN output list for deleting TINS and sorting.
outTINList = []

# Acquire Input Parameters defined above
outFGDB = arcpy.GetParameterAsText(0)
inFolder = arcpy.GetParameterAsText(1)
minSurface = arcpy.GetParameterAsText(2)
chanBnd = arcpy.GetParameterAsText(3)
eddyBnd = arcpy.GetParameterAsText(4)
wslTable = arcpy.GetParameterAsText(5)
aggDist = arcpy.GetParameterAsText(6)
inStage = arcpy.GetParameterAsText(7)
inSite = arcpy.GetParameterAsText(8)
binSize = arcpy.GetParameterAsText(9)
blnDeletePointFC = arcpy.GetParameterAsText(10)
blnDeleteAggBoundary = arcpy.GetParameterAsText(11)

fltBinSize = float(binSize)
# Check if table has Site Field and at least wsl8k field!!!!!!!!!!!!!!!!!!

theSite = None
wsl_8k = None
wsl_25k = None

scriptPath = os.path.dirname(os.path.realpath(__file__))
StageDischargePath = os.path.join(scriptPath, 'LookupTables', 'StageDischarge.csv')
arcpy.AddMessage("Path to script {}".format(StageDischargePath))

arcpy.AddMessage("Looking for site in CSV file {}".format(inSite))
try: 
    with open(StageDischargePath, 'r') as f:
        records = csv.DictReader(f)
        for row in records:
            if row['Site'] == inSite:
                arcpy.AddMessage("Found")
                theSite = row['Site']
                wsl_8k = row['wsl8k']
                wsl_25k = row['wsl25k']
except:
    arcpy.AddMessage("ERROR Reading {}".format(StageDischargePath))

if theSite is None:
    arcpy.AddMessage("ERROR: Site Not Found")
    print arcpy.GetMessages()
    sys.exit()
if wsl_8k is None:
    arcpy.AddMessage("ERROR: wsl_8k Not Found")
    print arcpy.GetMessages()
    sys.exit()
if wsl_25k is None:
    arcpy.AddMessage("ERROR: wsl_25k Not Found")
    print arcpy.GetMessages()
    sys.exit()
arcpy.AddMessage("Continuing for site: {} with wsl_8k: {} and wsl_25k: {}".format(theSite, wsl_8k, wsl_25k))
print arcpy.GetMessages()

decAggDist = float(aggDist)

# Some functions don't work without setting a workspace!
arcpy.env.Workspace = inFolder.replace("\\","/")

# Flip slash on output fgdb, and create output FGDB Path
out_fgdb = str(outFGDB).replace("\\","/")
outFGDBPath = out_fgdb + "/"
# arcpy.AddMessage("Output FGDB is: " + out_fgdb)
# arcpy.AddMessage("")

# Get the Root directory of the Output FGDB 
outRoot = os.path.split(outFGDB)[0]
# arcpy.AddMessage("Output Root Folder is: " + str(outRoot))
# arcpy.AddMessage("")

# Create an output Root Path (for TINS)
out_path = str(outRoot).replace("\\","/")
outPath = out_path + "/"

# Flip slash on channel boundary
chBndy = str(chanBnd).replace("\\","/")

# Flip slash on eddy boundary
edBndy = str(eddyBnd).replace("\\","/")

# Build names to copy the channel and eddy boundary
minChanBndy = (outFGDBPath + "minChanBndy")
minEddyBndy = (outFGDBPath + "minEddyBndy")

# Execute Copy
arcpy.Copy_management(chBndy, minChanBndy, "")
arcpy.Copy_management(edBndy, minEddyBndy, "")

# create empty boundary feature class list
boundaryFCList = []
boundaryFCList.append(minChanBndy)
boundaryFCList.append(minEddyBndy)

# Flip slash on minimum surface
minSurf = minSurface.replace("\\","/")
# arcpy.AddMessage("MIN SURFACE path is " + minSurf)
# arcpy.AddMessage("")

# Get name of min surface
inSurfName = os.path.split(minSurf)[1]
# arcpy.AddMessage("Name Only of minimum surface is " + str(inSurfName))

surfSplit = re.split("\_", inSurfName)
#arcpy.AddMessage("Split on all underscores of minimum surface name is " + str(surfSplit))

# Get start date
startDateRaw = surfSplit[1]
# arcpy.AddMessage("Split1 is " + str(startDateRaw))
  
# Get end date
endDateRaw = surfSplit[2]
# arcpy.AddMessage("Split2 is " + str(endDateRaw))

# Pick off Start 2 digit yr and mth
yrStart2digits = startDateRaw[:2]
startMth = startDateRaw[2:4]

# Pick off End 2 digit yr and mth
yrEnd2digits = endDateRaw[:2]
endMth = endDateRaw[2:4]

# Convert start yr to 4 digits
startYR4digits = twodigityr_fourdigityr(yrStart2digits, cur2digitYR)
# arcpy.AddMessage("After subroutine, 4 digit start year is = " + str(startYR4digits))

# Convert end yr to 4 digits
endYR4digits = twodigityr_fourdigityr(yrEnd2digits, cur2digitYR)
# arcpy.AddMessage("After subroutine, 4 digit end year is = " + str(endYR4digits))

# Build date range
minSurfDateRange = str(startMth) + "_" + str(startYR4digits) + "_" + str(endMth) + "_" + str(endYR4digits)
# arcpy.AddMessage("Date Range = " + str(minSurfDateRange))

#CalculateStatistics_management (in_raster_dataset, {x_skip_factor},
#    {y_skip_factor}, {ignore_values}, {skip_existing}, {area_of_interest})
arcpy.CalculateStatistics_management(minSurf)

# Process: GetRasterProperties_management.
# GetRasterProperties_management (in_raster, {property_type}, {band_index})
InPropertyType = "MINIMUM"
propResult = arcpy.GetRasterProperties_management(minSurf, InPropertyType)

zMinSurfMin = propResult.getOutput(0)
# zMinSurfMin = long(zMinSurfMin)
zMinSurfMin = float(zMinSurfMin)
arcpy.AddMessage("MIN SURFACE Zmin value = " + str(zMinSurfMin))
arcpy.AddMessage(" ")

# CreateFeatureclass_management (out_path, out_name, {geometry_type}, {template}, {has_m}, {has_z},
#   {spatial_reference}, {config_keyword}, {spatial_grid_1}, {spatial_grid_2}, {spatial_grid_3})
# arcpy.CreateFeatureclass_management(out_fgdb, outMinSurfPoints, "POINT", "", "DISABLED", "ENABLED", spatialRef)
# arcpy.AddMessage("Created FeatureClass " + str(outMinSurfPointsFull))

# Create Points from min_grid
outTempPoints = outFGDBPath + ("temp" + inSite.lower())
# arcpy.RasterToPoint_conversion (in_raster, out_point_features, {raster_field})
arcpy.RasterToPoint_conversion (minSurf, outTempPoints)
# arcpy.AddMessage("Converted Raster to Points")

#Calculate the XY Coordinates
arcpy.AddXY_management(outTempPoints)
#arcpy.AddMessage("Added and Calculated XY Fields to Temp Points")

# Add a POINT_Z field
arcpy.AddField_management(outTempPoints, "POINT_Z", "DOUBLE", "", "", "", "", "NULLABLE")
# arcpy.AddMessage("Added Z Field to Temp Points")

# Calculate the POINT_Z field from the grid_code
# arcpy.CalculateField_management (in_table, field, expression, {expression_type}, {code_block})
arcpy.CalculateField_management(outTempPoints, "POINT_Z", "!grid_code!", "PYTHON_9.3")
# arcpy.AddMessage("Calculated Z Field = grid_code")

# Create Numpy Array to hold data for output a Z-Enabled Point Feature Class
# array = arcpy.da.FeatureClassToNumPyArray(outTempPoints,["OID@", "SHAPE@X", "SHAPE@Y", "POINT_Z"], spatial_reference=spatialRef)
array = arcpy.da.FeatureClassToNumPyArray(outTempPoints, "*", spatial_reference=spatialRef)

# Create a Z_Enabled Feature Class to hold min surface points
outMinSurfPoints = ("minsurfpts" + inSite.lower())
outMinSurfPointsFull = outFGDBPath + outMinSurfPoints

# Delete old min surface points if it exists
if arcpy.Exists(outMinSurfPointsFull):
    arcpy.Delete_management(outMinSurfPointsFull)
    # arcpy.AddMessage("Deleted Existing " + str(outMinSurfPointsFull))
    # arcpy.AddMessage("")

# Create a feature class with x,y,z fields
arcpy.da.NumPyArrayToFeatureClass(array, outMinSurfPointsFull, ("POINT_X", "POINT_Y", "POINT_Z"), spatialRef)

# Calculate the XY, and Z Coordinates
arcpy.AddXY_management(outMinSurfPointsFull)

# Round the X, Y, Z fields
expr = "round(!POINT_Z!, 3)"
arcpy.CalculateField_management(outMinSurfPointsFull, "POINT_Z", expr, "PYTHON")
expr = "round(!POINT_Y!, 3)"
arcpy.CalculateField_management(outMinSurfPointsFull, "POINT_Y", expr, "PYTHON")
expr = "round(!POINT_X!, 3)"
arcpy.CalculateField_management(outMinSurfPointsFull, "POINT_X", expr, "PYTHON")
arcpy.AddMessage("Rounded X,Y,Z fields")

#arcpy.AddMessage("Created minsurface points " + str(outMinSurfPointsFull))
#arcpy.AddMessage(" ")

# Create Aggregate Boundary Output File Name for the minsurface
outAggFC = outMinSurfPointsFull + "_boundary"

# Execute Aggregate Points Method
arcpy.AggregatePoints_cartography(outMinSurfPointsFull, outAggFC, decAggDist)
# arcpy.AddMessage("Created Output Aggregate Boundary " + outAggFC)
# arcpy.AddMessage("")

# Append the AggPoint FC name to the delete list
# aggPointFCList.append(outAggFC)
# aggPointFCList.append(outAggFC + "_Tbl")

# Append FC to boundary list
#boundaryFCList.append(outAggFC)

# Check out the ArcGIS 3D Analyst extension
arcpy.CheckOutExtension("3D")

# Create TIN Name
# outTinName = "minsurf" + inSite
# arcpy.AddMessage("TIN name not lowercase = " + str(outTinName))
outMinTinName = "minsurf_" + inSite.lower() + "_" + minSurfDateRange
outMinTinNameFull = (outPath + outMinTinName)
#arcpy.AddMessage("TIN name lowercase = " + str(outTinNameFull))

if arcpy.Exists(outMinTinNameFull):
    arcpy.Delete_management(outMinTinNameFull)
    arcpy.AddMessage("Deleted Existing " + str(outMinTinNameFull))
    arcpy.AddMessage("")


arcpy.AddMessage("Creating minimum surface TIN ...")

# arcpy.CreateTin_3d (out_tin, {spatial_reference, {in_features}, {constrained_delaunay})
# arcpy.CreateTin_3d(outMinTinNameFull, spatialRef, str(outTempPoints)+ " Shape.Z masspoints", False)
arcpy.CreateTin_3d(outMinTinNameFull, spatialRef, str(outTempPoints)+ " grid_code", False)
arcpy.AddMessage("Finished minimum surface TIN creation")
arcpy.AddMessage(" ")

# Clip the min surface TIN to Aggregation Boundary
arcpy.EditTin_3d(outMinTinNameFull, outAggFC+ " <None> <None> hardclip false", False)
#arcpy.AddMessage("Clipped min surface TIN to Agg Boundary")
#arcpy.AddMessage(" ")

try:

    #for boundaryFC in boundaryFCList:
    # Desired properties separated by semi-colons
    Prop = "Z_Min;Z_Max"

    # Execute AddSurfaceInformation
    # arcpy.ddd.AddSurfaceInformation(boundaryFC, outMinTinNameFull, Prop)
    # arcpy.ddd.AddSurfaceInformation(outAggFC, outMinTinNameFull, Prop)
    arcpy.ddd.AddSurfaceInformation(outAggFC, outMinTinNameFull, Prop, "LINEAR")
    
    #arcpy.AddMessage("Completed adding TIN ZMin, ZMax surface information to " + str(outAggFC))
    #arcpy.AddMessage(" ")
            
    #else:
    #   arcpy.AddMessage("Aggregation FC does have Z! Exiting ...")
    #   arcpy.AddMessage("")
    #   sys.exit()

except arcpy.ExecuteError:
    arcpy.AddMessage("Error executing method!")
    print arcpy.GetMessages()
    
except:
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # Concatenate error information into message string
    pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
    .format(tbinfo, str(sys.exc_info()[1]))
    msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
    # Return python error messages for script tool or Python Window
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)
    arcpy.AddMessage(msgs)

# outTINList.append(outTinNameFull)
# outTINList.append(outTinNameFull) 

# if outFGDB == "":
#  outFGDB = inFolder
theFiles = glob.glob(inFolder+"/*.txt")
count = 0
processVol = False

#arcpy.AddMessage("Before the File Loop")
#print arcpy.GetMessages()

# Loop through all the Text Files
for i in theFiles:

    # Need to check if channel and eddy boundary intersect survey boundary
    processChanVol = False
    processEddyVol = False
    
    inTXTfull = str(i).replace("\\","/")  
    inTXT = os.path.split(inTXTfull)[1]
    inPath = os.path.split(inTXTfull)[0]
    # arcpy.AddMessage("Input Path is: " + inPath)
     
    arcpy.AddMessage("Input Text File is: " + inTXTfull)
    arcpy.AddMessage(" ")
    
    noextName = str(inTXT[:-4])
    result = re.split("\_", noextName)
    # arcpy.AddMessage("Split on all underscores result is " + str(result))
    result2 = re.split("\_", noextName, 1)
    # arcpy.AddMessage("Split on first underscore result is " + str(result2))
    siteNUM = result[0]
    # arcpy.AddMessage("Site Number is " + siteNUM)
    #if len(siteNUM) == 1:
    #    siteNUM = "00" + siteNUM
    #elif len(siteNUM) == 2:
    #    siteNUM = "0" + siteNUM
  
    siteDATE = result[1]
    siteYR = siteDATE[:2]
    siteMthDay = siteDATE[2:6]
    # arcpy.AddMessage("Date is " + siteDATE)
    # arcpy.AddMessage("YR is " + siteYR)
    # arcpy.AddMessage("MTH(2 digits) DAY(2 digits) is " + siteMthDay)
    if int(siteYR) > int(cur2digitYR):
        # arcpy.AddMessage("Site YR is > than Current YR so add 1900")
        siteYR = int(siteYR) + 1900
        # arcpy.AddMessage("Site YR is now = " + str(siteYR))
    else:
        # arcpy.AddMessage("Site YR is <=  Current YR so add 2000")
        siteYR = int(siteYR) + 2000
        # arcpy.AddMessage("Site YR is now = " + str(siteYR))

    siteFULLDATE = str(siteYR) + str(siteMthDay)
        
    # arcpy.AddMessage("Date is " + siteDATE)
    siteNOTE = result[2]
    # arcpy.AddMessage("Note is " + siteNOTE)

    # outRasterName = "SE" + "_" + siteDATE
    outTinName = "surf_" + inSite.lower() + "_" + siteFULLDATE
    #arcpy.AddMessage("TIN name lowercase = " + str(outTinName))
    outTinNameFull = (outPath + outTinName)

    # out_fgdb = (outPath + "/" + siteNUM + inSide + ".gdb")
    # outRasterNameFull = (outFGDBPath + outRasterName)emc
    
    # shortFCName = ("pt" + siteNUM + inSide + "_" + siteFULLDATE)
    shortFCName = ("pt_" + inSite.lower() + "_" + siteFULLDATE)
    outFCNameFull = (outFGDBPath + shortFCName)

    # Get comma delimited x,y,z file contents into a list
    fileHandle = open(inTXTfull, "r")
    inFileLinesList = fileHandle.readlines()
    fileHandle.close()

    # create empty output list
    outFileLinesList = []
    
    # copy only data lines {lines with numeric first character} to output list
    for line in inFileLinesList:
        tmpOut = line.replace(',', ' ')
        lineOut = tmpOut.strip() + '\n'
        pos = lineOut.find("GRID_1m")
        if pos != -1:
            # lineOut = line.strip[0:pos-1] + '\n'
            lineOut = lineOut[0:pos-1] + '\n'
        lineOut = lineOut.strip() + '\n'
        lineChk = lineOut[0]
        if lineChk.isdigit():
            outFileLinesList.append(lineOut)

        outFilename = inTXTfull

        # compare in / out lists to see if need to write file
        if inFileLinesList != outFileLinesList:
            fileHandle = open(outFilename,"w")
            fileHandle.writelines(outFileLinesList)
            fileHandle.close()

    #arcpy.AddMessage("Finished input file check!")
    # arcpy.AddMessage(" ")

    # Process: Create Feature Class...
    # arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, template, has_m, has_z, spatial_reference,
    # config_keyword, spatial_grid_1, spatial_grid_2, spatial_grid_3)

    arcpy.CreateFeatureclass_management(out_fgdb, shortFCName, "POINT", "", "DISABLED", "ENABLED", spatialRef)
    # arcpy.AddMessage("Created FeatureClass " + str(shortFCName))0

    # Open an insert cursor for the new feature class
    cur = arcpy.InsertCursor(outFCNameFull)
   
    # Create a point object needed to create features
    pnt = arcpy.Point()

    # Loop through lines of input file
    for line in fileinput.input(inTXTfull): # Open the input file
        # set the point's ID, X and Y properties
        pnt.ID, pnt.X, pnt.Y, pnt.Z = string.split(line," ")
        # arcpy.AddMessage("ID,X,Y,Z = " + str(pnt.ID) + ", " + str(pnt.X) + ", " + str(pnt.Y) + ", " + str(pnt.Z))
    
        # Create a new row or feature, in the feature class
        feat = cur.newRow()
        # Set the geometry of the new feature to the point
        feat.shape = pnt
        # Insert the feature
        cur.insertRow(feat)
    
    fileinput.close()
    del cur
  
    # arcpy.AddMessage("Created XYZ Point Feature Class: " + outFCNameFull)

    # Append the point FC name to the delete list
    outPointFCList.append(outFCNameFull)

    # Execute Aggregate Points to create aggregate boundary\
    outAggPredisv = outFCNameFull  + "_bndpredisv"
    # AggregatePoints_cartography (in_features, out_feature_class, aggregation_distance)
    arcpy.AggregatePoints_cartography(outFCNameFull, outAggPredisv, decAggDist)
 
    # Dissolve multiple attribute records  
    # Dissolve_management (in_features, out_feature_class, {dissolve_field}, {statistics_fields}, {multi_part}, {unsplit_lines})
    outAggSurveyFC = outFCNameFull + "_boundary"
    arcpy.Dissolve_management (outAggPredisv, outAggSurveyFC)

    # Append the AggPoint FC name to the delete list
    aggPointFCList.append(outAggSurveyFC)
    aggPointFCList.append(outAggSurveyFC + "_Tbl")
  
    #Calculate the XY Coordinates
    arcpy.AddXY_management(outFCNameFull)
    # arcpy.AddMessage("Added XYZ Coordinates to " + outFCNameFull)

    #arcpy.CalculateField_management (in_table, field, expression, {expression_type}, {code_block})
    expr = "round(!POINT_Z!, 3)"
    arcpy.CalculateField_management(outFCNameFull, InField, expr, "PYTHON")
    # arcpy.AddMessage("Rounded POINT_Z field!")

    # arcpy.AddMessage("Before Conditional Statement, CREATE TIN boolean variable is " + blnCreateTIN)
    # Some functions don't work without setting a workspace!
    # arcpy.env.Workspace = out_fgdb

    # using {0} in CreateTin means the first GetParameterAsText(0)
  
    # arcpy.CreateTin_3d (out_tin, {spatial_reference}, {in_features}, {constrained_delaunay})
    # Check out the ArcGIS 3D Analyst extension
    # arcpy.CheckOutExtension("3D")
    
    try:
        # Execute CreateTin
        # arcpy.AddMessage("Creating TIN dataset " + str(outTinName))
        arcpy.CreateTin_3d(outTinNameFull, spatialRef, str(outFCNameFull)+ " Shape.Z masspoints", False)
        # arcpy.AddMessage("Finished creating TIN " + outTinNameFull)

        # Clip the TIN to the Aggregation Boundary
        arcpy.EditTin_3d(outTinNameFull, outAggSurveyFC+ " <None> <None> hardclip false", False)
        #arcpy.AddMessage("Clipped TIN surface to Agg Boundary")
        #arcpy.AddMessage(" ")

        # Build name to copy the site channel and eddy  boundary
        chanBndy = (outFGDBPath + "chanBndy_" + inSite.lower() + "_" + siteFULLDATE)
        eddyBndy = (outFGDBPath + "eddyBndy_" + inSite.lower() + "_" + siteFULLDATE)

        # Execute Copy for channel and eddy boundary
        arcpy.Copy_management(chBndy, chanBndy, "")
        arcpy.Copy_management(edBndy, eddyBndy, "")

        # Desired properties to add to channel and eddy boundary, separated by semi-colons
        Prop = "Z_Min;Z_Max"

        # Get inputs for intersect of survey boundary and channel boundary
        inChanFeatures = [outAggSurveyFC, chanBndy]
        chanIntBndy = (outFGDBPath + "chanIntBndy" + inSite.lower() + "_" + siteFULLDATE)

        # Execute intersection of AggBoundary and Eddy boundary
        arcpy.Intersect_analysis(inChanFeatures, chanIntBndy, "", "", "")

        # Check for empty intersection of channel boundary and survey boundary
        resultChan = int(arcpy.GetCount_management(chanIntBndy).getOutput(0))
        
        if (resultChan > 0):
            # arcpy.AddMessage("Channel intersection is not NULL!")
            # arcpy.AddMessage(" ")
            processChanVol = True

            # Copy the channel intersection boundary
            minchanIntBndy = (outFGDBPath + "minchanIntBndy" + inSite.lower() + "_" + siteFULLDATE)
            arcpy.Copy_management(chanIntBndy, minchanIntBndy, "")

            # Prepare to Copy the survey TIN for clipping to the channel boundary
            chanTinCopy = "chan_" + inSite.lower() + "_" + siteFULLDATE
            chanTinCopyFullName = (outPath + chanTinCopy)

            # Execute CopyTin to create a survey channel TIN Copy
            arcpy.CopyTin_3d(outTinNameFull, chanTinCopyFullName, "CURRENT")

            # Clip the TIN surface to the channel and survey intersection boundary
            # arcpy.EditTin_3d(chanCopyFullName, chBndy+ " <None> <None> hardclip false", False)
            arcpy.EditTin_3d(chanTinCopyFullName, chanIntBndy+ " <None> <None> hardclip false", False)
            # arcpy.AddMessage("Clipped minsurface TINto Channel Boundary")
            # arcpy.AddMessage("")

            # Create min surface TIN Copy Name for the minchan surface
            # outTinCopy = "minchan" + inSite.lower() + "_" + minSurfDateRange
            outTinCopy = "minchan_" + inSite.lower() + "_" + siteFULLDATE
            outMinTinChanCopyFull = (outPath + outTinCopy)

            # Execute CopyTin for Channel TIN Copy
            arcpy.CopyTin_3d(outMinTinNameFull, outMinTinChanCopyFull, "CURRENT")
            # arcpy.AddMessage("Copied TIN " + outTinNameFull + " to " + outTinChanCopyFull)
            # arcpy.AddMessage("")

            # Clip the min surface TIN to the channel boundary
            arcpy.EditTin_3d(outMinTinChanCopyFull, chanIntBndy+ " <None> <None> hardclip false", False)
            # arcpy.AddMessage("Clipped min surface TIN copy to Channel Boundary")
            # arcpy.AddMessage(" ")

            # Execute AddSurfaceInformation to survey channel boundary
            arcpy.ddd.AddSurfaceInformation(chanIntBndy, outTinNameFull, Prop)
            # arcpy.AddMessage("Completed adding surface ZMin, ZMax information to Intersected Channel Boundary")
            # arcpy.AddMessage("")

            # Execute AddSurfaceInformation to minsurface channel boundary attach minsurface Zmin and Zmax
            arcpy.ddd.AddSurfaceInformation(minchanIntBndy, outMinTinChanCopyFull, Prop)         

        else:
            
            # Delete empty intersect poly feature class
            processChanVol = False
            if arcpy.Exists(chanIntBndy):
                arcpy.Delete_management(chanIntBndy)
                # arcpy.AddMessage("Deleted " + str(chanIntBndy))
                # arcpy.AddMessage("")           

        # Get inputs for intersection of AggBoundary and Eddy boundary
        inEddyFeatures = [outAggSurveyFC, eddyBndy]
        eddyIntBndy = (outFGDBPath + "eddyIntBndy" + inSite.lower() + "_" + siteFULLDATE)

        # Execute intersect of AggBoundary and Eddy boundary
        arcpy.Intersect_analysis(inEddyFeatures, eddyIntBndy, "", "", "") 

        # Check for empty intersection of eddy boundary and survey boundary
        resultEddy = int(arcpy.GetCount_management(eddyIntBndy).getOutput(0))
        
        if (resultEddy > 0):
            # arcpy.AddMessage("Eddy intersection is not NULL!")
            # arcpy.AddMessage(" ")
            processEddyVol = True

            # Copy the eddy intersection boundary to attach minsurface Zmin and Zmax
            mineddyIntBndy = (outFGDBPath + "mineddyIntBndy" + inSite.lower() + "_" + siteFULLDATE)
            arcpy.Copy_management(eddyIntBndy, mineddyIntBndy, "")

            # Copy the survey TIN to clip to the eddy intersection boundary
            eddyCopy = "eddy_" + inSite.lower() + "_" + siteFULLDATE
            eddyCopyFullName = (outPath + eddyCopy)

            # Execute CopyTin for Eddy TIN Copy
            arcpy.CopyTin_3d(outTinNameFull, eddyCopyFullName, "CURRENT")
            # arcpy.AddMessage("Copied TIN " + outTinNameFull + " to " + eddyCopyFullName)
            # arcpy.AddMessage("")

            # Clip the TIN to the eddy intersection boundary
            # arcpy.EditTin_3d(eddyCopyFullName, edBndy+ " <None> <None> hardclip false", False)
            arcpy.EditTin_3d(eddyCopyFullName, eddyIntBndy+ " <None> <None> hardclip false", False)
            #arcpy.AddMessage("Clipped TIN surface to Eddy Boundary")
            #arcpy.AddMessage("")

            # Create minsurface TIN Copy Name
            # outTinCopy = "mineddy" + inSite.lower() + "_" + minSurfDateRange
            outTinCopy = "mineddy_" + inSite.lower() + "_" + siteFULLDATE
            outMinTinEddyCopyFull = (outPath + outTinCopy)

            # Execute CopyTin for Eddy TIN Copy
            arcpy.CopyTin_3d(outMinTinNameFull, outMinTinEddyCopyFull, "CURRENT")
            # arcpy.AddMessage("Copied TIN " + outTinNameFull + " to " + outTinEddyCopyFull)
            # arcpy.AddMessage("")

            # Clip the min surface TIN to the intersection of the survey and eddy boundary
            arcpy.EditTin_3d(outMinTinEddyCopyFull, eddyIntBndy+ " <None> <None> hardclip false", False)
            #arcpy.AddMessage("Clipped min surface TIN copy to Eddy Boundary")
            #arcpy.AddMessage(" ")

            # Execute AddSurfaceInformation     
            arcpy.ddd.AddSurfaceInformation(eddyIntBndy, outTinNameFull, Prop)        
            # arcpy.AddMessage("Completed adding surface ZMin, ZMax information to Intersected Eddy Boundary")
            # arcpy.AddMessage("")

            # Execute AddSurfaceInformation to minsurface channel boundary
            #===================================================================================================
            arcpy.ddd.AddSurfaceInformation(mineddyIntBndy, outMinTinEddyCopyFull, Prop)
            #===================================================================================================
            # arcpy.AddMessage("Completed adding surface ZMin, ZMax information to Intersected Channel Boundary")
            # arcpy.AddMessage("")www.msn.com
            
            
        else:
            # Delete empty intersect poly feature class
            processEddyVol = False
            if arcpy.Exists(eddyIntBndy):
                arcpy.Delete_management(eddyIntBndy)
                # arcpy.AddMessage("Deleted " + str(eddyIntBndy))
                # arcpy.AddMessage("")
        

        # +++++++++++++++++++++++++++++++++++++++
        # outTINList.append(outTinNameFull)
        # outTINList.append(chanCopyFullName)
        # outTINList.append(eddyCopyFullName)
        # +++++++++++++++++++++++++++++++++++++++

        # sys.exit()

        # Check in the ArcGIS 3D Analyst extension
        # arcpy.CheckInExtension("3D")
    
    except arcpy.ExecuteError:
        arcpy.AddMessage("Error executing method!")
        print arcpy.GetMessages()
    except:
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
            .format(tbinfo, str(sys.exc_info()[1]))
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        arcpy.AddMessage(msgs)


    field1 = "Z_MAX"
    field2 = "Z_MIN"

    try:
        if (processChanVol == True):
            # The Boundary should have a Z_MAX, and Z_MIN field
            with arcpy.da.SearchCursor(chanIntBndy, (field1,field2)) as cursor:
                for row in cursor:
                    ZmaxTIN = row[0]
                    #arcpy.AddMessage("TIN Z_MAX = " + str(ZmaxTIN))
                    ZminTIN = row[1]
                    #arcpy.AddMessage("TIN Z_MIN = " + str(ZminTIN))
                    #arcpy.AddMessage(" ")
                    if ((ZmaxTIN <= 0) or (ZminTIN <= 0)):
                        arcpy.AddMessage("Cannot get boundary values from " + chanIntBndy + ". Skipping volume calculation!")
                        arcpy.AddMessage(" ")
                        processChanVol = False
                    else:
                        processChanVol = True 
             
    except:
        print arcpy.GetMessages()

    if (processChanVol == True):
        # Need to avoid putting output volume files in Geodatabases!
        # txtFileDef = str(outRoot + "/vol_" + "chan" + inSite.lower() + "_" + siteFULLDATE)
        # txtFile = str(outRoot + "/vol_" + "chan" + inSite.lower() + "_" + siteFULLDATE + ".txt")

        # Calculate Volume of minimum surface channel 
        minChanFile = str(outRoot + "/vol_" + "minchan_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minChanFile):
            arcpy.Delete_management(minChanFile)
            arcpy.AddMessage("Deleted " + str(minChanFile))
            arcpy.AddMessage(" ")

        # minChanBndy = (outFGDBPath + "minChanBndy")
        
        arcpy.AddMessage("Calculating volume for minchan_" + inSite.lower() + "_" + siteFULLDATE + "...")    
        volCalcOK = calcVolume(minchanIntBndy, minChanFile, wsl_8k, outMinTinChanCopyFull, fltBinSize, False)
        # arcpy.AddMessage("Return value from volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed minchan_" + inSite.lower() + "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in minchan_" + inSite.lower() + + "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of minimum surface channel above 8k
        minChanAbove8kFile = str(outRoot + "/vol_" + "minchanAbove8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minChanAbove8kFile):
            arcpy.Delete_management(minChanAbove8kFile)
            arcpy.AddMessage("Deleted " + str(minChanAbove8kFile))
            
        arcpy.AddMessage("Calculating volume for minchanAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(minchanIntBndy, minChanAbove8kFile, wsl_8k, outMinTinChanCopyFull, fltBinSize, True)
        # arcpy.AddMessage("Return value from minsurface chan volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed minchanAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in minchanAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of minimum surface chan above 25k
        minChanAbove25kFile = str(outRoot + "/vol_" + "minchanAbove25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minChanAbove25kFile):
            arcpy.Delete_management(minChanAbove25kFile)
            arcpy.AddMessage("Deleted " + str(minChanAbove25kFile))
            
        arcpy.AddMessage("Calculating volume for minchanAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(minchanIntBndy, minChanAbove25kFile, wsl_25k, outMinTinChanCopyFull, fltBinSize, True)
        #arcpy.AddMessage("Return value from minsurface channel volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed minchanAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in minchanAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of survey channel above 8k
        chanAbove8kFile = str(outRoot + "/vol_" + "chanAbove8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(chanAbove8kFile):
            arcpy.Delete_management(chanAbove8kFile)
            arcpy.AddMessage("Deleted " + str(chanAbove8kFile))
            
        arcpy.AddMessage("Calculating volume for chanAbove8k_" + inSite.lower() + "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(chanIntBndy, chanAbove8kFile, wsl_8k, chanTinCopyFullName, fltBinSize, True)
        # arcpy.AddMessage("Return value from volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed chanAbove8k_" + inSite.lower() + "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in chanAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of survey channel above 25k
        chanAbove25kFile = str(outRoot + "/vol_" + "chanAbove25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(chanAbove25kFile):
            arcpy.Delete_management(chanAbove25kFile)
            arcpy.AddMessage("Deleted " + str(chanAbove25kFile))
            
        arcpy.AddMessage("Calculating volume for chanAbove25kFile_" + inSite.lower() + "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(chanIntBndy, chanAbove25kFile, wsl_25k, chanTinCopyFullName, fltBinSize, True)
        # arcpy.AddMessage("Return value from volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed chanAbove25k_" + inSite.lower() + "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in chanAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")
        
        # Calculate Volume of eddy from Zmin to Zmax
        chanfromMinFile = str(outRoot + "/vol_" + "chanfrommin_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(chanfromMinFile):
            arcpy.Delete_management(chanfromMinFile)
            arcpy.AddMessage("Deleted " + str(chanfromMinFile))
            
        arcpy.AddMessage("Calculating volume for chanfromMin_" + inSite.lower() + "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(chanIntBndy, chanfromMinFile, wsl_8k, chanTinCopyFullName, fltBinSize, False)
        # arcpy.AddMessage("Return value from eddy above 8k volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed chanfrommin_" + inSite.lower() + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in chanfrommin_" + inSite.lower() + " volume calculation!")

        # New addition for calculation of channel from the minimum to 8K (Feb 11, 2014)
        # ==============================================================================
        if arcpy.Exists(chanfromMinFile):
            chanfromMinFileExists = True
            with open(chanfromMinFile, 'rb') as f100:      
                reader100 = csv.reader(f100, delimiter=',', quotechar='"')
                # Skip the Header
                row100 = next(reader100)
                # Get first row of data
                row100 = next(reader100)
                Area2DChanFromMin = row100[4]
                Area3DChanFromMin = row100[5]
                VolChanFromMin = row100[6]               
        else:
            VolChanFromMin = 0
            Area2DChanFromMin = 0
            Area3DChanFromMin = 0
            
        # ==============================================================================

        if arcpy.Exists(chanAbove8kFile):
            chanAbove8kFileExists = True
            with open(chanAbove8kFile, 'rb') as f10:      
                #reader1 = csv.reader(open(chanAbove8kFile, 'rb'), delimiter=',', quotechar='"')
                reader10 = csv.reader(f10, delimiter=',', quotechar='"')
                # Skip the Header
                row10 = next(reader10)
                # Get first row of data
                row10 = next(reader10)
                Area2D8k = row10[4]
                Area3D8k = row10[5]
                chvol8k = row10[6]
        else:
            chvol8k = 0
            Area2D8k = 0
            Area3D8k = 0
            
        # ==============================================================================    

        if arcpy.Exists(minChanAbove8kFile):
            minChanAbove8kFileExists = True
            with open(minChanAbove8kFile, 'rb') as f20:      
                #reader1 = csv.reader(open(chanAbove8kFile, 'rb'), delimiter=',', quotechar='"')
                reader20 = csv.reader(f20, delimiter=',', quotechar='"')
                f20row1 = next(reader20)
                f20row1 = next(reader20)
                #minArea2D8k = row1[4]
                #minArea3D8k = row1[5]
                minchanvol8k = f20row1[6]
        else:
            minchanvol8k = 0
            
        # ==============================================================================    

        # New addition for calculation of channel from the minimum to 8K (Feb 11, 2014)
        if arcpy.Exists(minChanFile):
            minChanFileExists = True
            with open(minChanFile, 'rb') as f1000:      
                #reader1 = csv.reader(open(chanAbove8kFile, 'rb'), delimiter=',', quotechar='"')
                reader1000 = csv.reader(f1000, delimiter=',', quotechar='"')
                f1000row1 = next(reader1000)
                f1000row1 = next(reader1000)
                #minArea2D8k = row1[4]
                #minArea3D8k = row1[5]
                minchanvol = f1000row1[6]
        else:
            minchanvol = 0

        # ==========================================================================================             
        # Here is were we calculate the Channel volume above 8K = ChannelAbove8K - MinChannelAbove8K
        # ==========================================================================================
        chanvol8k = float(chvol8k) - float(minchanvol8k)
        
        # New addition to write output the Volume of the Chan from the Minimum to 8K (Feb 11, 2014)
        # ========================================================================================================================
        binVol = str(outRoot + "/binvol_" + "chanminto8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(binVol):
            arcpy.Delete_management(binVol)
            arcpy.AddMessage("Deleted " + str(binVol))
        # headers = ['Site', 'Date', 'Area_2D', 'Area_3D', 'Volume']
        data = ['Site', 'Date', 'Plane_Height', 'Area_2D', 'Area_3D', 'Volume']
        #volHeaders = ['Dataset', 'Plane_Height', 'Reference', 'Z_Factor', 'Area_2D', 'Area_3D', 'Volume']
        
        # Write the Header Line
        with open(binVol, 'wb') as f400:
            writer400 = csv.writer(f400, delimiter=',')
            writer400.writerow(data)

        if chanfromMinFileExists == True:
            with open(chanfromMinFile) as f2:        
                num_survey_lines = sum(1 for line in f2)
            
        if minChanFileExists == True:
            #num_minsurf_lines = sum(1 for line in open(minChanFile))
            with open(minChanFile) as f3:        
                num_minsurf_lines = sum(1 for line in f3)
            
        arcpy.AddMessage("Number of Lines in Channel Survey = " + str(num_survey_lines) + ", Number of Lines in Channel MinSurface = " + str(num_minsurf_lines))
        
        survey_count = 0
        min_count = 0
        
        
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # MIN to 8K Volume Calcs
        if (chanfromMinFileExists == True):            
            if (minChanFileExists == True):                
                with open(chanfromMinFile, 'rb') as f41, open(minChanFile, 'rb') as f51, open(binVol, 'ab') as f81:
                    # arcpy.AddMessage("Got past open file statement!")
                    # Open csv readers
                    reader41 = csv.reader(f41, delimiter=',', quotechar='"')
                    reader51 = csv.reader(f51, delimiter=',', quotechar='"')
                    rownum_reader51 = 0
                    # Open the csv writer
                    writer81 = csv.writer(f81, delimiter=',')
                       
                    # Skip the header row of the Minimum Surface                   
                    minimumrow1 = next(reader51)
                    rownum_reader51 = rownum_reader51 + 1
          
                    # Get first data row of the Minimum Surface
                    minimumrow1 = next(reader51)
                    rownum_reader51 = rownum_reader51 + 1
                    
                    # Get first WSL of the Minimum Surface
                    minWSL = float((minimumrow1[1]).strip('"'))
                    
                    # Skip the header row of the Channel Survey
                    surveyChanrow1 = next(reader41)
                    
                    # Get first data row of the Channel Survey
                    surveyChanrow1 = next(reader41)
                    # Get first WSL of the Eddy Channel Surface
                    surveyChanWSL = float((surveyChanrow1[1]).strip('"'))
                    surveyChanArea2D = float((surveyChanrow1[4]).strip('"'))
                    surveyChanArea3D = float((surveyChanrow1[5]).strip('"'))
                    surveyChanVol = float((surveyChanrow1[6]).strip('"'))                   
                    
                    condition = True
                    while condition:
                        if (minWSL < surveyChanWSL):
                            condition = True
                            if (rownum_reader51 < num_minsurf_lines):
                                minimumrow1 = next(reader51)
                                rownum_reader51 = rownum_reader51 + 1                                 
                                # Get WSL of the Minimum Surface
                                minWSL = float((minimumrow1[1]).strip('"'))
                            else:
                                condition = False
                        else:
                            condition = False
                    
                    if (minWSL == surveyChanWSL):
                    
                        arcpy.AddMessage("============================================================================")
                        arcpy.AddMessage("Match!!! Minimum WSL = " + str(minWSL) + ", SurveyChannel WSL = " + str(surveyChanWSL))
                        arcpy.AddMessage("============================================================================")

                        #minChanArea2D = float((minimumrow1[4]).strip('"'))
                        #minChanArea3D = float((minimumrow1[5]).strip('"'))
                        minChanVol = float((minimumrow1[6]).strip('"'))
                        
                        #chanAbove8KWSL = float((chanAbove8Krow[1]).strip('"'))
                        #chanAbove8KArea2D = float((chanAbove8Krow[4]).strip('"'))
                        #chanAbove8KArea3D = float((chanAbove8Krow[5]).strip('"'))
                        #chanAbove8KVol = float((chanAbove8Krow[6]).strip('"'))

                        #minChanAbove8KWSL = float((minChanAbove8Krow[1]).strip('"'))
                        #minChanAbove8KArea2D = float((minChanAbove8Krow[4]).strip('"'))
                        #minChanAbove8KArea3D = float((minChanAbove8Krow[5]).strip('"'))
                        #minChanAbove8KVol = float((minChanAbove8Krow[6]).strip('"'))

                        volChanFromMinTo8K = (float(surveyChanVol)) - (float(minChanVol))
                        area2DChanFromMinto8K = float(surveyChanArea2D) # - float(chanAbove8KArea2D)
                        area3DChanFromMinto8K = float(surveyChanArea3D) # -  float(chanAbove8KArea3D)

                        outData = [str(inSite.lower()), str(siteFULLDATE), ("minto8K(" + str(surveyChanWSL) + ")"), str(area2DChanFromMinto8K),  str(area3DChanFromMinto8K), str(volChanFromMinTo8K)]
                        writer81.writerow(outData)

        # ==================================================================================================
        
        if arcpy.Exists(chanAbove25kFile):
            chanAbove25kFileExists = True
            with open(chanAbove25kFile, 'rb') as f11:  
                #reader2 = csv.reader(open(chanAbove25kFile, 'rb'), delimiter=',', quotechar='"')
                reader11 = csv.reader(f11, delimiter=',', quotechar='"')
                f11row2 = next(reader11)
                f11row2 = next(reader11)
                Area2D25k = f11row2[4]
                Area3D25k = f11row2[5]
                vol25k = f11row2[6]
        else:
            vol25k = 0
            Area2D25k = 0
            Area3D25k = 0

        # ======================================================================== 

        if arcpy.Exists(minChanAbove25kFile):
            minChanAbove25kFileExists = True
            with open(minChanAbove25kFile, 'rb') as f22:  
                #reader2 = csv.reader(open(chanAbove25kFile, 'rb'), delimiter=',', quotechar='"')
                reader22 = csv.reader(f22, delimiter=',', quotechar='"')
                f22row2 = next(reader22)
                f22row2 = next(reader22)
                #minArea2D25k = f22row2[4]
                #minArea3D25k = f22row2[5]
                minchanvol25k = f22row2[6]
        else:
            minchanvol25k = 0

        # Here is were we calculate the Channel volume above 25K = ChannelAbove25K - MinChannelAbove25K
        # =============================================================================================
        chanvol25k = float(vol25k) - float(minchanvol25k)
        # =============================================================================================
        #arcpy.AddMessage("Channel volume above 25k = " + str(chanvol25k))

        # Here is the final computation of 8K to 25K bin volume, and area
        # ===============================================================
        chanvol8kto25k = float(chanvol8k) - float(chanvol25k)
        chanarea2D8k = float(Area2D8k) - float(Area2D25k)
        chanarea3D8k = float(Area3D8k) - float(Area3D25k)
        # ===============================================================

        binVol = str(outRoot + "/binvol_" + "chan8kto25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(binVol):
            arcpy.Delete_management(binVol)
            arcpy.AddMessage("Deleted " + str(binVol))
        # headers = ['Site', 'Date', 'Area_2D', 'Area_3D', 'Volume']
        data = [['Site', 'Date', 'Plane_Height', 'Area_2D', 'Area_3D', 'Volume'], [str(inSite.lower()), str(siteFULLDATE), '8kto25k', str(chanarea2D8k), str(chanarea3D8k), str(chanvol8kto25k)]]
        #volHeaders = ['Dataset', 'Plane_Height', 'Reference', 'Z_Factor', 'Area_2D', 'Area_3D', 'Volume']
        
        with open(binVol, 'wb') as f3:
            writer1 = csv.writer(f3, delimiter=',')
            writer1.writerows(data)

        if arcpy.Exists(chanAbove8kFile):
            with open(chanAbove8kFile) as f5:
                num_survey_lines = sum(1 for line in f5)
                
        if arcpy.Exists(minChanAbove8kFile):
            with open(minChanAbove8kFile) as f6:
                num_minsurf_lines = sum(1 for line in f6)
                
        # arcpy.AddMessage("Number of Lines in Survey = " + str(num_survey_lines) + ", Number of Lines in MinSurface = " + str(num_minsurf_lines))
        survey_count = 0
        min_count = 0
        blnNoData = False

        if arcpy.Exists(minChanAbove8kFile):
            if arcpy.Exists(chanAbove8kFile):
                with open(minChanAbove8kFile, 'rb') as f4, open(chanAbove8kFile, 'rb') as f5, open(binVol, 'ab') as f6:
                    reader3 = csv.reader(f4, delimiter=',', quotechar='"')
                    reader4 = csv.reader(f5, delimiter=',', quotechar='"')
                    writer2 = csv.writer(f6, delimiter=',')
            
                    # Skip the header row of the Minimum Surface
                    minrow1 = next(reader3)
                    min_count = min_count + 1
                    # Get the first data row of the Minimum surface
                    minrow1 = next(reader3)
                    min_count = min_count + 1
            
                    # Skip the header row of the Survey Surface
                    surveyrow1 = next(reader4)
                    # Get the first data row of the Survey surface
                    survey_count = survey_count + 1
            
                    for surveyrow2 in reader4:
                        surveyWSL = float((surveyrow2[1]).strip('"'))
                        surveyArea2D = float((surveyrow2[4]).strip('"'))
                        surveyArea3D = float((surveyrow2[5]).strip('"'))
                        surveyVol = float((surveyrow2[6]).strip('"'))
                        # arcpy.AddMessage("In survey loop, NoData check in MinSurface = " + str(blnNoData))
                        # arcpy.AddMessage("In survey loop, survey_count = " + str(survey_count))
                
                        #Get the WSL of the minSurface for the current line                
                        minWSL = float((minrow1[1]).strip('"'))
                
                        if (minWSL == surveyWSL):
                            #arcpy.AddMessage("Min Surface WSL = " + str(minWSL) + ", Survey WSL = " + str(surveyWSL))
                            #minArea2D = float((minrow1[4]).strip('"'))
                            #minArea3D = float((minrow1[5]).strip('"'))
                            minVol = float((minrow1[6]).strip('"'))
                            # mindata = [float((minrow1[1]).strip('"')), float((minrow1[4]).strip('"')),float((minrow1[5]).strip('"')),float((minrow1[6]).strip('"'))]
                            # arcpy.AddMessage("Data Row = " + str(mindata))
                    
                            #output2D = surveyArea2D - minArea2D
                            output2D = surveyArea2D
                            #output3D = surveyArea3D - minArea3D
                            output3D = surveyArea3D                 
                            outputVol = surveyVol - minVol
                        
                            outData = [str(inSite.lower()), str(siteFULLDATE), "above" + str(surveyWSL), str(output2D),  str(output3D), str(outputVol)]
                            writer2.writerow(outData)
                            #arcpy.AddMessage("Output Data Row = " + str(outData))                        
                
                        if min_count < num_minsurf_lines:
                            blnNoData = False
                            minrow1 = next(reader3)
                            min_count = min_count + 1
                        else:
                            blnNoData = True
                            outData = [str(inSite.lower()), str(siteFULLDATE), "above" + str(surveyWSL), str(surveyArea2D),  str(surveyArea3D), str(surveyVol)]
                    
                        survey_count = survey_count + 1

                    #arcpy.AddMessage("On exit of survey loop, NoData check in MinSurface = " + str(blnNoData))
                    #arcpy.AddMessage("On exit of survey loop, survey_count = " + str(survey_count))
                    #arcpy.AddMessage("On exit of survey loop, min_count = " + str(min_count))
        else:
            if arcpy.Exists(chanAbove8kFile):
                with open(chanAbove8kFile, 'rb') as f5, open(binVol, 'ab') as f6:
                    writer2 = csv.writer(f6, delimiter=',')
                    reader4 = csv.reader(f5, delimiter=',', quotechar='"')
            
                    surveyrow1 = next(reader4)
                    #arcpy.AddMessage("Survey Row1 = " + str(surveyrow1))
                    survey_count = survey_count + 1

                    for surveyrow2 in reader4:
                        surveyWSL = float((surveyrow2[1]).strip('"'))
                        surveyArea2D = float((surveyrow2[4]).strip('"'))
                        surveyArea3D = float((surveyrow2[5]).strip('"'))
                        surveyVol = float((surveyrow2[6]).strip('"'))
                   
                        #output2D = surveyArea2D - minArea2D
                        output2D = surveyArea2D
                        #output3D = surveyArea3D - minArea3D
                        output3D = surveyArea3D                
                        #outputVol = surveyVol - minVol
                        outputVol = surveyVol
                        outData = [str(inSite.lower()), str(siteFULLDATE), "above" + str(surveyWSL), str(output2D),  str(output3D), str(outputVol)]
                        writer2.writerow(outData)
                        # arcpy.AddMessage("Output Data Row = " + str(outData))                        
                    
                        survey_count = survey_count + 1
                
    try:

        if (processEddyVol == True):
            # The AggBoundary has a Z_MAX, and Z_MIN field
            with arcpy.da.SearchCursor(eddyIntBndy, (field1,field2)) as cursor:
                for row in cursor:
                    ZmaxTIN = row[0]
                    #arcpy.AddMessage("TIN Z_MAX = " + str(ZmaxTIN))
                    ZminTIN = row[1]
                    #arcpy.AddMessage("TIN Z_MIN = " + str(ZminTIN))
                    #arcpy.AddMessage(" ")
                    if ((ZmaxTIN <= 0) or (ZminTIN <= 0)):
                        arcpy.AddMessage("Cannot get boundary values from " + eddyIntBndy + ". Skipping volume calculation!")
                        processEddyVol = False
                    else:
                        processEddyVol = True 
             
    except:
        print arcpy.GetMessages()

    if (processEddyVol == True):
        # Need to avoid putting output volume files in Geodatabases!
        # txtFile = str(outRoot + "/vol_" + "eddy" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        # arcpy.AddMessage("VOLUME Text File is " + txtFile)
        # arcpy.AddMessage("")

        #minEddyBndy = (outFGDBPath + "minEddyBndy")

        # Calculate Volume of minimum surface eddy 
        minEddyFile = str(outRoot + "/vol_" + "mineddy_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minEddyFile):
            arcpy.Delete_management(minEddyFile)
            arcpy.AddMessage("Deleted " + str(minEddyFile))

        arcpy.AddMessage("Calculating volume for mineddy_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(mineddyIntBndy, minEddyFile, wsl_8k, outMinTinEddyCopyFull, fltBinSize, False)
        # arcpy.AddMessage("Return value from minsurface eddy volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed mineddy_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in mineddy_" + inSite.lower() + "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of minimum surface eddy above 8k
        minEddyAbove8kFile = str(outRoot + "/vol_" + "mineddyAbove8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minEddyAbove8kFile):
            arcpy.Delete_management(minEddyAbove8kFile)
            arcpy.AddMessage("Deleted " + str(minEddyAbove8kFile))
            
        arcpy.AddMessage("Calculating volume for mineddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(mineddyIntBndy, minEddyAbove8kFile, wsl_8k, outMinTinEddyCopyFull, fltBinSize, True)
        # arcpy.AddMessage("Return value from minsurface eddy volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed mineddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in mineddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of minimum surface eddy above 25k
        minEddyAbove25kFile = str(outRoot + "/vol_" + "mineddyAbove25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(minEddyAbove25kFile):
            arcpy.Delete_management(minEddyAbove25kFile)
            arcpy.AddMessage("Deleted " + str(minEddyAbove25kFile))
            
        arcpy.AddMessage("Calculating volume for mineddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(mineddyIntBndy, minEddyAbove25kFile, wsl_25k, outMinTinEddyCopyFull, fltBinSize, True)
        #arcpy.AddMessage("Return value from minsurface eddy volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed mineddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in mineddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of survey surface eddy from Zmin to Zmax 
        eddySurfFile = str(outRoot + "/vol_" + "eddyfrommin_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(eddySurfFile):
            arcpy.Delete_management(eddySurfFile)
            arcpy.AddMessage("Deleted " + str(eddySurfFile))
            
        arcpy.AddMessage("Calculating volume for eddyfrommin_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(eddyIntBndy, eddySurfFile, wsl_8k, eddyCopyFullName, fltBinSize, False)
        # arcpy.AddMessage("Return value from eddy above 8k volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed eddyfrommin_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in eddyfrommin_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of survey surface eddy above 8k 
        eddyAbove8kFile = str(outRoot + "/vol_" + "eddyAbove8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(eddyAbove8kFile):
            arcpy.Delete_management(eddyAbove8kFile)
            arcpy.AddMessage("Deleted " + str(eddyAbove8kFile))
            
        arcpy.AddMessage("Calculating volume for eddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(eddyIntBndy, eddyAbove8kFile, wsl_8k, eddyCopyFullName, fltBinSize, True)
        # arcpy.AddMessage("Return value from eddy above 8k volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed eddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in eddyAbove8k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # Calculate Volume of survey surface eddy above 25k 
        eddyAbove25kFile = str(outRoot + "/vol_" + "eddyAbove25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(eddyAbove25kFile):
            arcpy.Delete_management(eddyAbove25kFile)
            arcpy.AddMessage("Deleted " + str(eddyAbove25kFile))
            
        arcpy.AddMessage("Calculating volume for eddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + "...")
        volCalcOK = calcVolume(eddyIntBndy, eddyAbove25kFile, wsl_25k, eddyCopyFullName, fltBinSize, True)
        # arcpy.AddMessage("Return value from eddy above 25k volume calculation =  " + str(volCalcOK))
        if volCalcOK == True:
            arcpy.AddMessage("Completed eddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation")
            arcpy.AddMessage(" ")
        else:
            arcpy.AddMessage("Error in eddyAbove25k_" + inSite.lower() +  "_" + siteFULLDATE + " volume calculation!")

        # ======================================================================================
        # New addition for calculation of eddy from min to 8K (Feb 11, 2014)
        # ======================================================================================
        if arcpy.Exists(eddySurfFile):
            eddySurfFileExists = True
            with open(eddySurfFile, 'rb') as f200:      
                reader200 = csv.reader(f200, delimiter=',', quotechar='"')
                # Skip the Header
                row200 = next(reader200)
                # Get first row of data
                row200 = next(reader200)
                Area2DEddyFromMin = row200[4]
                Area3DEddyFromMin = row200[5]
                VolEddyFromMin = row200[6]               
        else:
            VolEddyFromMin = 0
            Area2DEddyFromMin = 0
            Area3DEddyFromMin = 0
            eddySurfFileExists = False
            
        # ======================================================================================
        
        if arcpy.Exists(eddyAbove8kFile):
            eddyAbove8kFileExists = True
            with open(eddyAbove8kFile, 'rb') as f1:
                reader1 = csv.reader(f1, delimiter=',', quotechar='"')
                # Skip the Header Row
                row1 = next(reader1)
                # Get the First Data Row
                row1 = next(reader1)
                Area2D8k = row1[4]
                Area3D8k = row1[5]
                vol8k = row1[6]
        else:
            vol8k = 0
            Area2D8k = 0
            Area3D8k = 0
            eddyAbove8kFileExists = False

        # ======================================================================================

        if arcpy.Exists(minEddyAbove8kFile):
            minEddyAbove8kFileExists = True
            with open(minEddyAbove8kFile, 'rb') as f11:
                reader11 = csv.reader(f11, delimiter=',', quotechar='"')
                # Skip the Header Row
                f11row1 = next(reader11)
                # Get the First Data Row
                f11row1 = next(reader11)
                #minArea2D8k = f11row1[4]
                #minArea3D8k = f11row1[5]
                mineddyVol8k = f11row1[6]
        else:
            mineddyVol8k = 0
            minEddyAbove8kFileExists = False

        #eddyarea2D8k = float(Area2D8k) - float(minArea2D8k)
        #eddyarea3D8k = float(Area3D8k) - float(minArea3D8k)

        # ======================================================================================
        # Added code below for the calculation of channel vol from minimum to 8K (Feb 11, 2014)
        # ======================================================================================
        
        if arcpy.Exists(minEddyFile):
            minEddyFileExists = True
            with open(minEddyFile, 'rb') as f111:
                reader111 = csv.reader(f111, delimiter=',', quotechar='"')
                # Skip the Header Row
                f111row1 = next(reader111)
                # Get the First Data Row
                f111row1 = next(reader111)
                #minArea2D8k = f11row1[4]
                #minArea3D8k = f11row1[5]
                mineddyVol = f111row1[6]
        else:
            mineddyVol = 0
            minEddyFileExists = False

        # ======================================================================================
        # Calculate the eddy volume above 8K
        # ============================================
        eddyvol8k = float(vol8k) - float(mineddyVol8k)
        # ============================================

        # New addition for calculation of VolEddyFromMin to 8K (Feb 11, 2014)
        # =======================================================================================================================
        # volEddyFromMinTo8K = (val(eddySurfFile) - val(eddyAbove8kFile)) - (val(minEddyFile) - val(minEddyAbove8kFile))
        #volEddyFromMinTo8K = (float(VolEddyFromMin) - float(vol8k)) - (float(mineddyVol) - float(mineddyVol8k))
        #area2DEddyFromMinto8K = float(Area2DEddyFromMin) - float(Area2D8k)
        #area3DEddyFromMinto8K = float(Area3DEddyFromMin) -  float(Area3D8k)
        # ========================================================================================================================

        # New addition to write output the Volume of the Eddy from the Minimum to 8K (Feb 11, 2014)
        # ========================================================================================================================
        binVol = str(outRoot + "/binvol_" + "eddyminto8k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(binVol):
            arcpy.Delete_management(binVol)
            arcpy.AddMessage("Deleted " + str(binVol))
        # headers = ['Site', 'Date', 'Area_2D', 'Area_3D', 'Volume']
        data = ['Site', 'Date', 'Plane_Height', 'Area_2D', 'Area_3D', 'Volume']
        #volHeaders = ['Dataset', 'Plane_Height', 'Reference', 'Z_Factor', 'Area_2D', 'Area_3D', 'Volume']
        
        # Write the Header Line
        with open(binVol, 'ab') as f300:
            writer300 = csv.writer(f300, delimiter=',')
            writer300.writerow(data)

        if eddySurfFileExists == True:
            with open(eddySurfFile) as f:        
                num_survey_lines = sum(1 for line in f)
            
        if minEddyFileExists == True:
            #num_minsurf_lines = sum(1 for line in open(minEddyFile))
            with open(minEddyFile) as f1:             
                num_minsurf_lines = sum(1 for line in f1)
            
        arcpy.AddMessage("Number of Lines in Survey = " + str(num_survey_lines) + ", Number of Lines in MinSurface = " + str(num_minsurf_lines))
        
        survey_count = 0
        min_count = 0
        blnNoData = False

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # MIN to 8K Volume Calcs
        if eddySurfFileExists == True:
            if minEddyFileExists == True:
                if eddyAbove8kFileExists == True:
                    if minEddyAbove8kFileExists == True:
                        minEddyAbove8kFileExists
                        with open(eddySurfFile, 'rb') as f40, open(minEddyFile, 'rb') as f50, open(eddyAbove8kFile, 'rb') as f60, open(minEddyAbove8kFile, 'rb') as f70, open(binVol, 'ab') as f80:

                            # Open File readers
                            reader40 = csv.reader(f40, delimiter=',', quotechar='"')
                            reader50 = csv.reader(f50, delimiter=',', quotechar='"')
                            reader60 = csv.reader(f60, delimiter=',', quotechar='"')
                            reader70 = csv.reader(f70, delimiter=',', quotechar='"')
                    
                            # Open File writer
                            writer80 = csv.writer(f80, delimiter=',')

                            # Skip the header row of the eddyAbove8KFile
                            eddyAbove8Krow = next(reader60)
                            # Get first data row of the eddyAbove8KFile
                            eddyAbove8Krow = next(reader60)

                            # Skip the header row of the minEddyAbove8KFile
                            minEddyAbove8Krow = next(reader70)
                            # Get first data row of the minEddyAbove8KFile
                            minEddyAbove8Krow = next(reader70)
                            eddyAbove8KWSL = float((eddyAbove8Krow[1]).strip('"'))
                       
                            # Skip the header row of the Minimum Surface
                            minimumrow1 = next(reader50)
                            
                            # Get first data row of the Minimum Surface
                            minimumrow1 = next(reader50)
                            min_count = min_count + 1
                        
                            # Get first WSL of the Minimum Surface
                            minWSL = float((minimumrow1[1]).strip('"'))
                            
                            # Skip the header row of the Eddy Survey
                            surveyEddyrow1 = next(reader40)
                            # Get first data row of the Eddy Survey
                            surveyEddyrow1 = next(reader40)
                            # Get first WSL of the Eddy Survey Surface
                            surveyEddyWSL = float((surveyEddyrow1[1]).strip('"'))
                            surveyEddyArea2D = float((surveyEddyrow1[4]).strip('"'))
                            surveyEddyArea3D = float((surveyEddyrow1[5]).strip('"'))
                            surveyEddyVol = float((surveyEddyrow1[6]).strip('"'))
                            
                            condition = True
                            while condition:
                                if (minWSL < surveyEddyWSL):
                                    condition = True
                                    if min_count < num_minsurf_lines:
                                        minimumrow1 = next(reader50)
                                        min_count = min_count + 1
                                                       
                                        #Get first WSL of the Minimum Surface
                                        minWSL = float((minimumrow1[1]).strip('"'))
                                                                       
                                    else:
                                        condition = False
                                else:
                                    condition = False
                                
                            
                            if (minWSL == surveyEddyWSL):

                                arcpy.AddMessage("============================================================================")
                                arcpy.AddMessage("Match!!! Minimum WSL = " + str(minWSL) + ", SurveyEddy WSL = " + str(surveyEddyWSL))
                                arcpy.AddMessage("============================================================================")

                                #minEddyArea2D = float((minimumrow1[4]).strip('"'))
                                #minEddyArea3D = float((minimumrow1[5]).strip('"'))
                                minEddyVol = float((minimumrow1[6]).strip('"'))
                        
                                eddyAbove8KWSL = float((eddyAbove8Krow[1]).strip('"'))
                                eddyAbove8KArea2D = float((eddyAbove8Krow[4]).strip('"'))
                                eddyAbove8KArea3D = float((eddyAbove8Krow[5]).strip('"'))
                                eddyAbove8KVol = float((eddyAbove8Krow[6]).strip('"'))

                                minEddyAbove8KWSL = float((minEddyAbove8Krow[1]).strip('"'))
                                minEddyAbove8KArea2D = float((minEddyAbove8Krow[4]).strip('"'))
                                minEddyAbove8KArea3D = float((minEddyAbove8Krow[5]).strip('"'))
                                minEddyAbove8KVol = float((minEddyAbove8Krow[6]).strip('"'))

                                volEddyFromMinTo8K = (float(surveyEddyVol) - float(eddyAbove8KVol)) - (float(minEddyVol) - float(minEddyAbove8KVol))
                                arcpy.AddMessage("SurveyEddyVol = " + str(surveyEddyVol))
                                arcpy.AddMessage("EddyAbove8KVol = " + str(eddyAbove8KVol))
                                arcpy.AddMessage("minEddyVol = " + str(minEddyVol))
                                arcpy.AddMessage("minEddyAbove8KVol = " + str(minEddyAbove8KVol))
                                area2DEddyFromMinto8K = float(surveyEddyArea2D) - float(eddyAbove8KArea2D)
                                area3DEddyFromMinto8K = float(surveyEddyArea3D) -  float(eddyAbove8KArea3D)

                                outData = [str(inSite.lower()), str(siteFULLDATE), ("minto8K(" + str(surveyEddyWSL) + ")"), str(area2DEddyFromMinto8K),  str(area3DEddyFromMinto8K), str(volEddyFromMinTo8K)]
                                writer80.writerow(outData)

                            # Get next data row of the Eddy Survey, if not EOF
                            #if (survey_count < num_survey_lines):
                            #    surveyEddyrow1 = next(reader40)
                            # Get next WSL of the Eddy Survey Surface
                            #    surveyEddyWSL = float((surveyEddyrow1[1]).strip('"'))
                            #    survey_count = survey_count + 1
                            #else:
                            #    condition = False
                        
                            # Get next data row of the Minimum Surface, if not EOF
                            #if (min_count < num_minsurf_lines):
                            #    minimumrow1 = next(reader50)
                            # Get next WSL of the Minimum Surface
                            #    minWSL = float((minimumrow1[1]).strip('"'))
                            #    min_count = min_count + 1
                            #else:
                            #    minWSL = float(0)
                            #    minEddyVol = float(0)
                            #    condition = False
                        
                            #else:
                            #    condition = False
                        
        # ==================================================================================================
                 
        if arcpy.Exists(eddyAbove25kFile):
            with open(eddyAbove25kFile, 'rb') as f2:  
                #reader2 = csv.reader(open(eddyAbove25kFile, 'rb'), delimiter=',', quotechar='"')
                reader2 = csv.reader(f2, delimiter=',', quotechar='"')
                # Skip the Header Row
                row2 = next(reader2)
                # Get first Data Row
                row2 = next(reader2)
                Area2D25k = row2[4]
                Area3D25k = row2[5]
                vol25k = row2[6]
        else:
            vol25k = 0
            Area2D25k = 0
            Area3D25k = 0

        # ========================================================================

        if arcpy.Exists(minEddyAbove25kFile):
            with open(minEddyAbove25kFile, 'rb') as f22:  
                #reader2 = csv.reader(open(eddyAbove25kFile, 'rb'), delimiter=',', quotechar='"')
                reader22 = csv.reader(f22, delimiter=',', quotechar='"')
                # Skip the Header Row
                f22row2 = next(reader22)
                # Get the first row of data
                f22row2 = next(reader22)
                #minArea2D25k = f22row2[4]
                #minArea3D25k = f22row2[5]
                minvol25k = f22row2[6]
        else:
            minvol25k = 0

        # Calculate the Eddy Volume and Area above 25K (Feb 11, 2014)
        # ===========================================================
        eddyvol25k = float(vol25k) - float(minvol25k)
        eddyArea2DAbove25K = float(Area2D25k)
        eddyArea3DAbove25K = float(Area3D25k)
        # ===========================================================

        # Output the Eddy Above 25K Area and Volume (Feb 11, 2014)
        binVol = str(outRoot + "/binvol_" + "eddyabove25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(binVol):
            arcpy.Delete_management(binVol)
            arcpy.AddMessage("Deleted " + str(binVol))
        # headers = ['Site', 'Date', 'Area_2D', 'Area_3D', 'Volume']
        data = [['Site', 'Date', 'Plane_Height', 'Area_2D', 'Area_3D', 'Volume'], [str(inSite.lower()), str(siteFULLDATE), 'above25k', str(eddyArea2DAbove25K), str(eddyArea3DAbove25K), str(eddyvol25k)]]
        #volHeaders = ['Dataset', 'Plane_Height', 'Reference', 'Z_Factor', 'Area_2D', 'Area_3D', 'Volume']
        
        with open(binVol, 'wb') as f30:
            writer30 = csv.writer(f30, delimiter=',')
            writer30.writerows(data)
        
        # Here is where we calculate 8K to 25K bin volume
        # ================================================
        finalVol8Kto25K = eddyvol8k - eddyvol25k      
        area2D8kto25k = float(Area2D8k) - float(Area2D25k)
        area3D8kto25k = float(Area3D8k) - float(Area3D25k)
        # ================================================      

        # Output the Eddy 8K to 25K Area and Volume
        binVol = str(outRoot + "/binvol_" + "eddy8kto25k_" + inSite.lower() + "_" + siteFULLDATE + ".txt")
        if arcpy.Exists(binVol):
            arcpy.Delete_management(binVol)
            arcpy.AddMessage("Deleted " + str(binVol))
        # headers = ['Site', 'Date', 'Area_2D', 'Area_3D', 'Volume']
        data = [['Site', 'Date', 'Plane_Height', 'Area_2D', 'Area_3D', 'Volume'], [str(inSite.lower()), str(siteFULLDATE), '8kto25k', str(area2D8kto25k), str(area3D8kto25k), str(finalVol8Kto25K)]]
        #volHeaders = ['Dataset', 'Plane_Height', 'Reference', 'Z_Factor', 'Area_2D', 'Area_3D', 'Volume']
        
        with open(binVol, 'wb') as f3:
            writer1 = csv.writer(f3, delimiter=',')
            writer1.writerows(data)

        #sys.exit()
        if arcpy.Exists(eddyAbove8kFile):
            num_survey_lines = sum(1 for line in open(eddyAbove8kFile))
        if arcpy.Exists(minEddyAbove8kFile):
            num_minsurf_lines = sum(1 for line in open(minEddyAbove8kFile))
        # arcpy.AddMessage("Number of Lines in Survey = " + str(num_survey_lines) + ", Number of Lines in MinSurface = " + str(num_minsurf_lines))
        survey_count = 0
        min_count = 0
        blnNoData = False

        if arcpy.Exists(minEddyAbove8kFile):
            if arcpy.Exists(eddyAbove8kFile):
                with open(minEddyAbove8kFile, 'rb') as f4, open(eddyAbove8kFile, 'rb') as f5, open(binVol, 'ab') as f6:
                    writer2 = csv.writer(f6, delimiter=',')
                    reader3 = csv.reader(f4, delimiter=',', quotechar='"')
                    reader4 = csv.reader(f5, delimiter=',', quotechar='"')
            
                    # Skip the header row of the Minimum Surface
                    minrow1 = next(reader3)
                    #arcpy.AddMessage("MinSurface HeaderRow = " + str(minrow1))
                    min_count = min_count + 1
                    minrow1 = next(reader3)
                    min_count = min_count + 1
            
                    surveyrow1 = next(reader4)
                    #arcpy.AddMessage("Survey Row1 = " + str(surveyrow1))
                    survey_count = survey_count + 1
            
                    for surveyrow2 in reader4:
                        surveyWSL = float((surveyrow2[1]).strip('"'))
                        surveyArea2D = float((surveyrow2[4]).strip('"'))
                        surveyArea3D = float((surveyrow2[5]).strip('"'))
                        surveyVol = float((surveyrow2[6]).strip('"'))
                        # arcpy.AddMessage("In survey loop, NoData check in MinSurface = " + str(blnNoData))
                        # arcpy.AddMessage("In survey loop, survey_count = " + str(survey_count))
                
                        #Get the WSL of the minSurface for the current line                
                        minWSL = float((minrow1[1]).strip('"'))
                
                        if (minWSL == surveyWSL):
                            #arcpy.AddMessage("Min Surface WSL = " + str(minWSL) + ", Survey WSL = " + str(surveyWSL))
                            # minArea2D = float((minrow1[4]).strip('"'))
                            # minArea3D = float((minrow1[5]).strip('"'))
                            minVol = float((minrow1[6]).strip('"'))
                            # mindata = [float((minrow1[1]).strip('"')), float((minrow1[4]).strip('"')),float((minrow1[5]).strip('"')),float((minrow1[6]).strip('"'))]
                            # arcpy.AddMessage("Data Row = " + str(mindata))
                            #result = numpy.array(mindata).astype('float')
                            #numpy.savetxt(numpyTXT, result, delimiter=',')
                            #===================================================================
                            #output2D = surveyArea2D - minArea2D
                            output2D = surveyArea2D
                            #output3D = surveyArea3D - minArea3D
                            output3D = surveyArea3D
                            outputVol = surveyVol - minVol
                            #===================================================================
                            outData = [str(inSite.lower()), str(siteFULLDATE), ("above" + str(surveyWSL)), str(output2D),  str(output3D), str(outputVol)]
                            writer2.writerow(outData)
                            #arcpy.AddMessage("Output Data Row = " + str(outData))                        
                
                        if min_count < num_minsurf_lines:
                            blnNoData = False
                            minrow1 = next(reader3)
                            min_count = min_count + 1
                        else:
                            blnNoData = True
                            outData = [str(inSite.lower()), str(siteFULLDATE), ("above" + str(surveyWSL)), str(surveyArea2D),  str(surveyArea3D), str(surveyVol)]
                    
                        survey_count = survey_count + 1

                    #arcpy.AddMessage("On exit of survey loop, NoData check in MinSurface = " + str(blnNoData))
                    #arcpy.AddMessage("On exit of survey loop, survey_count = " + str(survey_count))
                    #arcpy.AddMessage("On exit of survey loop, min_count = " + str(min_count))
        else:
            if arcpy.Exists(eddyAbove8kFile):
                with open(eddyAbove8kFile, 'rb') as f5, open(binVol, 'ab') as f6:
                    writer2 = csv.writer(f6, delimiter=',')
                    reader4 = csv.reader(f5, delimiter=',', quotechar='"')
                
                    surveyrow1 = next(reader4)
                    #arcpy.AddMessage("Survey Row1 = " + str(surveyrow1))
                    survey_count = survey_count + 1

                    for surveyrow2 in reader4:
                        surveyWSL = float((surveyrow2[1]).strip('"'))
                        surveyArea2D = float((surveyrow2[4]).strip('"'))
                        surveyArea3D = float((surveyrow2[5]).strip('"'))
                        surveyVol = float((surveyrow2[6]).strip('"'))
                
                        #minVol = float((minrow1[6]).strip('"'))
                        #output2D = surveyArea2D - minArea2D
                        output2D = surveyArea2D
                        #output3D = surveyArea3D - minArea3D
                        output3D = surveyArea3D
                        #outputVol = surveyVol - minVol
                        outputVol = surveyVol
                        outData = [str(inSite.lower()), str(siteFULLDATE), ("above" + str(surveyWSL)), str(output2D),  str(output3D), str(outputVol)]
                        writer2.writerow(outData)
                        #arcpy.AddMessage("Output Data Row = " + str(outData))
                        survey_count = survey_count + 1

    # loop counter
    count = count + 1
    arcpy.AddMessage(str(count)+ " Text Files Processed")
    
#for outTIN in outTINList:
#    arcpy.AddMessage("TIN Name = " + str(outTIN))

#outTINList.sort(key=alphanum_key)
#arcpy.AddMessage("Sorted TIN List")

#for outTIN in outTINList:
#    arcpy.AddMessage("Sorted TIN Name = " + str(outTIN))

if blnDeletePointFC == "true":
    arcpy.AddMessage("Delete PointFC Checkbox is true")
    for ptfc in outPointFCList:
        # arcpy.AddMessage("File Name is!" + str(ptfc))
        if arcpy.Exists(ptfc):
            arcpy.Delete_management(ptfc)
            arcpy.AddMessage("Deleted " + str(ptfc))
# else:
# arcpy.AddMessage("Checkbox is false")

if blnDeleteAggBoundary == "true":
    arcpy.AddMessage("Delete AggBoundary Checkbox is true")
    for bndfc in aggPointFCList:
        # arcpy.AddMessage("File Name is!" + str(bndfc))
        if arcpy.Exists(bndfc):
            arcpy.Delete_management(bndfc)
            arcpy.AddMessage("Deleted " + str(bndfc))
      
# else:
# arcpy.AddMessage("Checkbox is false")

# Check in the ArcGIS Spatial Analyst extension license
arcpy.CheckInExtension("Spatial")

# Check in the ArcGIS 3D Analyst extension
arcpy.CheckInExtension("3D")

print(arcpy.GetMessages())
