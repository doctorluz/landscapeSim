#!/usr/bin/env python
import pylab
import numpy
from scipy import ndimage 
import time
import yaml
import Hydro_Network
import DecisionTree
#import VegetationClassify 
#import Geometry
#import surface_plot

import basemodel

class Model(basemodel.BaseModel):
    def execute(self, runparams):
        self.logger.fine("I'm in model.py!!")

        # get parameters qualified by input and output file paths
        params = runparams['parameters']

        # This is how to run R code directly if you plan to:
        # however, in this example, R is called from python using rpy.
        # self.run_r_code("example.R", runparams)
        """
        It imports all necessary python modules required for landscape simulation.
        It then performs the following:
        1. Gets all the parameters required for simulation from parameter.yaml file. 
        2. calls DEM_creator() --> for generating DEM grid
        3. Iteratively operate on DEM grid and do the following
           3.1 Remove single cell pits by calling Single_Cell_PitRemove()
           3.2 Get flow dirn using 9x9 window by calling Get_Flow_Dirn_using_9x9_window()  
           3.3 Get flow dirn using 3x3 window by calling Flow_Dirn_3x3() for catchment extraction
           3.4 Extract the catchment and do depression filling using CatchmentExtraction()
           3.5 Again get flow direction using Get_Flow_Dirn_using_9x9_window() after depression filling
           3.6 Perform flow accumulation by calling Flow_accumulation() 
           3.7 Do the erosion by calling Erosion()
        4. Generate a Decision tree for land_cover allocation by calling DecisionTree()
        5. Assign the vegetation class to DEM by calling VegetationClassify()
        6. Generate some agricultural field by calling GeometricFeature()
        """
        time1 = time.time()
        # Get the parameters for parameter.yaml file

        H = [float(x) for x in params['H'].split(', ')]
        
        H_wt = [float(x) for x in params['H_wt'].split(', ')]

        seed = [float(x) for x in params['seed'].split(', ')]

##        elev_range = stream['elev_range']
##        river_drop = stream['river_drop']
##        max_level = stream['max_level']
##        DEMcreator_option = stream['DEMcreator_option']
##        north = stream['north']
##        north_west = stream['north_west']
##        west = stream['west']
##        south_west = stream['south_west']
##        south = stream['south']
##        south_east = stream['south_east']
##        east = stream['east']
##        north_east = stream['north_east']
##        center = stream['center']
##        Three_DplotDEM = stream["Three_DplotDEM"]
##        output_dir = stream['output_dir']
##        response = stream['response']
##        elev_filename = stream["training_data_elev"]
##        landcover_filename = stream["training_data_landcover"]
##        river_filename = stream["training_data_river"]
##        counter = stream['counter']
##        min_area = stream['min_area']
##        max_area = stream['max_area']
##        aspect_ratio = stream['aspect_ratio']
##        agri_area_limit = stream['agri_area_limit']
##        next_patch_orientation_probability = stream['next_patch_orientation_probability']
        gradient_values = [params['north'], params['north_west'], params['west'], params['south_west'], params['south'], params['south_east'], params['east'], params['north_east'], params['center']]
