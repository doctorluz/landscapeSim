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
        
        H = [float(x) for x in params['H'].split(',')]
        
        H_wt = [float(x) for x in params['H_wt'].split(',')]

        seed = [float(x) for x in params['seed'].split(',')]

        elev_range = [float(x) for x in params['elev_range'].split(',')] 

##        Three_DplotDEM = stream["Three_DplotDEM"]

##        elev_filename = stream["training_data_elev"]
##        landcover_filename = stream["training_data_landcover"]
##        river_filename = stream["training_data_river"]

##        next_patch_orientation_probability = stream['next_patch_orientation_probability']
        gradient_values = [params['north'], params['north_west'], params['west'], params['south_west'], params['south'], params['south_east'], params['east'], params['north_east'], params['center']]

        self.logger.fine ("Running simulation with following parameters")
        self.logger.fine ("Counter %d" % params['counter'])
        self.logger.fine ("H %s" % H)
        self.logger.fine ("H_wt %s" % H_wt)
        self.logger.fine ("seed %s" % seed)
        self.logger.fine ("elev_range %s" % elev_range)
        self.logger.fine ("river_drop %s" % params['river_drop'])
        self.logger.fine ("max_level %s" % params['max_level'])
        self.logger.fine ("DEMcreator_option %s" % params['DEMcreator_option'])
        self.logger.fine ("Gradient values %s" % gradient_values)
        self.logger.fine ("response %s" % params['response'])
        self.logger.fine ("min_area %d" % params['min_area'])
        self.logger.fine ("max_area %d" % params['max_area'])
        self.logger.fine ("aspect_ratio %s" % params['aspect_ratio'])
        self.logger.fine ("agri_area_limit %s" % params['agri_area_limit'])
     
        #Generate DEM using FM2D/SS algorithm by calling DEM_creator(args...) function")
        time0 = time.time()
        self.logger.fine("Creating DEMs")
        l_DEM_Result = Hydro_Network.DEM_creator(H, H_wt, seed, elev_range, params['max_level'], gradient_values, params['DEMcreator_option'])
        #Write result to Output file
        l_file_name = "%sOriginal_DEM" % (params['outputDir'])
        self.logger.fine(l_file_name)
        pylab.imsave(l_file_name, l_DEM_Result[0])
        for i in range(0,len(l_DEM_Result[1])):
            l_file_name = "%s%s" % (params['outputDir'],l_DEM_Result[2][i])#TODO(include parameter in filename)l_DEM_Result[3][i][0],l_DEM_Result[3][i][1])
            self.logger.fine(l_file_name)
            pylab.imsave(l_file_name, l_DEM_Result[1][i])

        l_DEM = l_DEM_Result[0]
        for iteration in range(0,params['counter']):
            #Remove sink using 3x3 window by calling Single_Cell_PitRemove(originalDEM, no_of_itr)
            l_DEM = Hydro_Network.Single_Cell_PitRemove(l_DEM, no_of_itr = 6)
            (l_x_len,l_y_len) = l_DEM.shape
            l_max_posn = ndimage.maximum_position(l_DEM)
            l_Flow_dirn_arr = numpy.zeros((l_x_len,l_y_len,2), dtype="int" )
            #l_Flow_arr will be used for the purpose of catchment extraction
            l_Flow_arr = numpy.zeros((l_x_len, l_y_len), dtype = "uint8")
            l_River_arr = numpy.ones((l_x_len, l_y_len), dtype = "int")
            l_pit_list = [] #Not required now
            ( l_pit_list, l_Flow_dirn_arr, l_DEM ) = Hydro_Network.Get_Flow_Dirn_using_9x9_window(l_DEM, l_Flow_dirn_arr, l_pit_list)
            # call Flow_Dirn_3x3(l_DEM, l_Flow_arr , l_pit_list) for the purpose of catchment extraction
            l_pit_list = [] #Required for catchment extraction
            ( l_pit_list, l_Flow_arr ) = Hydro_Network.Flow_Dirn_3x3(l_DEM, l_Flow_arr , l_pit_list) 
            #Catchment extraction, calling CatchmentExtraction(l_pit_list, l_DEM_arr, l_max_posn)
            (l_DEM, l_Found_arr, l_Catchment_boundary_arr) = Hydro_Network.CatchmentExtraction(l_pit_list, l_DEM, l_Flow_arr, l_max_posn)
            #Write result to Output file
            l_file_name = "%s/Catchment%s" % (params['outputDir'], iteration+1)
            pylab.imsave(l_file_name, l_Found_arr)
            l_file_name = "%s/Catchment_Boundary%s" % (params['outputDir'], iteration+1)
            pylab.imsave(l_file_name, l_Catchment_boundary_arr)        
            #Assignnig flow dirnection again after catchment extraction and Depression filling
            ( l_pit_list, l_Flow_dirn_arr, l_DEM ) = Hydro_Network.Get_Flow_Dirn_using_9x9_window(l_DEM, l_Flow_dirn_arr , l_pit_list)
            #Calculate flow accumulation by Calling Flow_accumulation(l_Flow_dirn_arr ,l_River_arr , l_DEM)
            l_River_arr = Hydro_Network.Flow_accumulation(l_Flow_dirn_arr ,l_River_arr, l_DEM)
            #Write result to Output file
            l_file_name = "%s/River%s" % (params['outputDir'],iteration+1)
            pylab.imsave(l_file_name, l_River_arr)
            #"Eroding the DEM based on Distance form River ...Calling Erosion(l_River_arr,l_DEM_arr,river_drop)
            (l_DEM, l_Distance_arr) = Hydro_Network.Erosion(l_River_arr, l_DEM, params['river_drop'])  
            #Write result to Output file
            l_file_name = "%s/ErodedDEM%s" % (params['outputDir'], iteration+1)
            pylab.imsave(l_file_name, l_DEM)
            l_file_name = "%s/RiverDistance%s" % (params['outputDir'], iteration+1)
            pylab.imsave(l_file_name, l_Distance_arr)
        
        if params['Three_DplotDEM'] == 'y' or params['Three_DplotDEM'] == 'Y':
            surface_plot.plot(l_DEM)
        time2 = time.time()
        self.logger.fine ("Time taken in Erosion modeling: %3f seconds" % (time2 - time1))

        if (params['response'] == 'y') or (params['response'] == 'Y'):
            DecisionTree.DecisionTree(params['outputDir'], params['elev_filename'], params['landcover_filename'], params['river_filename'])
            time3 = time.time()
            self.logger.fine ("Time taken to generate decision tree is %3f" % (time3 - time2))

    ##    time3 = time.time()
    ##    l_Veg_arr = VegetationClassify.VegetationClassify(l_DEM, l_River_arr)
    ##    l_file_name = "%sLandcover" % (outputDir)
    ##    pylab.imsave(l_file_name, l_Veg_arr)
    ##    time4 = time.time()
    ##    self.logger.fine ("Time taken to assign landcover is %3f seconds" % (time4 - time3))
    ##    (l_agri, l_labelled_fields) =Geometry.GeometricFeature(l_Veg_arr,l_Distance_arr, params['min_area'], params['max_area'], params['aspect_ratio'], params['agri_area_limit'], params['next_patch_orientation_probability'])
    ##    l_file_name = "%slabelled_fields_display" % params['outputDir']
    ##    pylab.imsave(l_file_name, l_labelled_fields)
    ##    l_file_name = "%sAgriculture" % params['outputDir']
    ##    pylab.imsave(l_file_name, l_agri)
    ##    time5 = time.time()
    ##    self.logger.fine ("Time taken to generate Geometric Features is %3f seconds" % (time5 - time4))    

 
