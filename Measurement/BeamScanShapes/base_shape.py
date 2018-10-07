import matplotlib.pyplot as plt
import numpy as np

class base_shape(object):

    def __init__(self, 
            no_points_per_line, # defines the grid
            no_lines, # defines the grid
            Vmax_x = 10.0, 
            Vmax_y = 10.0, 
            offset_x = 0.0, 
            offset_y = 0.0, 
            scale_x = 100.0, 
            scale_y = 100.0
            ):

        # Define number of points in grid
        # Make sure points and lines are  > 1 and integers
        # The number of grid points shouldn't be too low (i.e. < 5)
        # since the program will not provide a descent grid
        self.no_points_per_line = max(1,int(no_points_per_line))
        self.no_lines = max(1,int(no_lines))     

        self.no_of_points_x = self.no_points_per_line
        self.no_of_points_y = self.no_lines


        self.Vmax_x = np.abs(float(Vmax_x)) # Vmax should be positive
        self.Vmax_y = np.abs(float(Vmax_y))

        # Parameters Vmax_x and Vmax_y are voltage values, in Volts
        # max voltages determining size of 'original picture'                                                     
        self.range_x = 2*self.Vmax_x
        self.range_y = 2*self.Vmax_y

        # Parameters offset_x and offset_y are the offset in % 
        # ( = % of size of 'original picture') from center of 'original picture'
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

        self.scale_x = np.abs(float(scale_x)) # scale should be positive
        self.scale_y = np.abs(float(scale_y))
                
    def scan_pattern(self):

        # x, y structure:
        # x = [-10, -10, -10,  -9, -9,  -9, ...] <- those are voltages going to the scanning coil
        # y = [-3.3,   0, +3.3, -3.3,  0, +3.3, ...]
        self.x = np.array([])        
        self.y = np.array([])

        # Scan_tuple defines the indices where the pixels are on the grid, important for Lissajous
        # scan_tuple_x = [0, 0, 0, 1, 1, 1, ...]
        # scan_tuple_y = [0, 1, 2, 0, 1, 2, ...]
        self.scan_tuple_x = np.array([])
        self.scan_tuple_y = np.array([])

        # make pattern - defined in the sub class
        self.make_pattern()
        # scale the pattern - defined in the base class
        self.scale_pattern()
        # offset the pattern - defined in the base class
        self.offset_pattern()

        return (self.x, self.y, self.scan_tuple_x, self.scan_tuple_y)

    def make_pattern(self):
        # defined in the sub class
        raise BaseException('Missing the make_pattern method in the sub class')
        pass

    def scale_pattern(self):

        # scale the vectors

        if self.scale_x > 100.0:
            self.scale_x = 100.0
            print "Scale of x is larger than 100%, adjusting to 100%"

        if self.scale_y > 100.0:
            self.scale_y = 100.0
            print "Scale of y is larger than 100%, adjusting to 100%"

        self.x *= self.scale_x/100.0
        self.y *= self.scale_y/100.0

    def offset_pattern(self):

        # check that we don't shift more than possible

        # take the max of x and restrict the offset_x to the max possible value
        if self.offset_x > 0.0:
            if (np.max(self.x) + 2.0*self.Vmax_x*self.offset_x/100.0) > +self.Vmax_x:
                # change to max offset
                self.offset_x = (+self.Vmax_x - np.max(self.x))/2.0/self.Vmax_x * 100.0
        else:
            if (np.min(self.x) + 2.0*self.Vmax_x*self.offset_x/100.0) < -self.Vmax_x:
                self.offset_x = (-self.Vmax_x - np.min(self.x))/2.0/self.Vmax_x * 100.0

        # take the max of y and restrict the offset_y to the max possible value
        if self.offset_y > 0.0:
            if (np.max(self.y) + 2.0*self.Vmax_y*self.offset_y/100.0) > +self.Vmax_y:
                self.offset_y = (+self.Vmax_y - np.max(self.y))/2.0/self.Vmax_y * 100.0
        else:
            if (np.min(self.y) + 2.0*self.Vmax_y*self.offset_y/100.0) < -self.Vmax_y:
                self.offset_y = (-self.Vmax_y - np.min(self.y))/2.0/self.Vmax_y * 100.0

        # shifting the picture
        # the factor of 2.0 stems from the fact that the offset is related to 2*Vmax, so 50% means shift by Vmax
        self.x += self.Vmax_x * 2.0*self.offset_x/100.0
        self.y += self.Vmax_y * 2.0*self.offset_y/100.0

    def reverse_direction(self):
        
        # changing the direction by inverting the x and y arrays
        self.x = self.x[::-1]
        self.y = self.y[::-1]

        self.scan_tuple_x = self.scan_tuple_x[::-1]
        self.scan_tuple_y = self.scan_tuple_y[::-1]

    def get_no_of_pixels(self):

        # returns number of pixels in the grid - ignoring samples per point
        return (self.no_of_points_x, self.no_of_points_y)

    def make_dummy(self, no_of_points_x, no_of_points_y):

        # make a dummy grid just to check things
        self.x = np.tile( np.linspace(-self.Vmax_x, self.Vmax_x, no_of_points_x), no_of_points_y )
        self.y = np.repeat( np.linspace(-self.Vmax_y, self.Vmax_y, no_of_points_y), no_of_points_x )

        self.no_of_points_x = no_of_points_x
        self.no_of_points_y = no_of_points_y

        self.scan_tuple_x = np.tile( range(no_of_points_x), no_of_points_y )
        self.scan_tuple_y = np.repeat( range(no_of_points_y), no_of_points_x )

    def plot(self):

        # plots the scan pattern
        ax1 = plt.subplot(1,2,1)
        ax2 = plt.subplot(1,2,2)

        ax1.plot(self.x, self.y, 'o-')

        ax1.plot(self.x[0], self.y[0], 'ro')
        ax1.plot(self.x[-1], self.y[-1], 'go')

        ax1.set_xlim([-self.Vmax_x, self.Vmax_x])
        ax1.set_ylim([-self.Vmax_y, self.Vmax_y])

        ax2.plot(self.scan_tuple_x, self.scan_tuple_y, 'o-')

        ax2.plot(self.scan_tuple_x[0], self.scan_tuple_y[0], 'ro')
        ax2.plot(self.scan_tuple_x[-1], self.scan_tuple_y[-1], 'go')

        plt.show()

    def plot_dynamics(self):
        
        import matplotlib.animation as anim
        fig = plt.figure()
      
        plt.xlim([-self.Vmax_x, self.Vmax_x])
        plt.ylim([-self.Vmax_y, self.Vmax_y])

        ax = fig.add_subplot(1,1,1)

        def update(i):
            #ax.clear()
            ax.plot(self.x[i], self.y[i], 'bo-')

        a = anim.FuncAnimation(fig, update, frames=len(self.x), repeat=False)
        plt.show()


    def plot_tuples(self):

        # plots the tuples of the scan pattern
        plt.plot(self.scan_tuple_x, self.scan_tuple_y, 'o-')

        plt.plot(self.scan_tuple_x[0], self.scan_tuple_y[0], 'ro')
        plt.plot(self.scan_tuple_x[-1], self.scan_tuple_y[-1], 'go')

        plt.show()

    def pixel_scaling(self):

        # returns the scaling to calculate the true size of the beam step
        return (self.scale_x/100.0/self.no_of_points_x, self.scale_y/100.0/self.no_of_points_y)

    def no_pixels(self):

        # returns the total number of pixels in the grid
        #return self.no_of_points_x * self.no_of_points_y
        # returning the number of voltages you have to give to the AO
        return len(self.x)

    def shape(self):

        # returns number of points in the grid in x and y direction
        return (self.no_of_points_x, self.no_of_points_y)

    def remove_duplicates(self):

        # removes duplicates in the voltage pairs and in the tuples
        hlp = self.x + 1j * self.y

        (hlp, ind) = np.unique(hlp, return_index = True)

        ind = np.sort(ind)

        self.x = self.x[ind]
        self.y = self.y[ind]

        self.scan_tuple_x = self.scan_tuple_x[ind]
        self.scan_tuple_y = self.scan_tuple_y[ind]




