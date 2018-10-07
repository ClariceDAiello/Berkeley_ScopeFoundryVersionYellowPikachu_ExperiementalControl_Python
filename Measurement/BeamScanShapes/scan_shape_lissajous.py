import numpy as np
from base_shape import base_shape

class CreateScanShapeLissajous(base_shape):
    '''
    generates xy coordinates for SEM and related image scanning - square scan
    '''
    def __init__(
            self, 
            no_points_per_line, # x-direction
            no_lines, # y-direction
            Vmax_x = 10.0, 
            Vmax_y = 10.0,
            offset_x = 0.0, 
            offset_y = 0.0, 
            scale_x = 100.0, 
            scale_y = 100.0, 
            scan_direction_increasing = True,
            wx = 1, # number of lobes (integer)
            step_size = 0.1, # step size in volt
            flag_remove_duplicates = True,
            snap_to_grid = True
            ):
        
        super(CreateScanShapeLissajous, self).__init__(no_points_per_line, no_lines, Vmax_x, Vmax_y, offset_x, offset_y, scale_x, scale_y)

        # Validate parameters
        # Make sure points and lines are  > 1 and integers
        self.Vmax = Vmax_x
        self.step_size = step_size
        self.wx = int(wx)

        self.flag_remove_duplicates = flag_remove_duplicates
        self.snap_to_grid = snap_to_grid

        # Scan direction increasing goes visually from L to R if X / T to B if Y   
        # self.scan_direction_x = scan_direction_x  
        self.scan_direction_increasing = scan_direction_increasing   

        # create scan shape - defined in the base class
        #self.scan_pattern()


    def make_pattern(self):

        # see e.g. Practical Handbook of Curve Design and Generation By David H. von Seggern

        # Generates the x, y pattern for the lissajous scan
        # x, y structure:
        # x = [-10,  -10,  -10,   -9, -9,  -9, ...] <- those are voltages going to the scanning coil
        # y = [-3.3,   0, +3.3, -3.3,  0, +3.3, ...]
        #
        # Scan_tuple defines the indices where the pixels are on the grid, important for Lissajous
        # scan_tuple_x = [0, 0, 0, 1, 1, 1, ...]
        # scan_tuple_y = [0, 1, 2, 0, 1, 2, ...]        

        # create x and y vectors
        # this is constructed in such a way that the beginning and endpoint overlap
        T = 2*np.pi
        
        # the step size using linspace is not equidistant because of the sinusoidals
        #no_of_steps = T/step
        #self.x = self.Vmax_x * np.sin( self.wx     * np.linspace(0, T, no_of_steps) )
        #self.y = self.Vmax_y * np.sin( (self.wx+1) * np.linspace(0, T, no_of_steps) )

        # exact solution not available, so taking approximation for small steps_x
        t = 0
        while t < T:
            self.x = np.append(self.x, self.Vmax * np.sin( self.wx     * t ))
            self.y = np.append(self.y, self.Vmax * np.sin( (self.wx+1) * t ))
            step = self.step_size/(self.Vmax * np.sqrt( self.wx**2 * np.cos( self.wx * t )**2 + (self.wx+1)**2 * np.cos( (self.wx+1) * t )**2 ))
            t += step



        # now, we have to snap the voltages to a grid
        # i.e. essentially binning the voltages
        if self.snap_to_grid:
            grid_step_size_x = 2.0*self.Vmax/self.no_of_points_x
            grid_step_size_y = 2.0*self.Vmax/self.no_of_points_y
            
            self.x = self.x + grid_step_size_x/2.0 - (self.x + grid_step_size_x/2.0) % grid_step_size_x
            self.y = self.y + grid_step_size_y/2.0 - (self.y + grid_step_size_y/2.0) % grid_step_size_y

            # the voltage divided by the step size should give the index
            # the astype command converts the array to int
            #self.scan_tuple_x = np.round(((self.x + self.Vmax)/grid_step_size_x)).astype(int)
            #self.scan_tuple_y = np.round(((self.y + self.Vmax)/grid_step_size_y)).astype(int)
            self.scan_tuple_x = np.round( (self.no_of_points_x - 1)/2.0/self.Vmax * self.x + (self.no_of_points_x - 1)/2.0 ).astype(int)
            self.scan_tuple_y = np.round( (self.no_of_points_y - 1)/2.0/self.Vmax * self.y + (self.no_of_points_y - 1)/2.0 ).astype(int)
 

        # now deleting the duplicates
        if self.flag_remove_duplicates:
            self.remove_duplicates()

        self.no_points_per_line = len(self.x)

        # choose direction of scan: forwards or backwards
        if not self.scan_direction_increasing:
            self.reverse_direction()




