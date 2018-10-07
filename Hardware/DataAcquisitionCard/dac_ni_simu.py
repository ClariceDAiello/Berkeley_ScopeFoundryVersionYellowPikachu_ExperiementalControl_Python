'''
@author: Frank Ogletree, Clarice Aiello

Many lines gratefully stolen from petebachant/daqmx, found below:
https://github.com/petebachant/daqmx/blob/master/daqmx/core.py
'''
import numpy as np

from Hardware.DataAcquisitionCard.PyDAQmx_simu import PyDAQmx_simu
mx = PyDAQmx_simu() 

from PySide.QtCore import *
from PySide.QtGui  import *

from collections import OrderedDict

from Hardware.hardware_component import HardwareComponent 

# Import helper functions
from HelperFunctions import *

class DACNI(HardwareComponent):
    
    name = 'DAC' # Needs to be given because of the hardware component structure; should match the line in set_hardware: from Hardware.DataAcquisitionCard.dac_ni import DACNI as *DAC*
    
    def __init__(self, gui, UserConfig):
        
        self.gui = gui
        self.UserConfig = UserConfig
        
        HardwareComponent.__init__(self,self.gui)
        
        self.setup()
        
    def setup(self):
        
        self.autoStart = False # Whether tasks autostart or not
        self.timeout = -1 # Timeout used to specify the amount of time in seconds to wait for the requested amount of samples to become available. 
                          # The minimum timeout value must be greater than the samples to read/write divided by the sampling rate (= minimum amount of time required for the device to acquire/generate the requested number of samples)
                          # A timeout of -1 means "wait indefinitely"                         

        # Create logged quantities; to each logged quantity there correspond one group of functions
        self.logged_quantities = OrderedDict() # Sort keys (or logged quantity names) by order at which they were declared
        
        
        self.add_logged_quantity('AO_channels_machine_names',
                                 dtype=str,
                                 ro=True,
                                 initial='X-6363/ao0,X-6363/ao1',
                                 is_variable=False,
                                 displayFlag=False)
        
        self.AIdict = dict([('SE2', 'X-6363/ai1'), ('InLens', 'X-6363/ai2'), ('VPSE', 'X-6363/ai3')])
        self.max_exp_clock = 1 #just the initial
        
#         if 2 == 2:
#            AI_machine_names = 'X-6363/ai1,X-6363/ai2'
#         elif 2 == 1:
#            AI_machine_names = 'X-6363/ai1'
#         elif 2 == 0:
#            AI_machine_names = ''
#         else:
#            self.my_msg_box('You can only set up to 2 analog in channels. Aborted!')
#            # FUTURE: ABORT GRACEFULLY 
#            return
        
        self.add_logged_quantity('AI_channels_machine_names',
                                 dtype=str,
                                 ro=True,
                                 #initial=AI_machine_names,
                                 is_variable=False,
                                 displayFlag=False)
        
       # if len(self.UserConfig.names_counter_channels) == 2:
        counter_machine_names = 'X-6363/ctr0,X-6363/ctr1'
        counter_terminal_names = 'PFI0,PFI12'
