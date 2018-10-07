import sys, time, serial
from PySide.QtCore import *
from PySide.QtGui  import *

from collections import OrderedDict

from Hardware.hardware_component import HardwareComponent  

# Import helper functions
from HelperFunctions import *

class SEMZeiss(HardwareComponent):
    
    name = 'Microscope' # Needs to be given because of the hardware component structure; should match the line in set_hardware: from Hardware.SEM.sem_zeiss import SEMZeiss as *Microscope*
    
    def __init__(self, gui,main_gui):
        
        self.gui = gui
        self.main_gui = main_gui
        
        HardwareComponent.__init__(self,self.gui)
        
        #self.setup()

        self.connect()
        
        self.cont_read_is_done = True
        #self.continuously_read_from_hardware(self.main_gui.scan_widget.start_is_on)
        
    def continuously_read_from_hardware(self,start_is_on):
        pass
        
#                 #QApplication.processEvents() 
#         
#                 print "inside loop!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             #try:
#                 
#                 if not start_is_on:
#                     self.cont_read_is_done = False
#                     for quantity in self.logged_quantities.keys():
#                         self.logged_quantities[quantity].hardware_read_func()
#                     #QApplication.processEvents() 
#                     self.cont_read_is_done = True
#            # finally:
#               #  QTimer.singleShot(5000, self.continuously_read_from_hardware(self.main_gui.scan_widget.start_is_on))
#               #  QApplication.processEvents() 
              