##        yaml_file.close() #close the yaml parameter file
        print ("Running simulation with follwing parameters")
        print ("Counter %d" % params['counter'])
        print ("H %s" % H)
        print ("H_wt %s" % H_wt)
        print ("seed %s" % seed)
        print ("elev_range %s" % elev_range)
        print ("river_drop %s" % params['river_drop'])
        print ("max_level %s" % params['max_level'])
        print ("DEMcreator_option %s" % params['DEMcreator_option'])
        print ("Gradient values %s" % gradient_values)
        print ("response %s" % params['response'])
        print ("min_area %d" % params['min_area'])
        print ("max_area %d" % params['max_area'])
        print ("aspect_ratio %s" % params['aspect_ratio'])
        print ("agri_area_limit %s" % params['agri_area_limit'])
     
        #Generate DEM using FM2D/SS algorithm by calling DEM_creator(args...) function")
        time0 = time.time()
        self.logger.fine("Creating DEMs")
        DEM_Result = Hydro_Network.DEM_creator(H, H_wt, seed, elev_range, params['max_level'], gradient_values, params['DEMcreator_option'])
        #Write result to Output file
        file_name = "%sOriginal_DEM" % (params['outputDir'])
        self.logger.fine(file_name)
        pylab.imsave(file_name, DEM_Result[0])
        for i in range(0,len(DEM_Result[1])):
            file_name = "%s%s" % (params['outputDir'],DEM_Result[2][i])#TODO(include parameter in filename)DEM_Result[3][i][0],DEM_Result[3][i][1])
            self.logger.fine(file_name)
            pylab.imsave(file_name, DEM_Result[1][i])

        DEM = DEM_Result[0]
        for iteration in range(0,counter):
            #Remove sink using 3x3 window by calling Single_Cell_PitRemove(originalDEM, no_of_itr)
            DEM = Hydro_Network.Single_Cell_PitRemove(DEM, no_of_itr = 6)
            (x_len,y_len) = DEM.shape
            max_posn = ndimage.maximum_position(DEM)
            Flow_dirn_arr = numpy.zeros((x_len,y_len,2), dtype="int" )
            #Flow_arr will be used for the purpose of catchment extraction
            Flow_arr = numpy.zeros((x_len, y_len), dtype = "uint8")
            River_arr = numpy.ones((x_len, y_len), dtype = "int")
            pit_list = [] #Not required now
            ( pit_list, Flow_dirn_arr, DEM ) = Hydro_Network.Get_Flow_Dirn_using_9x9_window(DEM, Flow_dirn_arr, pit_list)
            # call Flow_Dirn_3x3(DEM, Flow_arr , pit_list) for the purpose of catchment extraction
            pit_list = [] #Required for catchment extraction
            ( pit_list, Flow_arr ) = Hydro_Network.Flow_Dirn_3x3(DEM, Flow_arr , pit_list) 
            #Catchment extraction, calling CatchmentExtraction(pit_list, DEM_arr, max_posn)
            (DEM, Found_arr, Catchment_boundary_arr) = Hydro_Network.CatchmentExtraction(pit_list, DEM, Flow_arr, max_posn)
            #Write result to Output file
            file_name = "%s/Catchment%s" % (params['outputDir'], iteration+1)
            pylab.imsave(file_name, Found_arr)
            file_name = "%s/Catchment_Boundary%s" % (params['outputDir'], iteration+1)
            pylab.imsave(file_name, Catchment_boundary_arr)        
            #Assignnig flow dirnection again after catchment extraction and Depression filling
            ( pit_list, Flow_dirn_arr, DEM ) = Hydro_Network.Get_Flow_Dirn_using_9x9_window(DEM, Flow_dirn_arr , pit_list)
            #Calculate flow accumulation by Calling Flow_accumulation(Flow_dirn_arr ,River_arr , DEM)
            River_arr = Hydro_Network.Flow_accumulation(Flow_dirn_arr ,River_arr, DEM)
            #Write result to Output file
            file_name = "%s/River%s" % (params['outputDir'],iteration+1)
            pylab.imsave(file_name, River_arr)
            #"Eroding the DEM based on Distance form River ...Calling Erosion(River_arr,DEM_arr,river_drop)
            (DEM, Distance_arr) = Hydro_Network.Erosion(River_arr, DEM, river_drop)  
            #Write result to Output file
            file_name = "%s/ErodedDEM%s" % (params['outputDir'], iteration+1)
            pylab.imsave(file_name, DEM)
            file_name = "%s/RiverDistance%s" % (params['outputDir'], iteration+1)
            pylab.imsave(file_name, Distance_arr)
        
        if Three_DplotDEM == 'y' or Three_DplotDEM == 'Y':
            surface_plot.plot(DEM)
        time2 = time.time()
        print ("Time taken in Erosion modeling", time2 - time1,"seconds")

        if (response == 'y') or (response == 'Y'):
            DecisionTree.DecisionTree(params['outputDir'], elev_filename, landcover_filename, river_filename)
            time3 = time.time()
            print "Time taken to generate decision tree is " , (time3 - time2) ,"seconds"

    ##    time3 = time.time()
    ##    Veg_arr = VegetationClassify.VegetationClassify(DEM, River_arr)
    ##    file_name = "%s/Landcover" % (output_dir)
    ##    pylab.imsave(file_name, Veg_arr)
    ##    time4 = time.time()
    ##    print "Time taken to assign landcover is " , (time4 - time3),"seconds"
    ##    (agri, labelled_fields) =Geometry.GeometricFeature(Veg_arr,Distance_arr, min_area, max_area, aspect_ratio, agri_area_limit, next_patch_orientation_probability)
    ##    file_name = "%s/labelled_fields_display" % (output_dir)
    ##    pylab.imsave(file_name, labelled_fields)
    ##    file_name = "%s/Agriculture" % (output_dir)
    ##    pylab.imsave(file_name, agri)
    ##    time5 = time.time()
    ##    print "Time taken to generate Geometric Features is " ,(time5 - time4) ,"seconds"    

 
