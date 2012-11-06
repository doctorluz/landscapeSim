import numpy
import scipy
import random
import pylab
from scipy import ndimage
from scipy.ndimage import (label, find_objects)

def CreatePatch(max_area, min_area, aspect_ratio):
  # Calculate the dimension of field using area and aspect_ratio
  # Generate a rectangle with the dimensions calculated
  area = min_area + int( random.random()*(max_area - min_area) ) 
  height = numpy.sqrt(area/aspect_ratio)
  rectangle = numpy.zeros((int(height),int(aspect_ratio*height)),dtype="int")
  return rectangle


def GeometricFeature(Landcover_arr, Distance_arr, min_area = 40,max_area = 400,aspect_ratio = 1.8,agri_area_limit = 0.3, next_patch_orientation_probability = 0.5):
  """
  Generates geometrical features like fields
  Args:
    Landcover_arr: 2-D array having landcover values assigned to each pixel( 2-D array of ints)
    min_area: minimum area of an individual field (int)
    max_area: maximum area of an individual field (int)
    aspect_ratio: Ratio of lenght to breadth (float)
    agri_area_limit: percentage of grid area to be covered by fields (float b/w 0-1)
                     fraction of area to be covered by agricultural area 
  Results:
    Display_fields :2-D array having fields
  """
  (x_len, y_len) = Landcover_arr.shape
  # Allocate and initialize Suitabilty map 
  Suitability = numpy.zeros( Landcover_arr.shape, dtype = "float")
  for i in range(0,x_len):
    for j in range(0,y_len):
      if Landcover_arr[i][j] == 0 or Distance_arr[i][j] == 0: # Ignore
        Suitability[i][j] = 0
      elif Landcover_arr[i][j] == 25:  # Deciduous woodland
        Suitability[i][j] = 0.6
      elif Landcover_arr[i][j] == 50:  # Coniferous woodland
        Suitability[i][j] = 0.55
      elif Landcover_arr[i][j] == 75:  # Agriculture including pasture
        Suitability[i][j] = 0.98
      elif Landcover_arr[i][j] == 100: # Semi-natural grassland
        Suitability[i][j] = 0.9
      elif Landcover_arr[i][j] == 125: # Bog and swamp
        Suitability[i][j] = 0.5
      elif Landcover_arr[i][j] == 150: # Heath
        Suitability[i][j] = 0.75
      elif Landcover_arr[i][j] == 175: # Montane habitat
        Suitability[i][j] = 0.2
      elif Landcover_arr[i][j] == 200: # Rock and quarry
        Suitability[i][j] = 0.3
      elif Landcover_arr[i][j] == 225: # Urban
        Suitability[i][j] = 0.8
    
  # Agri_arr will have it's pixels labelled by Field ID and boundary
  Agri_arr = numpy.zeros((x_len,y_len),dtype = "int")
  # Display_fields is used for the purpose of display of fields, boundaries
  Display_fields = numpy.zeros((x_len,y_len),dtype = "uint8")
  # Initially ID is assigned value zero,the first field will receive ID = 1
  ID = 1 

  # Threshold the suitabilty map
  List = []
  for i in range(0,x_len):
    for j in range(0,y_len):
      List.append((Suitability[i][j],i,j))
  List.sort(reverse = True)
  threshold = List[int(0.7*len(List))][0]

  # list_index denote the suitability list element in consideration
  list_index = 0
  # Covered_area denote the total area covered by agriculture during program execution
  Covered_area = 0
  # limit1 denote the constraint on the area to be covered by agriculture
  limit1 = int(agri_area_limit * (x_len - 1)*(y_len - 1))

  # generate a random angle between 0 to 90
  angle_2 = int(random.random()*180)

  while Covered_area < limit1 or list_index > len(List) - min_area:
    ID = ID + 1 # keep increasing the ID before every field placement
    rectangle = CreatePatch(max_area, min_area, aspect_ratio)
    # Assign ID to rectangle
    rectangle[:,:] = ID
    # generate a random angle between 0 to 180
    angle_1 = angle_2
    angle_2 = int(random.random()*180)
    # Introducing next patch orientation probability
    if random.random() > next_patch_orientation_probability:
      angle = angle_2
    else:
      angle = angle_1
      angle_2 = angle_1

    patch = ndimage.interpolation.rotate(rectangle,angle,axes=(1,0),reshape=True,\
                 output=None, order=3, mode='constant', cval=0.0, prefilter=True)
    # get the approximate centroid of the patch (rotated field) 
    (x,y) = (int(( patch.shape[0] )/2 ),int((patch.shape[1])/2))
    # get the next best pixel for placing field onto map
    (p,q) = (List[list_index][1],List[list_index][2])
    Area = 0 # needed to keep track of area of the field
    Buffer = [] # needed in case we have to discard the field

    for i in range(0,patch.shape[0]):
      for j in range(0,patch.shape[1]):
        (a,b) = (p-x+i,q-y+j) # get the absolute location in the map 
        """Check weather the pixel lie within the boundary of the grid"""
        if ( (a >= 1) and (b >= 1) and ( a <= x_len - 2) and (b <= x_len-2) ):
          # check condition for overlap ,inter-field distance, suitability
          if patch[i][j] > 0 and Agri_arr[a][b] == 0 and Suitability[a][b] >= threshold:
            Area = Area + 1
            Buffer.append((a,b))

    if Area >= min_area:
      # If area of field, after removing unsuitable pixels, is greater than min_area
      # then place the field onto map
      Covered_area = Covered_area + Area # increase total covered area
      for i in range(0,len(Buffer)):
        Agri_arr[Buffer[i]] = ID
        Display_fields[Buffer[i]] = 255
        List.remove((Suitability[Buffer[i]],Buffer[i][0],Buffer[i][1]))

      for i in range(0,len(Buffer)):
        # mark the boundary of the field in the map
        (a,b) = Buffer[i]
        if (Agri_arr[a][b] == ID):
          if Agri_arr[a-1][b-1] == 0:
            Agri_arr[a-1][b-1] = 1 #inter-patch strip indicator
            Display_fields[a-1][b-1] = 150
            List.remove((Suitability[a-1][b-1],a-1,b-1))
            Covered_area = Covered_area + 1
          if Agri_arr[a-1][b] == 0: 
            Agri_arr[a-1][b] = 1 #inter-patch strip indicator
            Display_fields[a-1][b] = 150
            List.remove((Suitability[a-1][b],a-1,b))
            Covered_area = Covered_area + 1
          if Agri_arr[a-1][b+1] == 0:
            Agri_arr[a-1][b+1] = 1 #inter-patch strip indicator
            Display_fields[a-1][b+1] = 150
            List.remove((Suitability[a-1][b+1],a-1,b+1))
            Covered_area = Covered_area + 1
          if Agri_arr[a][b-1] == 0:
            Agri_arr[a][b-1] = 1 #inter-patch strip indicator
            Display_fields[a][b-1] = 150
            List.remove((Suitability[a][b-1],a,b-1))
            Covered_area = Covered_area + 1
          if Agri_arr[a][b+1] == 0:
            Agri_arr[a][b+1] = 1 #inter-patch strip indicator
            Display_fields[a][b+1] = 150
            List.remove((Suitability[a][b+1],a,b+1))
            Covered_area = Covered_area + 1
          if Agri_arr[a+1][b-1] == 0:
            Agri_arr[a+1][b-1] = 1 #inter-patch strip indicator
            Display_fields[a+1][b-1] = 150
            List.remove((Suitability[a+1][b-1],a+1,b-1))
            Covered_area = Covered_area + 1
          if Agri_arr[a+1][b] == 0:
            Agri_arr[a+1][b] = 1 #inter-patch strip indicator
            Display_fields[a+1][b] = 150
            List.remove((Suitability[a+1][b],a+1,b))
            Covered_area = Covered_area + 1
          if Agri_arr[a+1][b+1] == 0:
            Agri_arr[a+1][b+1] = 1 #inter-patch strip indicator
            Display_fields[a+1][b+1] = 150
            List.remove((Suitability[a+1][b+1],a+1,b+1))
            Covered_area = Covered_area + 1
    else:
      list_index = list_index + 1
   

  s= [[1,1,1],
      [1,1,1],
      [1,1,1]]
  mask = [Agri_arr == 1]
  Agri_arr[mask] = 0
  label_arr, no_of_patches =  label(Agri_arr, structure = s)
  print "no of patches", no_of_patches

  return (Agri_arr, label_arr)