#             QCoreApplication.processEvents() 
#         
#             print "inside loop!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
#             try:
#                 
#                 if not start_is_on:
#                     self.cont_read_is_done = False
#                     for quantity in self.logged_quantities.keys():
#                         self.logged_quantities[quantity].hardware_read_func()
#                     QCoreApplication.processEvents() 
#                     self.cont_read_is_done = True
#             finally:
#                 QTimer.singleShot(5000, self.continuously_read_from_hardware(self.main_gui.scan_widget.start_is_on))
#                 QCoreApplication.processEvents() 
#         
                
    def setup(self):
        
        # Make serial connection 
        self.ser = serial.Serial(port='COM4', 
                                 baudrate=9600, 
                                 bytesize= serial.EIGHTBITS, 
                                 parity=serial.PARITY_NONE, 
                                 stopbits=serial.STOPBITS_ONE,
                                 timeout=0.1)
        
        #self.ser = serial.Serial('COM4',9600,timeout=0)
        #self.ser.open()
        
        # Create logged quantities; to each logged quantity there correspond one group of functions
        self.logged_quantities = OrderedDict() # Sort keys (or logged quantity names) by order at which they were declared
         
        self.add_logged_quantity('Pixel_size',
                                 dtype=float,
                                 ro=True,
                                 vmin=0.0,
                                 vmax=5.0e4 * 1e-9,
                                 unit='m',
                                 is_variable=False,
                                 displayFlag=False)
        
        self.add_logged_quantity('Magnification',
                                 dtype=float,
                                 ro=False,
                                 vmin=5.0,
                                 vmax=5.0e5,
                                 unit='X',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Beam_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=1,
                                 vmax=2,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=False,
                                 choices=[('Off',2),('On',1)])
        
        self.add_logged_quantity('Beam_blanking_status', 
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',0),('On',1)])
        
        self.add_logged_quantity('EHT',
                                 dtype=float,
                                 ro=False,
                                 vmin=0.0,
                                 vmax=40.0 * 1e3,
                                 unit='V',
                                 is_variable=True,
                                 displayFlag=True)
        
        aperture_choices=list([('30 um',1),
                               ('10 um',2),
                               ('20 um',3),
                               ('60 um',4),
                               ('120 um',5),
                               ('300 um',6)])
           
        self.add_logged_quantity('Aperture_choice', 
                                 dtype=int,
                                 ro=False,
                                 vmin=1,
                                 vmax=6,
                                 unit='',
                                 is_variable=False, #CHANGE TO VARIABLE IN FUTURE
                                 displayFlag=True,
                                 choices=aperture_choices)
        
#         self.add_logged_quantity('Probe_current', 
#                                  dtype=float,
#                                  ro=True,
#                                  vmin=1.0e-14,
#                                  vmax=2.0e-5,
#                                  unit='A',
#                                  is_variable=True,
#                                  displayFlag=True)
        
        #Manual of OptiProbe says: 12pA to 40nA
        # READ ONLY FOR THE TIME BEING
        self.add_logged_quantity('Probe_current', 
                                 dtype=float,
                                 ro=True,
                                 vmin=12.0e-12,
                                 vmax=40.0e-9,
                                 unit='A',
                                 is_variable=False,
                                 displayFlag=True)
        
        self.add_logged_quantity('High_current_enabled_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',0),('On',1)])
        
        self.add_logged_quantity('Working_distance',
                                 dtype=float,
                                 ro=True,
                                 vmin= 1.0 * 1e-3, # could have been set to anything
                                 vmax=121.0 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_x',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 152 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_y',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 152 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_z',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 45.4 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_tilt',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 90.0,
                                 unit='deg',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_rotation',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 360.0,
                                 unit='deg',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Stigmator_x',
                                 dtype=float,
                                 ro=False,
                                 vmin=-100.0,
                                 vmax=100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
         
        self.add_logged_quantity('Stigmator_y', 
                                 dtype=float,
                                 ro=False,
                                 vmin=-100.0,
                                 vmax=100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Auto_contrast_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',0),('On',1)])
        
        self.add_logged_quantity('Contrast', 
                                 dtype=float,
                                 ro=False,
                                 vmin=0.0,
                                 vmax=100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Auto_brightness_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',0),('On',1)])
        
        self.add_logged_quantity('Brightness', 
                                 dtype=float,
                                 ro=False,
                                 vmin=0.0,
                                 vmax=100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('External_scan_enabled_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=False,
                                 choices=[('Off',0),('On',1)])
        
        self.add_logged_quantity('Vacuum_chamber',
                                 dtype=float,
                                 ro=True,
                                 vmin=1.8e-4,
                                 vmax=2e-8,
                                 unit='Pa(?)',
                                 is_variable=False,
                                 displayFlag=True)
        
        self.add_logged_quantity('Vacuum_gun',
                         dtype=float,
                         ro=True,
                         vmin=1.8e-4,
                         vmax=2e-8,
                         unit='mbar(?)',
                         is_variable=False,
                         displayFlag=True)
        
        self.add_logged_quantity('Joystick_enabled_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',1),('On',0)])
        
        self.add_logged_quantity('Panel_enabled_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=0,
                                 vmax=1,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
                                 choices=[('Off',1),('On',0)])
        
        # The Macros need to be called REMCONx, where x is an integer
        # Run the "dual channel" macro - saved in SmartSEM/Distrib
        #self.write_cmd('MAC REMCON1 \r')
        self.ser.flushInput()
        self.send_cmd('MAC REMCON1 \r')
        
        #time.sleep(3) # needed otherwise crashes
        # Run the "optiprobe on" macro - saved in SmartSEM/Distrib
        #self.send_cmd('MAC REMCON2 \r')
        
        #### Maybe want here to turn high current on????????????????????
       
          
    def connect(self):
        
        # Connect logged quantities to hardware
        for quantity in self.logged_quantities.keys():
            self.logged_quantities[quantity].hardware_read_func = eval('self.read_' + quantity)
            if not self.logged_quantities[quantity].ro:
                self.logged_quantities[quantity].hardware_set_func = eval('self.write_' + quantity)
     
    def my_msg_box(self,input_text):
        msgBox = QMessageBox()
        msgBox.setText(input_text)
        msgBox.exec_(); 
        
    def send_cmd(self,cmd):
        self.ser.flushOutput()
        self.ser.write(cmd)
    
    def write_cmd(self,cmd):
        self.ser.flushInput()
        self.send_cmd(cmd)
        time.sleep(0.5) #was 0.5
        resp=self.ser.readlines()  
        time.sleep(0.5)
        return self.conv_resp(resp)
    
    def conv_resp(self,resp):
        
        '''
        The response from RemCon32 comes in two lines;
        the first line shows the status of the task, 
        thesecond line contains the parameter or error number
        '''
        cmd_status=resp[0][0]
        #print cmd_status
        
        #if len(resp) > 1: #len(resp) always > 1 because of \r\n characters
        
        success=resp[1][0]
        print success
        if cmd_status=='@':
            if success=='>':
                #pass
               # if (len(resp[1])>3):
                    #output the requested value, if any
                   # print resp[1][1:-2]
                return resp[1][1:-2]
            else:
                if (len(resp[1])>3):   
                    print resp   
                    raise ValueError("RemCon32 command did not complete. Error Code: %s" % resp[1][1:-2])
                    self.my_msg_box("RemCon32 command did not complete. Error Code: %s" % resp[1][1:-2])
                else:
                    print resp
                    raise ValueError("RemCon32 command did not complete.")
                    self.my_msg_box("RemCon32 command did not complete.")
        else:
            raise ValueError("Your RemCon32 command is invalid. Error Code: %s" % resp[1][1:-2])
            self.my_msg_box("Your RemCon32 command is invalid. Error Code: %s" % resp[1][1:-2])
                  
#         else:
#             if cmd_status=='@':
#                 return 'ok'
#             elif cmd_status=='#':
#                 raise ValueError("RemCon32 command did not complete and returned dial symbol.")
#                 self.my_msg_box("RemCon32 command did not complete and returned dial symbol.") 
        
    '''
    Vacuum
    '''
    def read_Vacuum_chamber(self):
        return self.write_cmd('VAC?\r').split(" ")[0]
    
    def read_Vacuum_gun(self):
        return self.write_cmd('VAC?\r').split(" ")[1]
   
    '''
    Joystick
    '''
    def read_Joystick_enabled_status(self):
        return self.write_cmd('JKD?\r')
   
    def write_Joystick_enabled_status(self,val):
        # val == 0 ENABLES JOYSTICK
        # val == 1 DISABLES JOYSTICK    
        if val==0 or val==1:
            return self.write_cmd('JKD %i\r' % val)
        else:
            raise ValueError("Joystick disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val) 
            self.my_msg_box("Joystick disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val)
            
    '''
    Panel
    '''
    def read_Panel_enabled_status(self):
        return self.write_cmd('HPD?\r')
   
    def write_Panel_enabled_status(self,val):
        # val == 0 ENABLES PANEL
        # val == 1 DISABLES PANEL   
        if val==0 or val==1:
            return self.write_cmd('HPD %i\r' % val)
        else:
            raise ValueError("Panel disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val) 
            self.my_msg_box("Panel disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val)
   
    '''
    Pixel size
    '''
    def read_Pixel_size(self):
        return str(eval('1e-9 *' + self.write_cmd('PIX?\r')))
   
    '''
    EHT
    '''
    def read_Beam_status(self):
        status = self.write_cmd('EHT?\r')
        if status <= sys.float_info.epsilon:
            return 0 # If EHT is zero, beam is off
        else:
            return 1
   
    def write_Beam_status(self,val):
        if val>=1 and val<=2:
            return self.write_cmd('BMON %i\r' % val)
        else:
            raise ValueError("Beam on/off value %f not 1 (= on) or 2 (= off). Aborted." % val)
            self.my_msg_box("Beam on/off value %f not 1 (= on) or 2 (= off). Aborted." % val)
            # Value of 0 SHUTS DOWN THE GUN!!! and thus should not be employed  
    
    def read_EHT(self):
        return str(eval('1e3 * ' + self.write_cmd('EHT?\r')))
    
    def write_EHT(self,val):
        if val >= self.logged_quantities['EHT'].vmin and val <= self.logged_quantities['EHT'].vmax:
            return self.write_cmd('EHT %f\r' % float(val/1e3))
        else:
            return ValueError("EHT value %f kV out of range [0,40]kV. Aborted." % float(val/1e3))
            self.my_msg_box("EHT value %f kV out of range [0,40]kV. Aborted." % float(val/1e3))

    '''
    Beam Blanking
    '''
    def read_Beam_blanking_status(self):
        return self.write_cmd('BBL?\r')
    
    def write_Beam_blanking_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('BBLK %i\r' % val)
        else:
            raise ValueError("Blanking state is %s, should either be 0 (= off) or 1 (= on). Aborted." % val)
            self.my_msg_box("Blanking state is %s, should either be 0 (= off) or 1 (= on). Aborted." % val)
        
    '''
    Stigmator
    '''
    def read_stigmator_all(self):
        return self.write_cmd('STI?\r') 
    
    def read_Stigmator_x(self):
        return self.read_stigmator_all().split("  ")[0] # NOTE: 2 spaces necessary!
    
    def read_Stigmator_y(self):
        return self.read_stigmator_all().split("  ")[1]
    
    def write_Stigmator_x(self,val_x):
        if (val_x>=self.logged_quantities['Stigmator_x'].vmin and val_x<=self.logged_quantities['Stigmator_x'].vmax):
            current_stig=self.read_stigmator_all().split("  ")
            current_stig[0] = str(val_x)
            stig = "  ".join(current_stig)
            time.sleep(0.05)
            self.send_cmd('STIM '+stig+'\r') # Manual says STIG, only STIM works
            time.sleep(0.2)
        else:
            raise ValueError("Stigmator_x value %f %% out of range [-100,100]%%. Aborted." % val) 
            self.my_msg_box("Stigmator_x value %f %% out of range [-100,100]%%. Aborted." % val) 
        
    def write_Stigmator_y(self,val_y):
        if (val_y>=self.logged_quantities['Stigmator_y'].vmin and val_y<=self.logged_quantities['Stigmator_y'].vmax):
            current_stig=self.read_stigmator_all().split("  ")
            current_stig[1] = str(val_y)
            stig = "  ".join(current_stig)
            self.send_cmd('STIM '+stig+'\r')
        else:
            raise ValueError("Stigmator_y value %f %% out of range [-100,100]%%. Aborted." % val)  
            self.my_msg_box("Stigmator_y value %f %% out of range [-100,100]%%. Aborted." % val)
        
    '''
    Brightness
    '''
    def read_Auto_brightness_status(self):
        status = self.write_cmd('ABC?\r')
        if int(status) == 0 or int(status) == 2:
            return 0 # auto brightness off
        elif int(status) == 1 or int(status) == 3:
            return 1
       
    def write_Auto_brightness_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('ABGT %i\r' % val)
        else:
            raise ValueError("Auto brightness on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)  
            self.my_msg_box("Auto brightness on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)
       
    def read_Brightness(self):
        return self.write_cmd('BGT?\r')
    
    def write_Brightness(self,val):
        if val>=self.logged_quantities['Brightness'].vmin and val<=self.logged_quantities['Brightness'].vmax:
            return self.write_cmd('BRGT %f\r' % val)
        else:
            raise ValueError("Brightness value %f %% out of range [0,100]%%. Aborted." % val)  
            self.my_msg_box("Brightness value %f %% out of range [0,100]%%. Aborted." % val)
        
    '''
    Contrast
    '''
    def read_Auto_contrast_status(self):
        time.sleep(5)
        status = self.write_cmd('ABC?\r')
        time.sleep(5)
        if int(status) == 0 or int(status) == 1:
            return 0 # auto contrast off
        elif int(status) == 2 or int(status) == 3:
            return 1
       
    def write_Auto_contrast_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('ACST %i\r' % val)
        else:
            raise ValueError("Auto contrast on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)  
            self.my_msg_box("Auto contrast on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)  
       
    def read_Contrast(self):
        time.sleep(1)
        return self.write_cmd('CST?\r')
        time.sleep(1)
    
    def write_Contrast(self,val):
        if val>=self.logged_quantities['Contrast'].vmin and val<=self.logged_quantities['Contrast'].vmax:
            return self.write_cmd('CRST %f\r' % val)
        else:
            raise ValueError("Contrast value %f %% out of range [0,100]%%. Aborted." % val) 
            self.my_msg_box("Contrast value %f %% out of range [0,100]%%. Aborted." % val) 
     
    '''
    Magnification
    '''
    def read_Magnification(self):
        return self.write_cmd('MAG?\r')
    
    def write_Magnification(self, val):
        if val>=self.logged_quantities['Magnification'].vmin and val<=self.logged_quantities['Magnification'].vmax:
            return self.write_cmd('MAG %f\r' % val)
        else:
            raise ValueError("Magnification value %f out of range [5,500e3]. Aborted." % val)  
            self.my_msg_box("Magnification value %f out of range [5,500e3]. Aborted." % val)
    
    '''
    Working distance
    '''
    def read_Working_distance(self):
        return str(eval('1e-3 *' + self.write_cmd('FOC?\r')))
    
    def write_Working_distance(self,val):
        if val >=self.logged_quantities['Working_distance'].vmin and val<=self.logged_quantities['Working_distance'].vmax:
            return self.write_cmd('FOCS %f\r' % float(val*1e3))
        else:
            raise ValueError("Working distance value %f out of range [0,121]mm. Aborted." % float(val*1e3))  
            self.my_msg_box("Working distance value %f out of range [0,121]mm. Aborted." % float(val*1e3))
        
    '''
    External Scan
    '''
    def read_External_scan_enabled_status(self):
        return self.write_cmd('EXS?\r')
    
    def write_External_scan_enabled_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('EDX %i\r' % val)
        else:
            raise ValueError("External scan state is %s, should either be 0 (= refuse) or 1 (= accept). Aborted." % val)
            self.my_msg_box("External scan state is %s, should either be 0 (= refuse) or 1 (= accept). Aborted." % val)
        
    '''
    Probe Current
    '''
    def read_Probe_current(self):
        return self.write_cmd('PRB?\r') #12*1e-12 #DUMMMYYYYYYYY #self.write_cmd('PRB?\r')
    
    def write_Probe_current(self,val):
        # value is in pA
        # Hack - range of current is 12pA to 40nA
        # There is one MACRO per pA,
        # from REMCON12 to REMCON40000
        # Call the correct one
         if val>=self.logged_quantities['Probe_current'].vmin*1e12 and val<=self.logged_quantities['Probe_current'].vmax*1e12:
             pass
              #return self.write_cmd('MAC REMCON' + str(val) + '\r')
         else:
             raise ValueError("Probe current value %f out of range [12,40000]pA. Aborted." % val)  
             self.my_msg_box("Probe current value %f out of range [12,40000]pA. Aborted." % val)   
    
    # DOES NOT EXIST FOR SUPRA, see last table in remcon manual
#     def write_Probe_current(self,val):
#         if val>=self.logged_quantities['Probe_current'].vmin and val<=self.logged_quantities['Probe_current'].vmax:
#             time.sleep(0.05)
#             return self.write_cmd('PROB %f\r' % val)
#             time.sleep(0.2)
#         else:
#             raise ValueError("Probe current value %f out of range [1e-14,2e-5]A. Aborted." % val)  
#             self.my_msg_box("Probe current value %f out of range [1e-14,2e-5]A. Aborted." % val)
      
    def read_High_current_enabled_status(self):
        time.sleep(1)
        return self.write_cmd('HCM?\r')
        time.sleep(1)
    
    def write_High_current_enabled_status(self,val):
        ######## Won't set it!!!!!!!
        pass
#         if val==0 or val==1:
#             return self.write_cmd('HCM %i\r' % val)
#         else:
#             raise ValueError("High current state is %s, should either be 0 (= off) or 1 (= on). Aborted." % val)
#             self.my_msg_box("High current state is %s, should either be 0 (= off) or 1 (= on). Aborted." % val)  
#         
    '''
    Aperture
    '''
    def read_Aperture_choice(self):
        return self.write_cmd('APR?\r')
    
    def write_Aperture_choice(self,val):
        if val>=1 and val<=6:
            return self.write_cmd('APER %i\r' % val)
        else:
            raise ValueError("Aperture choice value %f out of range [1,6], corresponding to [30,10,20,60,120,300]um. Aborted." % val)  
            self.my_msg_box("Aperture choice value %f out of range [1,6], corresponding to [30,10,20,60,120,300]um. Aborted." % val)
    
    '''
    Stage
    '''
    def read_stage_all(self):
        return self.write_cmd('C95?\r')   
        # Output:  x y z t r m move_status
        # Units: mm mm mm deg deg ? ? ?
       
    def read_Stage_x(self):
        return str(eval('1e-3 *' + self.read_stage_all().split(' ')[0]))
        
    def read_Stage_y(self):
        return str(eval('1e-3 *' + self.read_stage_all().split(' ')[1]))
    
    def read_Stage_z(self):
        return str(eval('1e-3 *' + self.read_stage_all().split(' ')[2]))
    
    def read_Stage_tilt(self):
        return self.read_stage_all().split(' ')[3]
    
    def read_Stage_rotation(self):
        return self.read_stage_all().split(' ')[4]
    
    def write_Stage_x(self,val_x):
        if val_x>=self.logged_quantities['Stage_x'].vmin and val_x<=self.logged_quantities['Stage_x'].vmax:
            current_pos=self.read_stage_all().split(' ')
            current_pos[0] = str(val_x*1e3)
            pos = ' '.join(current_pos[0:-1]) #remove last element
            time.sleep(0.05)
            self.send_cmd('C95 '+pos+'\r')
            time.sleep(3) #Remcon manual p.12 says to wait 1sec after sending move command was 1
        else:
            raise ValueError("Stage_x value %f out of range [0,152]mm. Aborted." % float(1e3*val_x))
            self.my_msg_box("Stage_x value %f out of range [0,152]mm. Aborted." % float(1e3*val_x))
    
    def write_Stage_y(self,val_y):
        print "!!!!! Writing Stage_y to " + str(val_y)
        if val_y>=self.logged_quantities['Stage_y'].vmin and val_y<=self.logged_quantities['Stage_y'].vmax:
            current_pos=self.read_stage_all().split(' ')
            current_pos[1] = str(val_y*1e3)
            pos = ' '.join(current_pos[0:-1]) #remove last element
            time.sleep(0.05)
            self.send_cmd('C95 '+pos+'\r')
            time.sleep(3)
        else:
            raise ValueError("Stage_y value %f out of range [0,152]mm. Aborted." % float(1e3*val_y))  
            self.my_msg_box("Stage_y value %f out of range [0,152]mm. Aborted." % float(1e3*val_y))
            
    def write_Stage_z(self,val_z):
        if val_z>=self.logged_quantities['Stage_z'].vmin and val_z<=self.logged_quantities['Stage_z'].vmax:
            current_pos=self.read_stage_all().split(' ')
            current_pos[2] = str(val_z*1e3)
            pos = ' '.join(current_pos[0:-1]) #remove last element)
            time.sleep(0.05)
            self.send_cmd('C95 '+pos+'\r')
            time.sleep(3)
        else:
            raise ValueError("Stage_z value %f out of range [0,40]mm. Aborted." % float(1e3*val_z))  
            self.my_msg_box("Stage_z value %f out of range [0,40]mm. Aborted." % float(1e3*val_z))
            
    def write_Stage_tilt(self,val_t):
        if val_t>=self.logged_quantities['Stage_tilt'].vmin and val_t<=self.logged_quantities['Stage_tilt'].vmax:
            current_pos=self.read_stage_all().split(' ')
            current_pos[3] = str(val_t)
            pos = ' '.join(current_pos[0:-1]) #remove last element)
            time.sleep(0.05)
            self.send_cmd('C95 '+pos+'\r')
            time.sleep(3)
        else:
            raise ValueError("Stage_tilt value %f out of range [0,90]deg. Aborted." % val) 
            self.my_msg_box("Stage_tilt value %f out of range [0,90]deg. Aborted." % val)
        
    def write_Stage_rotation(self,val_r):
        if val_r>=self.logged_quantities['Stage_rotation'].vmin and val_r<=self.logged_quantities['Stage_rotation'].vmax:
            current_pos=self.read_stage_all().split(' ')
            current_pos[4] = str(val_r)
            pos = ' '.join(current_pos[0:-1]) #remove last element)
            time.sleep(0.05)
            self.send_cmd('C95 '+pos+'\r')
            time.sleep(3)
        else:
            raise ValueError("Stage_rotation value %f out of range [0,360]deg. Aborted." % val)  
            self.my_msg_box("Stage_rotation value %f out of range [0,360]deg. Aborted." % val)
         
    '''
    Close serial - not currently used
    '''  
    def close(self):
        self.ser.close()