#         elif len(self.UserConfig.names_counter_channels) == 1:
#            counter_machine_names = 'X-6363/ctr0'
#            counter_terminal_names = 'PFI0'
#         elif len(self.UserConfig.names_counter_channels) == 0:
#            counter_machine_names = ''
#            counter_terminal_names = ''
#         else:
#            self.my_msg_box('You can only set up to 2 counter channels. Aborted!')
#            #  FUTURE: ABORT GRACEFULLY
#            return
#         
        self.add_logged_quantity('Counter_channels_machine_names',
                                 dtype=str,
                                 ro=True,
                                 initial=counter_machine_names,
                                 is_variable=False,
                                 displayFlag=False)
         
        self.add_logged_quantity('Counter_channels_terminal_names',
                                 dtype=str,
                                 ro=True,
                                 initial=counter_terminal_names,
                                 is_variable=False,
                                 displayFlag=False)
        
        # There are 3 clock rates for the DAC: AO (max output update 2.86MHz), AI (max acquisition 2.0MHz) and counter (max acquisition 100MHz).
        # The experiment clock rate is chosen by the slowest rate among them, namely the AI rate of 2.0MHz.
        # The clock trigger is chosen as the AO clock, since it's the AO that conceptually starts the experiment by writing beam scan voltages.
        self.add_logged_quantity('Experiment_clock_rate', 
                         dtype=float,
                         ro=True,
                         initial= 5e5,
                         vmin= np.finfo(float).eps, # Arbitrarily small number, usually of the order ~ 1e-16
                         vmax= 5e5,  # This is the max AI acquisition rate for NI DAC 6363 for 2 AI channels
                         unit='Hz',
                         is_variable=False,
                         displayFlag=True)
        
        self.add_logged_quantity('Counter_clock_rate', 
                                 dtype=float,
                                 ro=False,
                                 initial = 10e6,
                                 vmin=self.logged_quantities['Experiment_clock_rate'].val,
                                 vmax=100e6,
                                 unit='Hz',
                                 is_variable=False, # Is there any interest in being able to vary the Counter_clock_rate?
                                 displayFlag=True)
        
        
        self.add_logged_quantity('Max_beam_scan_voltage', 
                         dtype=float,
                         ro=True,
                         initial=10.0,
                         vmin=0.0, # vmin is actually -10.0 but changing the sign of the Beam_scan_voltage will reverse scan direction; since there are other ways to reverse scan voltage, by design I am forbidding values < 0
                         vmax=10.0, # This is the max analog output voltage for NI DAC 6363
                         unit='V',
                         is_variable=False,
                         displayFlag=True)
     
    def dummy(self,is_high):
        
        pass   
        
    def configure(self,  no_pixels, no_samples_per_pixel, blanking_delay, lifetime_delay, no_frames,use_TTL_beam_blanker,time_between_frames,is_imediate):

        self.no_pixels = no_pixels
        self.no_samples_per_pixel = no_samples_per_pixel
        self.no_frames = no_frames
        self.experiment_clock_rate = self.logged_quantities['Experiment_clock_rate'].read_from_hardware()
        self.time_between_frames = time_between_frames
        self.is_imediate = is_imediate
         
        # Adjust counter frequency so that there's an int number of counter clocks inside the no_samples_per_pixel * experiment clock cycle 
        desiredfreq = self.logged_quantities['Counter_clock_rate'].read_from_hardware()
        self.freq_counter = self.experiment_clock_rate/self.no_samples_per_pixel * round(self.no_samples_per_pixel/self.experiment_clock_rate*desiredfreq) 
        # Display adjusted counter frequency
        self.logged_quantities['Counter_clock_rate'].update_value(self.freq_counter)
        
        # We adjust the timehigh so that we have really dark counts and bright counts - don't want to, in the same counter clock cycle, acquire both 
        # when beam blank is on and off
        desiredtimehigh = blanking_delay
        timehigh = 1.0/self.freq_counter * round(desiredtimehigh*self.freq_counter) # timehigh: Beam is shut; this time needs to be updated in scan gui 
                                                                                  # and as such is returned from this function (at the end)
        desiredlifetime = lifetime_delay
        lifetime = 1.0/self.freq_counter * round(desiredlifetime*self.freq_counter)
        # Create and populate a tasks dictionary; important that it is ordered because I am going to use this order to start and stop tasks
        self.tasks = OrderedDict()
        
        # Check if time between frames > time one frame
        if not self.is_imediate:
           if self.time_between_frames < self.no_pixels * self.no_samples_per_pixel / self.experiment_clock_rate:
               self.is_imediate = True
               self.my_msg_box('Time between frames less than time for one frame. Automatically changing to immediate frames.')
                
        
