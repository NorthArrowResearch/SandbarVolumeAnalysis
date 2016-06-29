# create.py
# Create, write, or both to folder, personal geodatabase or feature dataset
# Tim Andrews
# April 28, 2010
import sys, string, os, arcgisscripting, glob, re

# Note used 9.3!
gp = arcgisscripting.create(9.3)

# Allow for the overwriting of file geodatabases, if they previously exist
gp.OverWriteOutput = 1

# Turn on history logging so that a history log file is written
gp.LogHistory = True

# Check out any necessary licenses
gp.CheckOutExtension("spatial")
gp.CheckOutExtension("3D")

# Load required toolboxes...
gp.AddToolbox("C:/ArcGIS/ArcToolbox/Toolboxes/Spatial Analyst Tools.tbx")
gp.AddToolbox("C:/ArcGIS/ArcToolbox/Toolboxes/Conversion Tools.tbx")
gp.AddToolbox("C:/ArcGIS/ArcToolbox/Toolboxes/Data Management Tools.tbx")
gp.AddToolbox("C:/ArcGIS/ArcToolbox/Toolboxes/3D Analyst Tools.tbx")
gp.AddToolbox("C:/ArcGIS/ArcToolbox/Toolboxes/Analysis Tools.tbx")

# Local variables...
inFolder = ""
outFolder = ""
inSide = ""
outGrid = ""
inSep = "."
inHeader = "Point"
inFooter = "END"
InCellSize = int(1.00)
InField = "Z"
count = int(0)

# GUI variables
inFolder = gp.GetParameterAsText(0)
outFGDB = gp.GetParameterAsText(1)
inSide = gp.GetParameterAsText(2)

# Some functions don't work without setting a workspace!
# gp.Workspace = inFolder.replace("\\","/")

# if outFGDB == "":
#  outFGDB = inFolder
theFiles = glob.glob(inFolder+"/*.txt")

