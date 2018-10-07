import PyDAQmx as mx

import numpy as np
import pyqtgraph as pg
import time

from collections import OrderedDict

from PySide.QtCore import *
from PySide.QtGui  import *

from Hardware.hardware_component import HardwareComponent 

# Import helper functions
from HelperFunctions import *

class DACNI(HardwareComponent):
    
    name = 'DAC' # Needs to be given because of the hardware component structure; should match the line in set_hardware: from Hardware.DataAcquisitionCard.dac_ni import DACNI as *DAC*
    
    def __init__(self, gui, main_gui):
        
        self.gui = gui
        self.main_gui = main_gui
        
        HardwareComponent.__init__(self,self.gui)
      
    def setup(self):
        
        self.update_after = 100
        
        self.autoStart = False # Whether tasks autostart or not
        self.timeout = -1 # Timeout used to specify the amount of time in seconds to wait for the requested amount of samples to become available. 
                          # The minimum timeout value must be greater than the samples to read/write divided by the sampling rate (= minimum amount of time required for the device to acquire/generate the requested number of samples)
                          # A timeout of -1 means "wait indefinitely"                         

        # Create logged quantities; to each logged quantity there correspond one group of functions
        self.logged_quantities = OrderedDict() # Sort keys (or logged quantity names) by order at which they were declared
        
        self.add_logged_quantity('AO_channels_machine_names',
                                 dtype=str,
                                 ro=True,
                                 initial='X-6363/ao0:1',
                                 is_variable=False,
                                 displayFlag=False)
        
        self.AIdict = dict([('SE2', 'X-6363/ai1'), ('InLens', 'X-6363/ai2'), ('VPSE', 'X-6363/ai3')])
        self.max_exp_clock = 1 #just the initial
        
        self.add_logged_quantity('AI_channels_machine_names',
                                 dtype=str,
                                 ro=True,
                                 initial='',
                                 is_variable=False,
                                 displayFlag=False)
        
        if len(self.main_gui.UserConfig.names_counter_channels) == 2:
            counter_machine_names = 'X-6363/ctr2,X-6363/ctr3'
            counter_terminal_names = 'PFI0,PFI5'
        elif len(self.main_gui.UserConfig.names_counter_channels) == 1:
            counter_machine_names = 'X-6363/ctr2'
            counter_terminal_names = 'PFI0'
        elif len(self.main_gui.UserConfig.names_counter_channels) == 0:
            counter_machine_names = ''
            counter_terminal_names = ''
        else:
            self.my_msg_box('You can only set up to 2 counter channels. Aborted!')
            #  FUTURE: ABORT GRACEFULLY
            return None
        
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
        
        # There are 3 clock rates for the DAC: AO (max output update 2.86MHz), AI (max acquisition 2MHz for 1 channel; for N channels,
        # max rate is 1MHz/N), and counter (max acquisition 100MHz).
        # The experiment clock rate is chosen by the slowest rate among them, namely the AI rate.
        self.add_logged_quantity('Experiment_clock_rate', 
                         dtype=float,
                         ro=True,
                         initial= self.max_exp_clock,
                         vmin= np.finfo(float).eps, # Arbitrarily small number, usually of the order ~ 1e-16
                         vmax= self.max_exp_clock,  # This is the max AI acquisition rate for NI DAC 6363
                         unit='Hz',
                         is_variable=False,
                         displayFlag=True)
           
        self.add_logged_quantity('Counter_clock_rate', 
                                 dtype=float,
                                 ro=False,
                                 initial = self.logged_quantities['Experiment_clock_rate'].read_from_hardware(),
                                 vmin=self.logged_quantities['Experiment_clock_rate'].read_from_hardware(),
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
        # This function sets the Raith beam blanker to a high (= beam shut) or low state (= beam open)
        self.tasks = OrderedDict()
        self.tasks['Counter_Pulse_Train'] = NamedTask('Counter_Pulse_Train')
        timehigh = 5e-3
        timelow = 5e-3
        if is_high:
            val = mx.DAQmx_Val_High
        else:
            val = mx.DAQmx_Val_Low
        self.tasks['Counter_Pulse_Train'].CreateCOPulseChanTime('X-6363/ctr0','', mx.DAQmx_Val_Seconds, val, timehigh, timelow, timehigh) # initial delay, low level time, high level time                                   
        no_train_samples = 1
        self.tasks['Counter_Pulse_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, no_train_samples) 
        self.tasks['Counter_Pulse_Train'].StartTask()
        time.sleep(50e-3) 
        #self.tasks['Counter_Pulse_Train'].WaitUntilTaskDone(self.timeout) #seems to be much slower than needed!
        self.tasks['Counter_Pulse_Train'].StopTask()              
        self.tasks['Counter_Pulse_Train'].ClearTask()
        
    def configure(self, no_pixels, no_samples_per_pixel, blanking_delay, lifetime_delay, no_frames,use_TTL_beam_blanker,time_between_frames,is_imediate):    
    
        self.no_pixels = no_pixels
        self.no_samples_per_pixel = no_samples_per_pixel
        self.no_frames = no_frames
        self.experiment_clock_rate = self.logged_quantities['Experiment_clock_rate'].read_from_hardware()
        self.time_between_frames = time_between_frames
        self.is_imediate = is_imediate
        self.use_TTL_beam_blanker = use_TTL_beam_blanker # if not using TTL blanker, dummy output counter channel, leaving the beam open
         
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
                                                                                  
        # We adjust the timelifetime so that we have really dark counts and bright counts - don't want to, in the same counter clock cycle, acquire both 
        # when beam blank is on and off
        desiredlifetime = lifetime_delay
        lifetime = 1.0/self.freq_counter * round(desiredlifetime*self.freq_counter)
        
        # Create and populate a tasks dictionary; important that it is ordered because I am going to use this order to start and stop tasks
        self.tasks = OrderedDict()
        
        # Check if time between frames > time one frame
        dummy_value = 10e-3
        if not self.is_imediate:
           if self.time_between_frames < self.no_pixels * self.no_samples_per_pixel / self.experiment_clock_rate + dummy_value:
               self.is_imediate = True
               self.my_msg_box('Time between frames less than time for one frame (plus short value to make readout before new buffer overwrites). Automatically changing to immediate frames.')
        
        if self.is_imediate:
            
            self.time_between_frames = self.no_pixels * self.no_samples_per_pixel / self.experiment_clock_rate #not used inside the if; just to be returned and saved
            
            #No DO line needed
            # Beam blanker pulse train: delimits when to acquire
            self.tasks['Counter_Pulse_Train'] = NamedTask('Counter_Pulse_Train')
            # 1/(timelow+timehigh) = Experiment_clock_rate = frequency of AO out
            
             
            timelow = self.no_samples_per_pixel/(self.experiment_clock_rate) - timehigh - lifetime
            no_train_samples = self.no_pixels *self.no_frames #There is one acquisition window per pixel
            # Beam blanker LOW == BEAM OPEN     HIGH -> BEAM SHUT
            # mx.DAQmx_Val_High -> needs to be high by default
            if use_TTL_beam_blanker:
                self.tasks['Counter_Pulse_Train'].CreateCOPulseChanTime('X-6363/ctr0','', mx.DAQmx_Val_Seconds, mx.DAQmx_Val_High, timehigh, timelow, timehigh + lifetime) # initial delay, low level time, high level time                                   
                self.tasks['Counter_Pulse_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, no_train_samples) 
                # Trigger of beam blanker is start of AO
                self.tasks['Counter_Pulse_Train'].SetArmStartTrigType(mx.DAQmx_Val_DigEdge)    
                self.tasks['Counter_Pulse_Train'].SetDigEdgeArmStartTrigSrc('ao/StartTrigger')
                self.tasks['Counter_Pulse_Train'].SetDigEdgeArmStartTrigEdge(mx.DAQmx_Val_Rising)  
                                
                   #### Did I use to have a falling edge here????
            else: #Run a dummy cycle , then keep it low
                # timehigh and timelow set to min of beam blanker, 1e6 - not hard code this later
                self.tasks['Counter_Pulse_Train'].CreateCOPulseChanTime('X-6363/ctr0','', mx.DAQmx_Val_Seconds, mx.DAQmx_Val_Low, 0, 1.0e-6,1.0e-6) # initial delay, low level time, high level time                                   
                self.tasks['Counter_Pulse_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, 1)
                self.tasks['Counter_Pulse_Train'].StartTask()
            
            # High-frequency pulse train: count counts
            self.tasks['Counter_HF_Train'] = NamedTask('Counter_HF_Train') 
           
            duty_cycle = 0.5
            self.tasks['Counter_HF_Train'].CreateCOPulseChanFreq('X-6363/ctr1','', mx.DAQmx_Val_Hz, mx.DAQmx_Val_Low, 0, self.freq_counter, duty_cycle)
            self.int_clock_rate = int(self.freq_counter/self.experiment_clock_rate)
            no_pmt_samples =  self.no_pixels*self.no_samples_per_pixel *self.int_clock_rate *self.no_frames 
            self.tasks['Counter_HF_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, no_pmt_samples)
             
            # Trigger of high-frequency pulse train 
            self.tasks['Counter_HF_Train'].SetArmStartTrigType(mx.DAQmx_Val_DigEdge)
            self.tasks['Counter_HF_Train'].SetDigEdgeArmStartTrigSrc('ao/StartTrigger')
            self.tasks['Counter_HF_Train'].SetDigEdgeArmStartTrigEdge(mx.DAQmx_Val_Rising)
            
            # PMT counter channels
            # Create pulse width measurement
            MinVal = 0.000200 # MinVal = 2/rate  ##### Check this which rate that is 
            MaxVal = 10
            self.tasks['Counter1_task'] = NamedTask('Counter1_task')
            self.tasks['Counter2_task'] = NamedTask('Counter2_task')
            # This is the number of counter samples: no of beam blanker trains * number of blue HF train under one blanker train
             
            # Set up for buffered edge counting (fig. 7-4) using the PF13 = HF Train Out as a Sampleclock 
            self.tasks['Counter1_task'].CreateCICountEdgesChan('X-6363/ctr2','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
            # Below: this 100e6 number that appears in CfgSampClkTiming is the maximum expected rate of the HF train. Also, needs ContSamps -  why?????
            ######## In GatedMEasurements.py, the test program, I needed to use mx.DAQmx_Val_ContSamps; here, for it to work I needed Finite
            self.tasks['Counter1_task'].CfgSampClkTiming('PFI13', 100e6, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, no_pmt_samples ) 
            self.tasks['Counter1_task'].SetCIDupCountPrevent('X-6363/ctr2',1)
            if len(self.main_gui.UserConfig.names_counter_channels) == 2:
                self.tasks['Counter2_task'].CreateCICountEdgesChan('X-6363/ctr3','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
                self.tasks['Counter2_task'].CfgSampClkTiming('PFI13', 100e6, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, no_pmt_samples )
             
            # AI
            no_AI_samples = self.no_pixels*self.no_samples_per_pixel *self.no_frames
            self.tasks['AI_task'] = NamedTask('AI_task')
            #print self.logged_quantities['AI_channels_machine_names'].val
            self.add_AI_lines(self.logged_quantities['AI_channels_machine_names'].val,self.tasks['AI_task'])
            self.tasks['AI_task'].CfgSampClkTiming( ' ',self.experiment_clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps,no_AI_samples)
            self.tasks['AI_task'].SetStartTrigType(mx.DAQmx_Val_DigEdge)
            self.tasks['AI_task'].CfgDigEdgeStartTrig('ao/StartTrigger', mx.DAQmx_Val_Rising)
 
            #No trigger for AO task - it is the one driving the acqusitions
            self.tasks['AO_task'] = NamedTask('AO_task')
            self.add_AO_lines(self.logged_quantities['AO_channels_machine_names'].val,self.tasks['AO_task'])
            self.tasks['AO_task'].CfgSampClkTiming( '', self.experiment_clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, self.no_pixels*self.no_samples_per_pixel *self.no_frames)
       
        else: #ther's a delay between frames
        
            ################################################################################ NEW- RETRIG ALL ONTO DO LINE
            
            # Source of retriggering pulses
            clockTrigDO = 10.0e6 #100e3
            clockTrigSrc =  '10MHzRefClock' #'100kHzTimebase'
            no_of_repetitions = 10 # just so that the DO doesn't switch from 0 to 5 in one cycle: 000 555 etc
            
            trig_do_samples_per_frame = self.time_between_frames * clockTrigDO 
            no_Trig_DO_samples = int(self.no_frames * trig_do_samples_per_frame) 
            #### ADJUST AND DISPLAY HERE TIME BETWEEN FRAMES
            
            # There is a physical cable from PFI2 to P0.0
            DummytrigAOterm = 'PFI2' #'PFI2' #PFI1 This is Ctr2 Z, whatever Z is; PFI2 This is Ctr2 B, whatever B is; 
            portname = 'X-6363/port0/line0'
            
            # DO Trigger Task 
            self.tasks['Trig_DO'] = NamedTask('Trig_DO')
            self.tasks['Trig_DO'].CreateDOChan(portname, '', mx.DAQmx_Val_ChanForAllLines)
            self.tasks['Trig_DO'].CfgSampClkTiming(clockTrigSrc,  clockTrigDO, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, no_Trig_DO_samples)
    
           # write AO samples
            data_Trig_DO = np.repeat(np.array([np.int32(0.0), np.int32(5.0)]), no_of_repetitions)
            data_Trig_DO = np.tile(np.append(data_Trig_DO, [np.int32(0.0)] * int(trig_do_samples_per_frame - 2*no_of_repetitions)), self.no_frames)
            data_Trig_DOnew = np.uint32(data_Trig_DO)
            self.tasks['Trig_DO'].WriteDigitalU32(no_Trig_DO_samples, self.autoStart, self.timeout, mx.DAQmx_Val_GroupByChannel,data_Trig_DOnew,mx.int32(no_Trig_DO_samples), None)
            
            #####################################################################################
            
            ######################################RETRIG PULSE TRAIN
            
            # Beam blanker pulse train: delimits when to acquire
            self.tasks['Counter_Pulse_Train'] = NamedTask('Counter_Pulse_Train')
            # 1/(timelow+timehigh) = Experiment_clock_rate = frequency of AO out
            
            timelow = self.no_samples_per_pixel/(self.experiment_clock_rate) - timehigh - lifetime
            no_train_samples = self.no_pixels #*self.no_frames #There is one acquisition window per pixel
            # Beam blanker LOW == BEAM OPEN     HIGH -> BEAM SHUT
            # mx.DAQmx_Val_High -> needs to be high by default
            if self.use_TTL_beam_blanker:
                self.tasks['Counter_Pulse_Train'].CreateCOPulseChanTime('X-6363/ctr0','', mx.DAQmx_Val_Seconds, mx.DAQmx_Val_High, timehigh, timelow, timehigh + lifetime) # initial delay, low level time, high level time                                   
                self.tasks['Counter_Pulse_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, no_train_samples)  
                self.tasks['Counter_Pulse_Train'].CfgDigEdgeStartTrig(DummytrigAOterm,mx.DAQmx_Val_Falling) 
                self.tasks['Counter_Pulse_Train'].SetStartTrigRetriggerable(mx.bool32(True))
                self.tasks['Counter_Pulse_Train'].SetCOEnableInitialDelayOnRetrigger('X-6363/ctr0',mx.bool32(True))
            
            else: #Run a dummy cycle , then keep it low
                self.tasks['Counter_Pulse_Train'].CreateCOPulseChanTime('X-6363/ctr0','', mx.DAQmx_Val_Seconds, mx.DAQmx_Val_Low, timehigh, timelow, timehigh) # initial delay, low level time, high level time                                   
                self.tasks['Counter_Pulse_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, 1)
                self.tasks['Counter_Pulse_Train'].StartTask()
            
            ####################################RETRIG HF FREQ TRAIN
        
            # High-frequency pulse train: count counts
            self.tasks['Counter_HF_Train'] = NamedTask('Counter_HF_Train') 
          
            duty_cycle = 0.5
            self.tasks['Counter_HF_Train'].CreateCOPulseChanFreq('X-6363/ctr1','', mx.DAQmx_Val_Hz, mx.DAQmx_Val_Low, 0, self.freq_counter, duty_cycle)
            self.int_clock_rate = int(self.freq_counter/self.experiment_clock_rate)
            no_pmt_samples =  self.no_pixels*self.no_samples_per_pixel *self.int_clock_rate  #*self.no_frames 
            self.tasks['Counter_HF_Train'].CfgImplicitTiming(mx.DAQmx_Val_FiniteSamps, no_pmt_samples)
            self.tasks['Counter_HF_Train'].CfgDigEdgeStartTrig(DummytrigAOterm,mx.DAQmx_Val_Falling) 
            self.tasks['Counter_HF_Train'].SetStartTrigRetriggerable(mx.bool32(True))
            self.tasks['Counter_HF_Train'].SetCOEnableInitialDelayOnRetrigger('X-6363/ctr1',mx.bool32(True))
            
            ########################################################## PMTs
            
            # PMT counter channels
            # Create pulse width measurement
            MinVal = 0.000200 # MinVal = 2/rate  ##### Check this which rate that is 
            MaxVal = 10
            self.tasks['Counter1_task'] = NamedTask('Counter1_task')
            self.tasks['Counter2_task'] = NamedTask('Counter2_task')
            # This is the number of counter samples: no of beam blanker trains * number of blue HF train under one blanker train
            
            # Set up for buffered edge counting (fig. 7-4) using the PF13 = HF Train Out as a Sampleclock 
            self.tasks['Counter1_task'].CreateCICountEdgesChan('X-6363/ctr2','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
            # Below: this 100e6 number that appears in CfgSampClkTiming is the maximum expected rate of the HF train. Also, needs ContSamps -  why?????
            ######## In GatedMEasurements.py, the test program, I needed to use mx.DAQmx_Val_ContSamps; here, for it to work I needed Finite
            self.tasks['Counter1_task'].CfgSampClkTiming('PFI13', 100e6, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, no_pmt_samples*self.no_frames ) 
            self.tasks['Counter1_task'].SetCIDupCountPrevent('X-6363/ctr2',1)
            if len(self.main_gui.UserConfig.names_counter_channels) == 2:
                self.tasks['Counter2_task'].CreateCICountEdgesChan('X-6363/ctr3','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
                self.tasks['Counter2_task'].CfgSampClkTiming('PFI13', 100e6, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, no_pmt_samples*self.no_frames )
                
            ########################################################### Retriggerable AI
             
            # AI
            no_AI_samples = self.no_pixels*self.no_samples_per_pixel #*self.no_frames
            self.tasks['AI_task'] = NamedTask('AI_task')
            print self.logged_quantities['AI_channels_machine_names'].val
            self.add_AI_lines(self.logged_quantities['AI_channels_machine_names'].val,self.tasks['AI_task'])
            self.tasks['AI_task'].CfgSampClkTiming( ' ',self.experiment_clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps,no_AI_samples)
            self.tasks['AI_task'].SetStartTrigType(mx.DAQmx_Val_DigEdge)
            self.tasks['AI_task'].CfgDigEdgeStartTrig(DummytrigAOterm,mx.DAQmx_Val_Falling)   #Rising #.SetStartTrigTerm    CfgDigEdgeStartTrig 
            self.tasks['AI_task'].SetStartTrigRetriggerable(mx.bool32(True))
            
            ##################################################################################### RETRIG A0
            self.tasks['AO_task'] = NamedTask('AO_task')
            self.add_AO_lines(self.logged_quantities['AO_channels_machine_names'].val,self.tasks['AO_task'])
            self.tasks['AO_task'].CfgSampClkTiming( '', self.experiment_clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_FiniteSamps, self.no_pixels*self.no_samples_per_pixel) # *self.no_frames)
            self.tasks['AO_task'].SetStartTrigType(mx.DAQmx_Val_DigEdge)
            self.tasks['AO_task'].CfgDigEdgeStartTrig(DummytrigAOterm,mx.DAQmx_Val_Falling)   #Rising #.SetStartTrigTerm    CfgDigEdgeStartTrig 
            self.tasks['AO_task'].SetStartTrigRetriggerable(mx.bool32(True))
  
        return  self.freq_counter, self.int_clock_rate, timehigh, int(round(timehigh*self.freq_counter)), lifetime, int(round(lifetime*self.freq_counter)), self.is_imediate, self.time_between_frames
        # third return is how many dark samples
        # 5th is how many lifetime samples
    
    def start_data_acquisition(self):
        if self.use_TTL_beam_blanker:
            self.tasks['Counter_Pulse_Train'].StartTask() #waits for AO
            
        self.tasks['Counter_HF_Train'].StartTask() #waits for AO
        self.tasks['Counter1_task'].StartTask() #waits for AO 
        self.tasks['Counter2_task'].StartTask() #waits for AO 
        self.tasks['AI_task'].StartTask() #waits for AO 
        self.tasks['AO_task'].StartTask()   
        
        if not self.is_imediate:
            self.tasks['Trig_DO'].StartTask()      
           
    def read_data(self,buffersize):
        
        self.read_counter_buffer(buffersize)
        self.read_AI_buffer(buffersize)
        
        return self.data_AI, self.data_counter, self.data_counter_time_resolved
    
    def stop_data_acquisition(self,is_forced=False):
        
#        if not self.is_imediate: 
#            time.sleep(self.no_frames * self.time_between_frames) #give time to the tasks to complete
#            # DO i need this? wont the data reading limit howfast I acquire data?
       if is_forced:
           
           for key in self.tasks:
               #self.tasks[key].TaskControl(mx.DAQmx_Val_Task_Abort)     
               self.tasks[key].ClearTask()
           
       else:        
           
           if 'Trig_DO' in self.tasks.keys():
               self.tasks['Trig_DO'].TaskControl(mx.DAQmx_Val_Task_Abort)
               self.tasks['Trig_DO'].ClearTask()
               del self.tasks['Trig_DO']
               
           for key in self.tasks:
               self.tasks[key].StopTask()              
               self.tasks[key].ClearTask()
       
#        self.tasks['Counter1_task'].StopTask()              
#        self.tasks['Counter1_task'].ClearTask()
#        
#        self.tasks['Counter2_task'].StopTask()              
#        self.tasks['Counter2_task'].ClearTask()
#        
#        self.tasks['AI_task'].StopTask()              
#        self.tasks['AI_task'].ClearTask()
#        
#        self.tasks['Counter_Pulse_Train'].StopTask()              
#        self.tasks['Counter_Pulse_Train'].ClearTask()
#        
#        self.tasks['Counter_HF_Train'].StopTask()              
#        self.tasks['Counter_HF_Train'].ClearTask()
#        
#        self.tasks['AO_task'].StopTask()              
#        self.tasks['AO_task'].ClearTask()
#        
#        if not self.is_imediate:
#            self.tasks['Trig_DO'].TaskControl(mx.DAQmx_Val_Task_Abort)
#            # Neither of the below will work, gives error of missed samples to write
#            #self.tasks['Trig_DO'].AbortTask()
#            #self.tasks['Trig_DO'].WaitUntilTaskDone(self.timeout)
#            #self.tasks['Trig_DO'].StopTask()              
#            self.tasks['Trig_DO'].ClearTask()

    def count_continuously(self):
        
            self.main_gui.results_widget.fig_ch[0].lineedit_name.setDisabled(True)
            self.main_gui.results_widget.fig_ch[1].lineedit_name.setDisabled(True)
        
            # Create and populate a tasks dictionary; important that it is ordered because I am going to use this order to start and stop tasks
            self.tasks = OrderedDict()
        
            no_samples = 50000# 50000 #once or half or 1/10 of sample rate will do - too few samples and there wil lbe error
            #http://forums.ni.com/t5/LabVIEW/Attempted-to-read-samples-that-are-no-longer-available/td-p/331498
            clock_rate = 1e6
            
            # This is a dummy AI task required for doing buffered edge counting
            self.tasks['AI_clock'] = NamedTask('AI_clock')
            self.tasks['AI_clock'].CreateAIVoltageChan('X-6363/ai1', '', mx.DAQmx_Val_Cfg_Default, -self.logged_quantities['Max_beam_scan_voltage'].val, +self.logged_quantities['Max_beam_scan_voltage'].val, mx.DAQmx_Val_Volts, '')
            self.tasks['AI_clock'].CfgSampClkTiming( '', clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, no_samples) 
            
            # Get numbers from counters from machine name instead
            self.tasks['Counter_tracker'] = NamedTask('Counter_tracker')
            self.tasks['Counter_tracker'].CreateCICountEdgesChan('X-6363/ctr2','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
            self.tasks['Counter_tracker'].SetCICountEdgesTerm('X-6363/ctr2','PFI0')
            
            self.tasks['Counter_tracker2'] = NamedTask('Counter_tracker2')
            self.tasks['Counter_tracker2'].CreateCICountEdgesChan('X-6363/ctr3','', mx.DAQmx_Val_Rising,0, mx.DAQmx_Val_CountUp)
            self.tasks['Counter_tracker2'].SetCICountEdgesTerm('X-6363/ctr3','PFI5')
           
            ###### READING THE CLOCK AT 10 TIMES THE AI CLOCK RATE - LOOK OUT FOR THE *10 NEEDED
            #CORRECT THIS LATER
            self.tasks['Counter_tracker'].CfgSampClkTiming('10MHzRefClock',10*clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 50*no_samples)
            self.tasks['Counter_tracker2'].CfgSampClkTiming('10MHzRefClock',10*clock_rate, mx.DAQmx_Val_Rising, mx.DAQmx_Val_ContSamps, 50*no_samples)
           
            self.tasks['AI_clock'].StartTask()
            self.tasks['Counter_tracker'].StartTask()
            self.tasks['Counter_tracker2'].StartTask()
            
            self.abort = 0
        
            tot = []
            tot2 = []
            
            self.win = MyPlot(self,title="Counts") 
            self.win.resize(1000,600)
            #self.win.setWindowFlags
            #self.win.setWindowFlags(Qt.WindowMinimizeButtonHint)
            #self.win.ui.setModal(True)Qt::FramelessWindowHint
            #self.win.setWindowFlags(Qt.FramelessWindowHint)
            #self.win.setWindowFlags(Qt.CustomizeWindowHint)
            #self.win.setWindowFlags(Qt.WindowTitleHint)
            #self.win.setWindowFlags(Qt.WindowCloseButtonHint)
            p1 = self.win.addPlot(title=self.main_gui.results_widget.fig_ch[0].lineedit_name.text())

            p2 = self.win.addPlot(title=self.main_gui.results_widget.fig_ch[1].lineedit_name.text())
            
            while self.abort == 0:
               
                sizebuf = 10*no_samples
                data_counter = np.zeros(shape=[sizebuf])
                data_counter2 = np.zeros(shape=[sizebuf])
                self.tasks['Counter_tracker'].ReadCounterF64(sizebuf, -1,  data_counter,sizebuf,mx.byref(mx.int32(sizebuf)),None)
                self.tasks['Counter_tracker2'].ReadCounterF64(sizebuf, -1,  data_counter2, sizebuf,mx.byref(mx.int32(sizebuf)),None)
                QCoreApplication.processEvents()
              
                diffcounts = np.diff(data_counter)
                totalcounts = np.sum(diffcounts)
                counts_kcps = totalcounts/(sizebuf-1)/1000*(10*clock_rate)
                diffcounts2 = np.diff(data_counter2)
                totalcounts2 = np.sum(diffcounts2)
                counts_kcps2 = totalcounts2/(sizebuf-1)/1000*(10*clock_rate)
             
                tot.append(counts_kcps)
                tot2.append(counts_kcps2)
            
                ###### Choose only to show last X samples
                if len(tot) > self.update_after:
                
                    p1.plot(range(self.update_after), tot[-self.update_after:], pen='r', clear=True)
                    p1.setTitle(title = str(self.main_gui.results_widget.fig_ch[0].lineedit_name.text() + ' counts = ' + str("{:.3f}".format(np.mean( tot[-self.update_after:]))) + ' kcps'))
                    
                    p2.plot(range(self.update_after), tot2[-self.update_after:], pen='r', clear=True)
                    p2.setTitle(title = str(self.main_gui.results_widget.fig_ch[1].lineedit_name.text() + ' counts = ' + str("{:.3f}".format(np.mean( tot2[-self.update_after:]))) + ' kcps'))
                    
                else:
                        
                    p1.plot(range(len(tot)), tot, pen='r', clear=True)
                    p1.setTitle(title = str(self.main_gui.results_widget.fig_ch[0].lineedit_name.text() + ' counts = ' + str("{:.3f}".format(np.mean(tot))) + ' kcps'))
                     
                    p2.plot(range(len(tot2)), tot2, pen='r', clear=True)
                    p2.setTitle(title = str(self.main_gui.results_widget.fig_ch[1].lineedit_name.text() + ' counts = ' + str("{:.3f}".format(np.mean(tot2))) + ' kcps'))
                   

           
       
    def stop_count_continuously(self): 
        
        
        ###### DO something if the person tries to close the figure!!!!!!!!!!!
        
        #self.win.setAttribute(Qt.WA_DeleteOnClose,True)
        self.win.hide()
        self.win.deleteLater()
        
        self.abort = 1
      
        self.tasks['Counter_tracker'].StopTask()
        self.tasks['Counter_tracker'].ClearTask()
        
        self.tasks['Counter_tracker2'].StopTask()
        self.tasks['Counter_tracker2'].ClearTask()
        
        self.tasks['AI_clock'].StopTask()
        self.tasks['AI_clock'].ClearTask()
        
        self.main_gui.results_widget.fig_ch[0].lineedit_name.setEnabled(True)
        self.main_gui.results_widget.fig_ch[1].lineedit_name.setEnabled(True)
    '''
    Analog out
    '''
    def add_AO_lines(self, machine_name, task, fatalerror=True):
        # CreateAOVoltageChan ( const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, const char customScaleName[])
        task.CreateAOVoltageChan(machine_name, '', -self.logged_quantities['Max_beam_scan_voltage'].val, +self.logged_quantities['Max_beam_scan_voltage'].val, mx.DAQmx_Val_Volts, None)
       
    def load_AO_buffer(self, scan_pattern, fatalerror=True):
   
        buffer_size = self.no_pixels *  self.no_samples_per_pixel * self.no_frames
        
        self.tasks['AO_task'].WriteAnalogF64(mx.int32(buffer_size), self.autoStart, self.timeout, mx.DAQmx_Val_GroupByScanNumber, scan_pattern.astype(mx.float64),mx.byref(mx.int32(buffer_size)), None)
        self.tasks['AO_task'].WaitUntilTaskDone(self.timeout)
        
    '''
    Analog in
    '''
    def add_AI_lines(self, machine_name, task, fatalerror=True):
        # CreateAIVoltageChan( const char physicalChannel[], const char nameToAssignToChannel[], int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[])
        task.CreateAIVoltageChan(machine_name, '', mx.DAQmx_Val_Cfg_Default, -self.logged_quantities['Max_beam_scan_voltage'].val, +self.logged_quantities['Max_beam_scan_voltage'].val, mx.DAQmx_Val_Volts, '')
        
    def read_AI_buffer(self, buffersize, fatalerror=True):
        #instead of 2 below, count the number of analog in channels
        data_AIs = np.zeros(shape=[self.main_gui.results_widget.no_ai_channels * buffersize ])
        
        # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved)
        # BELOW, instead of  buffersize*2, replace 2 with how many analog channels i have
        self.tasks['AI_task'].ReadAnalogF64( buffersize, self.timeout, mx.DAQmx_Val_GroupByScanNumber, data_AIs, buffersize*self.main_gui.results_widget.no_ai_channels,mx.byref(mx.int32(buffersize)),None)
        #self.tasks['AI_task'].WaitUntilTaskDone(self.timeout) # gives weird error????
        
        # data_AIs also contains interleaved data, [x1, y1, x2, y2...]
        # Below, replace 2 with number of AI channels acquired
        self.data_AI = np.zeros(shape=[self.main_gui.results_widget.no_ai_channels, buffersize ])
        #Instead of 2 below, use number of AI channels
        for k in range(self.main_gui.results_widget.no_ai_channels):
            self.data_AI[k] = data_AIs[k::self.main_gui.results_widget.no_ai_channels]
        # Above, replace 2 in k::2 with no AI channels
    '''
    Counters
    '''
    def add_counter_line(self, machine_name, terminal_name, task, fatalerror=True):
        #CreateCICountEdgesChan (const char counter[], const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection)
        task.CreateCICountEdgesChan(machine_name, '', mx.DAQmx_Val_Rising, 0, mx.DAQmx_Val_CountUp)
        task.SetCICountEdgesTerm(machine_name, terminal_name)
        
    def read_counter_buffer(self, buffersizecounter, fatalerror=True):
        self.fac = self.int_clock_rate
        buffer_size =  buffersizecounter * self.fac
        self.data_counter = np.zeros(shape=[len(self.main_gui.UserConfig.names_counter_channels), buffersizecounter ])
        self.data_counter_time_resolved = np.zeros(shape=[len(self.main_gui.UserConfig.names_counter_channels), buffer_size  ])
        data_counters = np.zeros(shape=[int( buffer_size) ])
        
        # ReadAnalogF64( int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved)
        self.tasks['Counter1_task'].ReadCounterF64( mx.int32(buffer_size) , self.timeout,  data_counters, buffer_size,mx.byref(mx.int32(buffer_size)),None)
        
        newly = np.diff(data_counters)
        data_counterTR0 =  np.insert(newly,0,0)
        self.data_counter_time_resolved[0] =data_counterTR0
        
        #corrected
        data_countershlp=np.diff(data_counters)
        data_counters=np.insert(data_countershlp,0,0) #inset 0 point at beginning (index 0) to be able to take diff
        newarr = np.mean(data_counters.reshape(-1, int(self.fac)), axis=1)
        self.data_counter[0] = newarr
        
        ######################################

        data_counters = np.zeros(shape=[ int(buffer_size)]) 
        self.tasks['Counter2_task'].ReadCounterF64( mx.int32(buffer_size) , self.timeout, data_counters, buffer_size,mx.byref(mx.int32(buffer_size )),None)
        
        
        newly2 = np.diff(data_counters)
        data_counterTR =  np.insert(newly2,0,0)
        self.data_counter_time_resolved[1] =data_counterTR
        
        
        #corrected
        data_countershlp=np.diff(data_counters)
        data_counters=np.insert(data_countershlp,0,0) #inset 0 point at beginning (index 0) to be able to take diff
        newarr = np.mean(data_counters.reshape(-1, int(self.fac)), axis=1)
        self.data_counter[1] = newarr
        

    
    def my_msg_box(self,input_text):
       msgBox = QMessageBox()
       msgBox.setText(input_text)
       msgBox.exec_(); 
       
class NamedTask(mx.Task):
    ''' replaces __init__ with one that accepts a name for the task, otherwise identical to PyDaqmx task
        override PyDAQmx definition, which does not support named tasks
        no special chars in names, space OK
    '''
    def __init__(self, name= ''):
        self.taskHandle = mx.TaskHandle(0)
        mx.DAQmxCreateTask(name, mx.byref(self.taskHandle))

class MyPlot(pg.GraphicsWindow): #(pg.PlotWidget):
        def __init__(self,this_gui,title=None):
            super(MyPlot, self).__init__() # super() lets you avoid referring to the base class explicitly
        
            self.this_gui = this_gui
    
        def closeEvent(self, ev):
            if self.this_gui.abort == 0:
               self.this_gui.abort = 1
               self.this_gui.main_gui.results_widget.count_clicked()
                