#         self.task_list = ['Analog_out_task', 'Analog_in_task', 'Counter_task'] # The order needs to remain this one! [AO, AI, Counter]
#         
#         # AO task
#         #self.create_task(self.task_list[0], mx.TaskHandle(0))
#         # Add exactly 2 AO channels to the AO task, for doing external beam scan
#         for k in range(2): 
#             self.add_AO_line(self.logged_quantities['AO_channels_machine_names'].val.split(',')[k],self.task_list[0])
#             
#         # AI task
#         #self.create_task(self.task_list[1], mx.TaskHandle(1))
#         # Add up to 2 AI channels to the AI task
#         for k in range(2):
#             self.add_AI_line(self.logged_quantities['AI_channels_machine_names'].val.split(',')[k],self.task_list[1])
#          
#         # Counter task
#         #self.create_task(self.task_list[2], mx.TaskHandle(2))       
#         # Add up to 2 counter channels to the counter task
#         for k in range(len(self.UserConfig.names_counter_channels)):
#             self.add_counter_line(self.logged_quantities['Counter_channels_machine_names'].val.split(',')[k],self.logged_quantities['Counter_channels_terminal_names'].val.split(',')[k],self.task_list[2])
#             
#     #def configure(self, no_pixels, no_AI_samples, no_counter_samples):        
#             
#         # Configure trigger of AI task to be AO start trigger
#         self.clock_trigger = '/ao/StartTrigger' 
        #self.set_trigger(self.task_list[1], self.clock_trigger)
        
        # For all the tasks, sets the source of the sample clock, and the number of samples to acquire or generate, if not acquiring continuously
        #self.clock_source = ['', '', '/ao/SampleClock'] # Not sure why the clock source is left blank for analog channels
        #self.buffer_size = [no_pixels, no_AI_samples, no_counter_samples] # My hope is that it adds a buffer for each channel connected to a task
        #for k in range(len(self.task_list)):
        #    self.set_clock(self.task_list[k], self.clock_source[k], is_finite, self.buffer_size[k])  
        
        self.buffer_size = [no_pixels,0,0] #
        self.int_clock_rate = int(self.freq_counter/self.experiment_clock_rate)
        no_pmt_samples =  self.no_pixels*self.no_samples_per_pixel *self.int_clock_rate *self.no_frames 
        #return timehigh,  self.int_clock_rate, int(round(timehigh*self.freq_counter)), self.is_imediate, self.freq_counter
    
        return  self.freq_counter, self.int_clock_rate, timehigh, int(round(timehigh*self.freq_counter)), lifetime, int(round(lifetime*self.freq_counter)), self.is_imediate, 30

                          
    def start_data_acquisition(self):
        pass
        # Start tasks: counter first, than AI before AO (since AI waits for AO trigger)
        #for k in range(len(self.task_list)-1,-1,-1):
           # self.start_task(self.task_list[k])
            
    def read_data(self, arg1):#, no_samples_to_read):
        
        self.read_AI_buffer(arg1) #no_samples_to_read)
        self.read_counter_buffer(arg1) #no_samples_to_read)
        return self.data_AI, self.data_counter, self.data_counter_time_resolved
    
    def stop_data_acquisition(self,is_forced=False):
        pass
        # Stop and clear tasks
        #for k in range(len(self.task_list)):
        #    self.stop_task(self.task_list[k])
         #   self.clear_task(self.task_list[k])
      
      
    '''
    Tasks
    '''
    def create_task(self, taskname, taskhandle, fatalerror=True):
        pass
        #self.error_handling(mx.DAQmxCreateTask(taskname, mx.byref(taskhandle)), fatalerror)        
   
    def start_task(self, taskname, fatalerror=True):
        pass
        #self.error_handling(mx.DAQmxStartTask(taskname), fatalerror)

    def stop_task(self, taskname, fatalerror=True):
        pass
        #self.error_handling(mx.DAQmxStopTask(taskname), fatalerror)
    
    def clear_task(self, taskname, fatalerror=True):
        pass
        #self.error_handling(mx.DAQmxClearTask(taskname), fatalerror)
        
    
    '''
    Analog out
    '''
    def add_AO_line(self, machine_name, taskname, fatalerror=True):
        pass
        # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, const char customScaleName[])
        #self.error_handling(mx.CreateAOVoltageChan(taskname, machine_name, '', -self.logged_quantities['Max_beam_scan_voltage'].val, +self.logged_quantities['Max_beam_scan_voltage'].val, mx.DAQmx_Val_Volts, ''), fatalerror)        
   
    def load_AO_buffer(self, scan_pattern, fatalerror=True):
        # Array-like objects converted to np arrays if required
        # Scan_pattern is interleaved, i.e. [x1, y1, x2, y2, x3, y3...], for output on x and y. This is reflected in the choice mx.DAQmx_Val_GroupByScanNumber
         