for i in theFiles:
  inTXTfull = str(i).replace("\\","/")  
  inTXT = os.path.split(inTXTfull)[1]
  inPath = os.path.split(inTXTfull)[0]
  gp.AddMessage("Input Path is: " + inPath)
  out_fgdb = str(outFGDB).replace("\\","/")
  gp.AddMessage("Output FGDB is: " + out_fgdb)  
  outPath = out_fgdb + "/"
  gp.AddMessage("")     
  gp.AddMessage("Input Text File is: " + inTXTfull)
  noextName = str(inTXT[:-4])
  result = re.split("\_", noextName)
  # gp.AddMessage("Split on all underscores result is " + str(result))
  result2 = re.split("\_", noextName, 1)
  # gp.AddMessage("Split on first underscore result is " + str(result2))
  siteNUM = result[0]
  # gp.AddMessage("Site Number is " + siteNUM)
  if len(siteNUM) == 1:
    siteNUM = "00" + siteNUM
  elif len(siteNUM) == 2:
    siteNUM = "0" + siteNUM
  
  siteDATE = result[1]
  # gp.AddMessage("Date is " + siteDATE)
  siteNOTE = result[2]
  # gp.AddMessage("Note is " + siteNOTE)

  outRasterName = "SE" + "_" + siteDATE
  lenRasterName = len(outRasterName)
  if lenRasterName > 13:
    gp.AddMessage("Output Raster Name is too long: " + outRasterName)
  
  # out_fgdb = "C:/TEMP/ED/123L/coregistered/123L.gdb"
  # out_fgdb = (outPath + "/" + siteNUM + inSide + ".gdb")
  outRasterNameFull = (outPath + outRasterName)
  # gp.AddMessage("Full Output Grid Name: " + outRasterNameFull)

  shortFCName = ("pt" + siteNUM + inSide + "_" + siteDATE)
  # gp.AddMessage("Short Output FC Name: " + shortFCName)

  outFCNameFull = (outPath + shortFCName)
  # gp.AddMessage("Full Output FC Name: " + outFCNameFull)
  # outFCNameFull = (out_fgdb + "/" + shortFCName)
  # gp.AddMessage("Full Output FC Name: " + outFCNameFull)

  # Get comma delimited x,y,z file contents into a list
  fileHandle = open(inTXTfull, "r")
  inFileLinesList = fileHandle.readlines()
  fileHandle.close()

  # create empty output list
  outFileLinesList = []

  # set file header as first line of output list
  outFileLinesList.append(inHeader + '\n')

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

  # set footer as last line of output list
  outFileLinesList.append(inFooter)
  outFilename = inTXTfull

  # compare in / out lists to see if need to write file
  if inFileLinesList != outFileLinesList:
    fileHandle = open(outFilename,"w")
    fileHandle.writelines(outFileLinesList)
    fileHandle.close()
  
  # Use the projection file as input to the SpatialReference class
  prjFile = r"C:\arcgis\Coordinate Systems\Projected Coordinate Systems\State Plane\NAD 1983\NAD 1983 StatePlane Arizona Central FIPS 0202.prj"
  spatialRef = gp.CreateObject("spatialreference")
  spatialRef.CreateFromFile(prjFile)  

  # Process: Create Feature Class...
  gp.CreateFeatureclass_management(out_fgdb, shortFCName, "POINT", "", "DISABLED", "DISABLED", "", "", "0", "0", "0")

  # Create the features from the XYZ text file
  gp.CreateFeaturesFromTextFile(inTXTfull, inSep, outFCNameFull, spatialRef)
   
  # AddField_management (in_table, field_name, field_type, {field_precision}, {field_scale}, {field_length},
  # {field_alias}, {field_is_nullable}, {field_is_required}, {field_domain})
  gp.AddField_management(outFCNameFull, "X", "DOUBLE", "20", "20", "", "", "NULLABLE", "NON_REQUIRED", "")
  gp.AddField_management(outFCNameFull, "Y", "DOUBLE", "20", "20", "", "", "NULLABLE", "NON_REQUIRED", "")
  gp.AddField_management(outFCNameFull, "Z", "DOUBLE", "20", "20", "", "", "NULLABLE", "NON_REQUIRED", "") 

  # Find the name of the shape field using Describe.
  strShapeFieldName = gp.Describe(outFCNameFull).ShapeFieldName
  
  # Create an update cursor to index through all the features in the feature class table.
  objRowList = gp.UpdateCursor(outFCNameFull)
  objRow = objRowList.Next()

  try:
    while objRow:
      # Create a geometry object from the Shape field.
      objGeometry = objRow.GetValue(strShapeFieldName)

      # Assuming this feature class is a point shapefile, access the point XYZ
      # "parts" and copy the values into the X/Y/Z fields.
      objPart = objGeometry.GetPart(0)
      objRow.SetValue("X", objPart.X) 
      objRow.SetValue("Y", objPart.Y)
      objRow.SetValue("Z", objPart.Z)     

      # save the changes to the attribute table
      objRowList.UpdateRow(objRow)
      
      # release objects from memory
      del objRow, objPart, objGeometry
      objRow = objRowList.Next()
        
  except:
    print "error in script"
    print gp.GetMessages()
    sys.exit()

  gp.AddMessage("Created XYZ Point Feature Class: " + outFCNameFull)

  try:
    
    # Process: FeatureToRaster_conversion
    gp.FeatureToRaster_conversion(outFCNameFull, InField, outRasterNameFull, InCellSize)
    gp.AddMessage("Created XYZ GRID: " + outRasterNameFull)

    # Local variables...
    outGRIDcm = (out_fgdb + "/" + "cm" + outRasterName)
    outGRIDint = (out_fgdb + "/" + "i" + outRasterName)
    tmpPOLY = (out_fgdb + "/" + "tmpPOLY")    
    outPOLY = (out_fgdb + "/" + "py" + siteNUM + inSide + "_" + siteDATE + "_bnd")
    outBUFR = (out_fgdb + "/" + "py" + siteNUM + inSide + "_" + siteDATE + "_bndbuf")
    tmpTIN = (out_fgdb + "/" + "tn" + siteNUM + inSide + "_" + siteDATE + "_tin")
    
    # Process: Times 100 to get cm grid
    gp.Times_sa(outRasterNameFull, 100, outGRIDcm)
    gp.AddMessage("Created XYZ Float cm GRID: " + outGRIDcm)

    # Process: Int...
    gp.Int_sa(outGRIDcm, outGRIDint)
    gp.AddMessage("Created XYZ Integer cm GRID: " + outGRIDint)    

    # Process: Raster to Polygon...
    gp.RasterToPolygon_conversion(outGRIDint, tmpPOLY, "NO_SIMPLIFY", "Value")
    gp.AddMessage("Created Polygons from XYZ Integer GRID: " + tmpPOLY) 

    # Process: Dissolve...
    gp.Dissolve_management(tmpPOLY, outPOLY, "", "", "MULTI_PART", "DISSOLVE_LINES")
    gp.AddMessage("Created Boundary Polygon from polygon dissolve operation: " + outPOLY)

    # Process: Buffer...
    gp.Buffer_analysis(outPOLY, outBUFR, "1 Meters", "FULL", "ROUND", "NONE", "")
    gp.AddMessage("Created Buffered Boundary Polygon (1 meter): " + outBUFR)

    logfilename = (inPath + "log.dat")
    fileHandle = open(logfilename,'a')
    
    # create empty output list
    outLogList = []

    # Add process lines    
    outLogList.append("Input: XYZ Point Text File = " + inTXTfull + "\n")    
    outLogList.append("Output: XYZ Point Feature Class = " + outFCNameFull + "\n")
    outLogList.append("Output: XYZ Raster = " + outRasterNameFull + "\n")
    outLogList.append("Parameters: XYZ Points to Raster: CellSize = " + str(InCellSize) + "\n")
    outLogList.append("Output: XYZ Float cm Raster = " + outGRIDcm + "\n")    
    outLogList.append("Output: XYZ Integer Raster = " + outGRIDint + "\n")
    outLogList.append("Output: Temporary XYZ Integer Raster to Polygons Undissolved = " + tmpPOLY + "\n")
    outLogList.append("Parameters: Integer Raster to Polygon operation: " + outGRIDint + ", " + tmpPOLY + ", NO_SIMPLIFY, Value" + "\n")    
    outLogList.append("Output: Dissolved Boundary Polygon = " + outPOLY + "\n")   
    outLogList.append("Parameters: Dissolve Polygons operation: " + tmpPOLY + ", " + outPOLY + ", "", "", MULTI_PART, DISSOLVE_LINES" + "\n")
    outLogList.append("Output: Boundary Polygon buffered 1 meter = " + outBUFR + "\n")
    outLogList.append("Parameters: Buffer Boundary Polygon operation: " + outPOLY + ", " + outBUFR + ", " + "1 Meters, FULL, ROUND, NONE, """ + "\n")    
    outLogList.append(" " + '\n')
    fileHandle.writelines(outLogList)
    fileHandle.close()
    gp.AddMessage("Log file written to: " + logfilename)
    
    count = count + 1
    gp.AddMessage(str(count)+ " Text Files Processed")
    
  except:
    print "error in script"
    print gp.GetMessages()
    sys.exit()

