import arcpy
import csv
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tool"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        # Get the values from the CSV file
        scriptPath = os.path.dirname(os.path.realpath(__file__))
        StageDischargePath = os.path.join(scriptPath, 'LookupTables', 'StageDischarge.csv')
        SandbarSites = os.path.join(scriptPath, 'LookupTables', 'SandbarSites.csv')

        headers = []
        with open(StageDischargePath, 'r') as f:
            reader = csv.reader(f)
            headers = reader.next()    

        sites = []
        with open(StageDischargePath, 'r') as f:
            records = csv.DictReader(f)
            for row in records:
                if row['Site']:
                    sites.append(row['Site'])         

        # First parameter
        param0 = arcpy.Parameter(
            displayName="outFGDB",
            name="outFGDB",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="inFolder",
            name="inFolder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Minimum Surface(GRID)",
            name="minSurface",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Channel Boundary",
            name="chanBnd",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="Eddy Boundary",
            name="eddyBnd",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input")

        param5 = arcpy.Parameter(
            displayName="Aggregation Distance",
            name="aggDist",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input")

        param6 = arcpy.Parameter(
            displayName="Stage",
            name="inStage",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        param7 = arcpy.Parameter(
            displayName="Site",
            name="inSite",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # param6.filters[0].list = headers

        param8 = arcpy.Parameter(
            displayName="Bin Size",
            name="binSize",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param9 = arcpy.Parameter(
            displayName="Delete Points?",
            name="blnDeletePointFC",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        param10 = arcpy.Parameter(
            displayName="Delete AggBoundary?",
            name="blnDeleteAggBoundary",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")

        params = [param0, param1, param2, param4, param5, param6, param7, param8, param9, param10]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        return