#         if not isinstance( scan_pattern, np.ndarray ) or scan_pattern.dtype != np.float64:
#             scan_pattern = np.asarray(scan_pattern, dtype = np.float64 )
#             
#         if not len(scan_pattern) == 2*self.buffer_size[0]:
#             self.my_msg_box('Something went wrong - scan_pattern is not twice as long as the buffer_size of each AO channel! In the future, abort here.')
#          
        pass   
        # WriteAnalogF64 (int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved)    
        #self.error_handling(mx.WriteAnalogF64(self.task_list[0], self.buffer_size[0], self.autoStart, self.timeout, mx.DAQmx_Val_GroupByScanNumber, scan_pattern,''), fatalerror)    
   
   
    '''
    Analog in
    '''
    def add_AI_line(self, machine_name, taskname, fatalerror=True):
        pass
        # CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[])
        #self.error_handling(mx.CreateAIVoltageChan(taskname, machine_name, '', mx.Val_Cfg_Default, -self.logged_quantities['Max_beam_scan_voltage'].val, +self.logged_quantities['Max_beam_scan_voltage'].val, mx.DAQmx_Val_Volts, ''), fatalerror) 
        
    def read_AI_buffer(self, buff, fatalerror=True):
        self.buffer_size[1] = buff
        # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved)
        #self.error_handling(mx.ReadAnalogF64(self.task_list[1], self.buffer_size[1], self.timeout, mx.DAQmx_Val_GroupByScanNumber, self.data_AIs, self.buffer_size[1]*2,self.buffer_size[1],''), fatalerror)   
        # data_AIs also contains interleaved data, [x1, y1, x2, y2...]
        # Separate data from AI channels - reverse interleaving and output data by channel
        ### THIS READS THE COMPLETE BUFFER
        #self.data_AIs = np.random.rand(self.buffer_size[1]*2) 
        self.data_AIs = np.arange(self.buffer_size[1]*2)
        self.data_AI = np.zeros(shape=[2, self.buffer_size[1] ])
        for k in range(2):
            self.data_AI[k] = self.data_AIs[k::2]
            
        #### THIS READS NO_SAMPLES_TO_READ ONLY
