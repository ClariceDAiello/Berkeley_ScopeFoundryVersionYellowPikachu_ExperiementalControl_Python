import time, serial

from collections import OrderedDict

from Hardware.hardware_component import HardwareComponent  

# Import helper functions
from HelperFunctions import *

class SEMZeiss(HardwareComponent):
    
    name = 'Microscope' # Needs to be given because of the hardware component structure; should match the line in set_hardware: from Hardware.SEM.sem_zeiss import SEMZeiss as *Microscope*
    
    def __init__(self, gui,main_gui):
        
        self.gui = gui
        
        HardwareComponent.__init__(self,self.gui)
        
        self.setup()

        self.connect()
        
        self.cont_read_is_done = True
        
    def setup(self):
        
        # Make serial connection 
#         self.ser = serial.Serial(port='COM4', 
#                                  baudrate=9600, 
#                                  bytesize= serial.EIGHTBITS, 
#                                  parity=serial.PARITY_NONE, 
#                                  stopbits=serial.STOPBITS_ONE,
#                                  timeout=0.1)
        
        # Create logged quantities; to each logged quantity there correspond one group of functions
        self.logged_quantities = OrderedDict() # Sort keys (or logged quantity names) by order at which they were declared
         
        self.add_logged_quantity('Pixel_size',
                                 dtype=float,
                                 ro=True,
                                 vmin=0.0,
                                 vmax=5.0e4 * 1e-9,
                                 unit='m',
                                 is_variable=False,
                                 displayFlag=True)
        
        self.add_logged_quantity('Magnification',
                                 dtype=float,
                                 ro=False,
                                 vmin=5.0,
                                 vmax=5.0e5,
                                 unit='x',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Beam_status',
                                 dtype=int,
                                 ro=False,
                                 vmin=1,
                                 vmax=2,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True,
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
        
        aperture_choices=list([('30.00 um',1),
                               ('10.00 um',2),
                               ('20.00 um',3),
                               ('60.00 um',4),
                               ('120.00 um',5),
                               ('300.00 um',6)])
           
        self.add_logged_quantity('Aperture_choice', 
                                 dtype=int,
                                 ro=False,
                                 vmin=1,
                                 vmax=6,
                                 unit='',
                                 is_variable=False, #CHANGE TO VARIABLE IN FUTURE
                                 displayFlag=True,
                                 choices=aperture_choices)
        
        self.add_logged_quantity('Probe_current', 
                                 dtype=float,
                                 ro=False,
                                 vmin=1.0e-14,
                                 vmax=2.0e-5,
                                 unit='A',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity('Working_distance',
                                 dtype=float,
                                 ro=False,
                                 vmin=0.0,
                                 vmax=121.0 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_x',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 152 * 1e-3,
                                 initial=50 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_y',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 152 * 1e-3,
                                 initial=50 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_z',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 40 * 1e-3,
                                 initial=30 * 1e-3,
                                 unit='m',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_tilt',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 90.0,
                                 initial=0.0,
                                 unit='deg',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.add_logged_quantity(name='Stage_rotation',
                                 dtype=float,
                                 ro=False,
                                 vmin= 0.0,
                                 vmax= 360.0,
                                 initial=0.0,
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
        
        self.add_logged_quantity('Vacuum',
                                 dtype=float,
                                 ro=True,
                                 vmin=1.8e-4,
                                 vmax=2e-8,
                                 unit='Torr',
                                 is_variable=False,
                                 displayFlag=True)
          
          
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
        print "Sending command ..." + str(cmd)
    
    def write_cmd(self,cmd):
        print "Writing command ..." + str(cmd)
#         if cmd[0:3] == 'EHT' or cmd[0:3] == 'RAT' or cmd[0:3] == 'MAG' or cmd[0:3] == 'FOC' or cmd[0:3] == 'STG' or cmd[0:3] == 'PIX':
#            return 12.3
#         elif cmd[0:3] == 'GUN' or cmd[0:3] == 'BBL' or cmd[0:3] == 'EXS' or cmd[0:3] == 'JDK':
#            return True
#         elif cmd[0:4] == 'BMON' or cmd[0:4] == 'ACST' or cmd[0:4] == 'ABGT': 
#            return 1
#         elif cmd[0:3] == 'APR' or cmd[0:3] == 'CST' or cmd[0:3] == 'BGT':
#            return 6
#         elif cmd[0:3] == 'PRB' or cmd[0:3] == 'VAC' or cmd[0:4] == 'PROB':
#            return 1.12e-5
#         elif cmd[0:3] == 'C95':
#            return '1 2 3 4 5 6'
#         elif cmd[0:3] == 'STI':
#            return '50 57'  
#         else:
#            print "COMMAND NOT RECOGNIZED: " + cmd
    
    def conv_resp(self,resp):
        '''
        The response from RemCon32 comes in two lines;
        the first line shows the status of the task, 
        thesecond line contains the parameter or error number
        '''
        cmd_status=resp[0][0]
        success=resp[1][0]
        if cmd_status=='@':
            if success=='>':
                if (len(resp[1])>3):
                    #output the requested value, if any
                    return resp[1][1:-2]
            else:
                if (len(resp[1])>3):
                    raise ValueError("RemCon32 command did not complete. Error Code: %s" % resp[1][1:-2])
                    self.my_msg_box("RemCon32 command did not complete. Error Code: %s" % resp[1][1:-2])
                else:
                    raise ValueError("RemCon32 command did not complete.")
                    self.my_msg_box("RemCon32 command did not complete. Error Code" )
        else:
            raise ValueError("Your RemCon32 command is invalid. Error Code: %s" % resp[1][1:-2])
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
              
    '''
    Vacuum
    '''
    def read_Vacuum(self):
        #eturn self.write_cmd('VAC?\r')
        return str(1e-8)
   
    '''
    Joystick
    '''
    def read_Joystick_enabled_status(self):
        #return self.write_cmd('JDK?\r')
        return str(1)
   
    def write_Joystick_enabled_status(self,val):
        # val == 0 ENABLES JOYSTICK
        # val == 1 DISABLES JOYSTICK    
        if val==0 or val==1:
            return self.write_cmd('JDK %i\r' % val)
        else:
            raise ValueError("Joystick disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val) 
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
   
    def read_Panel_enabled_status(self):
        #return self.write_cmd('JDK?\r')
        return str(1)
   
    def write_Panel_enabled_status(self,val):
        # val == 0 ENABLES JOYSTICK
        # val == 1 DISABLES JOYSTICK    
        if val==0 or val==1:
            return self.write_cmd('JDK %i\r' % val)
        else:
            raise ValueError("Joystick disable on/off value %f not 0 (= on) or 1 (= off). Aborted." % val) 
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")   
   
    '''
    Pixel size
    '''
    def read_Pixel_size(self):
        #return 1e-9 * self.write_cmd('PIX?\r')
        return str(12*1e-9)
   
    '''
    EHT
    '''
    def read_Beam_status(self):
        #return self.write_cmd('BMON?\r')
        return str(1)
   
    def write_Beam_status(self,val):
        if val>=1 and val<=2:
            return self.write_cmd('BMON %i\r' % val)
        else:
            raise ValueError("Beam on/off value %f not 1 (= on) or 2 (= off). Aborted." % val)
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
            # Value of 0 SHUTS DOWN THE GUN!!! and thus should not be employed  
    
    def read_EHT(self):
        #return self.write_cmd('EHT?\r')
        return 1e3* 1.33
    
    def write_EHT(self,val):
        if val/1e3 >= 0.0 and val/1e3 <= 40.0:
           return self.write_cmd('EHT %f\r' % float(val/1e3))
        else:
           return ValueError("EHT value %f kV out of range [0,40]kV. Aborted." % val)
           self.my_msg_box("RemCon32 command did not complete. Error Code: ")

    '''
    Beam Blanking
    '''
    def read_Beam_blanking_status(self):
        #return self.write_cmd('BBL?\r')
        return str(1)
    
    def write_Beam_blanking_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('BBLK %i\r' % val)
        else:
            raise ValueError("Blanking state is %s, should either be 0 (= off) or 1 (= on). Aborted." % val)
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    Stigmator
    '''
    def read_stigmator_all(self):
        #return self.write_cmd('STI?\r')
        return '33 34'
    
    def read_Stigmator_x(self):
        return self.read_stigmator_all()[0]
    
    def read_Stigmator_y(self):
        return self.read_stigmator_all()[1]
    
    def write_Stigmator_x(self,val_x):
        if (val_x>=-100.0 and val_x<=100.0):
            current_stig=self.read_stigmator_all().split(' ')
            current_stig[0] = str(val_x)
            current_stig = ' '.join(current_stig)
            self.send_cmd('STIG '+current_stig+'\r')
        else:
            raise ValueError("Stigmator_x value %f %% out of range [-100,100]%%. Aborted." % val) 
            self.my_msg_box("RemCon32 command did not complete. Error Code: ") 
        
    def write_Stigmator_y(self,val_y):
        if (val_y>=-100.0 and val_y<=100.0):
            current_stig=self.read_stigmator_all().split(' ')
            current_stig[1] = str(val_y)
            current_stig = ' '.join(current_stig)
            self.send_cmd('STIG '+current_stig+'\r')
        else:
            raise ValueError("Stigmator_y value %f %% out of range [-100,100]%%. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    Brightness
    '''
    def read_Auto_brightness_status(self):
        #return self.write_cmd('ABGT?\r')      
        return str(1)
       
    def write_Auto_brightness_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('ABGT %i\r' % val)
        else:
            raise ValueError("Auto brightness on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
       
    def read_Brightness(self):
        #return self.write_cmd('BGT?\r')
        return str(35)
    
    def write_Brightness(self,val):
        if val>=0.0 and val<=100.0:
            return self.write_cmd('BRGT %f\r' % val)
        else:
            raise ValueError("Brightness value %f %% out of range [0,100]%%. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    Contrast
    '''
    def read_Auto_contrast_status(self):
        #return self.write_cmd('ACST?\r') 
        return str(1)  
       
    def write_Auto_contrast_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('ACST %i\r' % val)
        else:
            raise ValueError("Auto contrast on/off value %f not 0 (= off) or 1 (= on). Aborted." % val)    
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
       
    def read_Contrast(self):
        #return self.write_cmd('CST?\r')
        return str(56)
    
    def write_Contrast(self,val):
        if val>=0.0 and val<=100.0:
            return self.write_cmd('CRST %f\r' % val)
        else:
            raise ValueError("Contrast value %f %% out of range [0,100]%%. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
     
    '''
    Magnification
    '''
    def read_Magnification(self):
        #return self.write_cmd('MAG?\r')
        return 1234
    
    def write_Magnification(self, val):
        if val>=5.0 and val<=500e3:
            return self.write_cmd('MAG %f\r' % val)
        else:
            raise ValueError("Magnification value %f out of range [5,500e3]. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
    
    '''
    Working distance
    '''
    def read_Working_distance(self):
        #return 1e-3 * self.write_cmd('FOC?\r')
        return 1e-3 * 80
    
    def write_Working_distance(self,val):
        if val*1e3>=0.0 and val*1e3<=121.0:
            return self.write_cmd('FOCS %f\r' % float(val*1e3))
        else:
            raise ValueError("Working distance value %f out of range [0,121]mm. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    External Scan
    '''
    def read_External_scan_enabled_status(self):
        #return self.write_cmd('EXS?\r')
        return str(1)
    
    def write_External_scan_enabled_status(self,val):
        if val==0 or val==1:
            return self.write_cmd('EDX %i\r' % val)
        else:
            raise ValueError("External scan state is %s, should either be 0 (= refuse) or 1 (= accept). Aborted." % val)
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    Probe Current
    '''
    def read_Probe_current(self):
        #return self.write_cmd('PRB?\r')
        return str(1e-5)
    
    def write_Probe_current(self,val):
        if val>=1.0e-14 and val<=2.0e-5:
            return self.write_cmd('PROB %f\r' % val)
        else:
            raise ValueError("Probe current value %f out of range [1e-14,2e-5]A. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    '''
    Aperture
    '''
    def read_Aperture_choice(self):
        #return self.write_cmd('APR?\r')
        return str(4)
    
    def write_Aperture_choice(self,val):
        if val>=1 and val<=6:
            return self.write_cmd('APER %i\r' % val)
        else:
            raise ValueError("Aperture choice value %f out of range [1,6]. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
    
    '''
    Stage
    '''
    def read_stage_all(self):
        #return self.write_cmd('C95?\r')   
        # Output:  x y z t r m move_status
        # Units: mm mm mm deg deg ? ? ?
        return '30 40 10 45 345 1 2 3'
       
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
        if val_x*1e3>=0.0 and val_x*1e3<=152.0:
            current_pos=self.read_stage_all().split(' ')
            current_pos[0] = str(val_x*1e3)
            current_pos = ' '.join(current_pos)
            time.sleep(0.05)
            self.send_cmd('C95 '+current_pos+'\r')
            time.sleep(0.2)
        else:
            raise ValueError("stage_x value %f out of range [0,152]mm. Aborted." % val*1e3)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
    
    def write_Stage_y(self,val_y):
        if val_y*1e3>=0.0 and val_y*1e3<=152.0:
            current_pos=self.read_stage_all().split(' ')
            current_pos[1] = str(val_y*1e3)
            current_pos = ' '.join(current_pos)
            time.sleep(0.05)
            self.send_cmd('C95 '+current_pos+'\r')
            time.sleep(0.2)
        else:
            raise ValueError("stage_y value %f out of range [0,152]mm. Aborted." % val*1e3)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
            
    def write_Stage_z(self,val_z):
        if val_z*1e3>=0.0 and val_z*1e3<=40.0:
            current_pos=self.read_stage_all().split(' ')
            current_pos[2] = str(val_z*1e3)
            current_pos = ' '.join(current_pos)
            time.sleep(0.05)
            self.send_cmd('C95 '+current_pos+'\r')
            time.sleep(0.2)
        else:
            raise ValueError("stage_z value %f out of range [0,40]mm. Aborted." % val*1e3)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
            
    def write_Stage_tilt(self,val_t):
        if val_t>=0.0 and val_t<=90.0:
            current_pos=self.read_stage_all().split(' ')
            current_pos[3] = str(val_t)
            current_pos = ' '.join(current_pos)
            time.sleep(0.05)
            self.send_cmd('C95 '+current_pos+'\r')
            time.sleep(0.2)
        else:
            raise ValueError("stage_tilt value %f out of range [0,90]deg. Aborted." % val) 
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
        
    def write_Stage_rotation(self,val_r):
        if val_r>=0.0 and val_r<=360.0:
            current_pos=self.read_stage_all().split(' ')
            current_pos[4] = str(val_r)
            current_pos = ' '.join(current_pos)
            time.sleep(0.05)
            self.send_cmd('C95 '+current_pos+'\r')
            time.sleep(0.2)
        else:
            raise ValueError("stage_rotation value %f out of range [0,360]deg. Aborted." % val)  
            self.my_msg_box("RemCon32 command did not complete. Error Code: ")
         
    '''
    Close serial - not currently used
    '''  
    def close(self):
        self.ser.close()