import numpy as np
from base_shape import base_shape

class CreateScanShapeSquare(base_shape):
    '''
    generates xy coordinates for SEM and related image scanning - square scan
    '''
    def __init__(
            self, 
            no_points_per_line, 
            no_lines, 
            Vmax_x = 10.0, 
            Vmax_y = 10.0, 
            offset_x = 0.0, 
            offset_y = 0.0, 
            scale_x = 100.0, 
            scale_y = 100.0,
            scan_direction_increasing = True, 
            scan_direction_x = True
            ):
       
        super(CreateScanShapeSquare, self).__init__(no_points_per_line, no_lines, Vmax_x, Vmax_y, offset_x, offset_y, scale_x, scale_y)

        # Scan direction increasing goes visually from L to R if X / T to B if Y   
        self.scan_direction_x = scan_direction_x  
        self.scan_direction_increasing = scan_direction_increasing   

        # create scan shape - defined in the base class
        self.scan_pattern()

        
    def make_pattern(self):

        # Generates the x, y pattern for the square scan
        # x, y structure:
        # x = [-10,  -10,  -10,   -9, -9,  -9, ...] <- those are voltages going to the scanning coil
        # y = [-3.3,   0, +3.3, -3.3,  0, +3.3, ...]
        #
        # Scan_tuple defines the indices where the pixels are on the grid, important for Lissajous
        # scan_tuple_x = [0, 0, 0, 1, 1, 1, ...]
        # scan_tuple_y = [0, 1, 2, 0, 1, 2, ...]


        if self.scan_direction_x: # scan along x
            # creating voltages
            self.x = np.tile( np.linspace(-self.Vmax_x, self.Vmax_x, self.no_of_points_x), self.no_of_points_y )
            self.y = np.repeat( np.linspace(-self.Vmax_y, self.Vmax_y, self.no_of_points_y), self.no_of_points_x )

            # creating indices
            self.scan_tuple_x = np.tile( range(self.no_of_points_x), self.no_of_points_y )
            self.scan_tuple_y = np.repeat( range(self.no_of_points_y), self.no_of_points_x )
                  
        else: # scan along y
            # creating voltages
            self.x = np.repeat( np.linspace(-self.Vmax_x, self.Vmax_x, self.no_of_points_x), self.no_of_points_y )
            self.y = np.tile( np.linspace(-self.Vmax_y, self.Vmax_y, self.no_of_points_y), self.no_of_points_x )

            # creating indices
            self.scan_tuple_x = np.repeat( range(self.no_of_points_x), self.no_of_points_y )
            self.scan_tuple_y = np.tile( range(self.no_of_points_y), self.no_of_points_x )
                       
        # choose direction of scan: forwards or backwards
        if not self.scan_direction_increasing:
            self.reverse_direction()
 