#        self.data_AIs = np.random.rand(no_samples_to_read*2)
#       self.data_AI = np.zeros(shape=[2, no_samples_to_read ])
#        for k in range(2):
 #           self.data_AI[k] = self.data_AIs[k::2]

    '''
    Counters
    '''
    def add_counter_line(self, machine_name, terminal_name, taskname, fatalerror=True):
        pass
        #CreateCICountEdgesChan (const char counter[], const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection)
        #self.error_handling(mx.CreateCICountEdgesChan(taskname, machine_name, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp), fatalerror) 
        #self.error_handling(mx.SetCICountEdgesTerm(taskname, machine_name, terminal_name), fatalerror) 
        
    def read_counter_buffer(self, buff, fatalerror=True):
        self.buffer_size[2] = buff
        
        
        #self.tasks['Counter1_task'].ReadCounterF64( mx.int32(buffer_size) , self.timeout,  data_counters, buffer_size,mx.byref(mx.int32(buffer_size)),None)
        #newly = np.insert(data_counters,0,0)
        #self.data_counter_time_resolved[0] = np.diff(newly)
        
        #newarr = np.mean(data_counters.reshape(-1,int(self.fac)), axis=1)
        #data_counters=np.insert(newarr,0,0)
        #data_counters=np.diff(data_counters)
        #self.data_counter[0] = data_counters
        #self.tasks['Counter1_task'].WaitUntilTaskDone(self.timeout)
        
        
        
        
        # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved)
        #self.error_handling(mx.ReadCounterF64(self.task_list[2], self.buffer_size[2], self.timeout, mx.DAQmx_Val_GroupByScanNumber, self.data_counters, self.buffer_size[2]*len(self.UserConfig.names_Counter_channels),self.buffer_size[2],''), fatalerror)   
        # data_counter also contains interleaved data, [x1, y1, x2, y2...]
        # Separate data from individual counters - reverse interleaving and output data by channel
        ###### THIS READS ENTIRE BUFFER
        #self.data_counters = np.random.rand(self.buffer_size[2]*len(self.UserConfig.names_counter_channels))
        self.data_counters = np.arange(self.buffer_size[2]*2)
        self.data_counter = np.zeros(shape=[2, self.buffer_size[2] ])
        for k in range(2):
            self.data_counter[k] = self.data_counters[k::2]
        #### THIS READS NO_SAMPLES_TO_READ ONLY
 #       self.data_counters = np.random.rand(no_samples_to_read*len(self.UserConfig.names_counter_channels))
  #      self.data_counter = np.zeros(shape=[len(self.UserConfig.names_counter_channels), no_samples_to_read ])
 #       for k in range(len(self.UserConfig.names_counter_channels)):
  #          self.data_counter[k] = self.data_counters[k::len(self.UserConfig.names_counter_channels)]
        self.fac = self.int_clock_rate
        self.data_counter_time_resolved = np.zeros(shape=[2, buff*self.fac ])
    '''
    Timing and trigger
    '''
    def set_trigger(self, taskname, machine_terminal_to_trigger_task_to, fatalerror=True):
        pass
        # DAQmxCfgDigEdgeStartTrig (const char triggerSource[], int32 triggerEdge)
        #self.error_handling(mx.CfgDigEdgeStartTrig(taskname, machine_terminal_to_trigger_task_to, mx.DAQmx_Val_Rising), fatalerror) 

    def set_clock(self, taskname, clock_source, is_finite, buffer_size, fatalerror=True):
        pass
        if is_finite:
           sampleMode = mx.DAQmx_Val_FiniteSamps
        else:
           sampleMode = mx.DAQmx_Val_ContSamps # Generates samples until task is stopped
        
        # DAQmxCfgSampClkTiming ( const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChanToAcquire)
        #self.error_handling(mx.CfgDigEdgeStartTrig(taskname, clock_source, mx.DAQmx_Val_Rising, sampleMode, buffer_size), fatalerror)     
     
         
    '''
    Errors
    '''
    def error_handling(returned_value, fatalerror=True):
        if returned_value != 0:
            if fatalerror == True:
                raise RuntimeError(get_error_string(returned_value))
            else: 
                print(get_error_string(returned_value))
        else: 
            return
        
    def get_error_string(errorcode, buffersize=512):
        errorstring = ctypes.create_string_buffer(buffersize)
        mx.DAQmxGetErrorString(int32(errorcode), byref(errorstring), uInt32(buffersize))
        return errorstring.value.decode()
    
    def my_msg_box(self,input_text):
       msgBox = QMessageBox()
       msgBox.setText(input_text)
       msgBox.exec_(); 