try:
  # Local variables
  inputs = ""
  gp.Workspace = out_fgdb
  max_grid = (out_fgdb + "/" + "max_grid")
  min_grid = (out_fgdb + "/" + "min_grid")  
  GRIDlist = gp.ListRasters("SE*", "GRID")
  gp.AddMessage("")
  gp.AddMessage("GRIDlist is: " + str(GRIDlist))
  
  # Get all the GRIDS in the list and separate by  a semi-colon
  for raster in GRIDlist:
    inputs += raster + ";"
  
  # Echo out the input list
  gp.AddMessage("")
  gp.AddMessage("Inputs List = " + inputs)
  
  # Process: Cell Statistics...
  # Create the MAXIMUM GRID
  # gp.CellStatistics_sa(inputs, max_grid, "MAXIMUM")
  # gp.AddMessage("Created Maximum GRID = " + str(max_grid))

  # Process: MosaicToNew
  gp.MosaicToNewRaster_management(inputs, (str(out_fgdb) + "/"), "max_grid", spatialRef, "32_BIT_SIGNED", "1","1", "MAXIMUM", "#")
  gp.AddMessage("Created Maximum GRID = " + str(max_grid))

  # Process: Cell Statistics...
  # Create the MINIMUM GRID
  # gp.CellStatistics_sa(inputs, min_grid, "MINIMUM")
  # gp.AddMessage("Created Minimum GRID = " + str(min_grid))

  # Process: MosaicToNew
  gp.MosaicToNewRaster_management(inputs, (str(out_fgdb) + "/"), "min_grid", spatialRef, "32_BIT_SIGNED", "1","1", "MINIMUM", "#")
  gp.AddMessage("Created Minimum GRID = " + str(min_grid))
    
except:
  # If an error occurred while running a tool, then print the messages.
  print gp.GetMessages()

# try:
  # Feature class to hold exported MIN GRID points
  # ptMINgrid = (out_fgdb + "/" + "ptMINgrid")

  # Process: RasterToPoint_conversion
  # gp.RasterToPoint_conversion(min_grid, ptMINgrid)
  # gp.AddMessage("Created Points from Minimum GRID = " + str(ptMINgrid))

  # Feature class to hold exported MIN GRID points
  # ptMAXgrid = (out_fgdb + "/" + "ptMAXgrid")

  # Process: RasterToPoint_conversion
  # gp.RasterToPoint_conversion(max_grid, ptMAXgrid)
  # gp.AddMessage("Created Points from Maximum GRID = " + str(ptMAXgrid))

# except:
  # Print error message if an error occurs
  # print gp.GetMessages()

# try:
  # Process: Erase...
  # ptMINsurvey = (out_fgdb + "/" + "ptMINsurvey")
  # gp.Erase_analysis(ptMINgrid, outBUFR, ptMINsurvey, "")
  # gp.AddMessage("Erased boundary of Minimum GRID = " + str(ptMINsurvey))  

  # Process: Create TIN...
  # gp.CreateTin_3d(tmpTIN, spPROJ)
  
# except:
  # If an error occurred while running a tool, then print the messages.
  # print gp.GetMessages()
