# North_Arrow_ex

### Examples of sandbar process for Philip and Matt

Compiled sandbar survey data for Marble and Grand Canyons, Grand Canyon National Park, Arizona

### Objectives:

* Compile sandbar surveys from 1990 to 2015 at 43 selected long-term monitoring sites.
* Create synthetic minimum and maximum surfaces to calculate sand volume and area above minimum (baseline) surface, and calculate sand volume and area above minimum surface as percent of maximum potential fill.
* Develop output text files at 0.10 m elevation intervals (bins) above lowest survey point containing area and volume above the base of each bin for both survey surface, and minimum surface clipped to same areal extent as survey surface for each date. These files are being used for interactive online database purposes, where area and volume above the minimum surface can be displayed for custom discharge ranges.
* Develop output text files for intervals corresponding to elevations below 227 m3/s, between 227 m3/s and 708 m3/s, and above 708 m3/s. These files are being used for Northern Arizona University Sandbar Studies/Grand Canyon Monitoring and Research Center sandbars report.
* Compile output text files for NAU/GCMRC reporting, and plot individual sites and overall data for individual reaches in Marble and Grand Canyons for all three discharge intervals (<227 m3/s, 227 m3/s – 708 m3/s, and >708 m3/s). 
Methods:
* Interpolate 1-m spaced coregistered text files from survey TINs.
* Use Union tool in ESRI ArcGIS for all surveys surfaces from 1990-1992, and 1995-2011 (2014 in some cases where there were major geomorphic changes at certain sites). Run the Union function twice, using the minimum point values for one raster, and maximum point values for the other. 
* Run Python script using file folder of interpolated 1-m survey surfaces, common computational boundary, minimum surface, stage discharge relationships at each site, water surface elevation of interest at each site (default is elevation corresponding to 227 m3/s), and aggregation boundary tolerance of 2.5 meters. The script loops though the list of text files, creates point feature classes, aggregates a boundary around the points, intersects the aggregate boundary with the computational boundary, parses out the date of the survey, and converts the raster of the minimum surface into a point feature class, using the same boundary for each date to create a minimum surface corresponding to each survey date. It then converts the point feature classes into TINs, using the aggregated boundary to delineate the TIN area. The script then runs the Surface Volume tool on each survey and corresponding minimum surface, using the 227 m3/s water surface elevation as an indexing feature. The script indexes down in elevation at even 0.10 m intervals, and rounds down the lowest elevation in each surface to an even factor of the 227 m3/s water surface elevation (e.g., if the 227 m3/s elevation is 920.87, and the minimum point in the file is 903.42, it will use 903.37 as the reference elevation to begin area and volume calculations above). It then iterates solutions for each 0.10 m elevation value upwards, until the data run out. These provide the “vol_eddyfromminmin” and “vol_mineddy” files (see attached; note that there are files for “chan” rather than “eddy” where applicable). These are the files we have been using for the database.
* Use the output files mentioned above, and index the minimum surface until we find the same elevation value corresponding to the first elevation in the survey surface. This then calculates area and volume for the intervals below 227 m3/s, 227 m3/s – 708 m3/s, and above 708 m3/s, outputting a new file for each survey and each interval (see the attached “binvol” files; note that only the first row of data below the header is used). These files are used for the NAU/GCMRC reporting. 
* Using a Python compiler script, we compile the data, compare them to a look up table containing survey dates, trip dates, sites, and uncertainty, and use VBA to put values into a spreadsheet. Then we use R to create plots of the data for each site. This method is being rearranged by Dan Hammill, who I believe is using Pandas to do a more elegant method.

## Setting up in Arc

```
Program Variable Name       Display Name              Data type                       Type      Direction ObtainedFrom    Filter
arcpy.GetParameterAsText(0) outFGDB                   Workspace or Feature Dataset    Required  Input
arcpy.GetParameterAsText(1) inFolder                  Folder                          Required  Input
arcpy.GetParameterAsText(2) Minimum Surface(GRID)     Raster Dataset      Required  Input
arcpy.GetParameterAsText(3) Channel Boundary        Feature Class     Required  Input
arcpy.GetParameterAsText(4) Eddy Boundary       Feature Class     Required  Input
arcpy.GetParameterAsText(5) StageLUTable          Table       Required  Input
arcpy.GetParameterAsText(6) Aggregation Distance  Double              Required  Input
arcpy.GetParameterAsText(7) Stage               Field       Required  Input     StageLUTable    Field(double)
arcpy.GetParameterAsText(8) Site                String        Required  Input                     Value List
arcpy.GetParameterAsText(9) Bin Size                Double        Required  Input                     Value List
arcpy.GetParameterAsText(10) Delete Points?   Boolean       Required  Input
arcpy.GetParameterAsText(11) Delete AggBoundary?  Boolean       Required  Input
```
