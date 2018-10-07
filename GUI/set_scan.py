'''
Scan widget inside SEMGUI
'''

import sys, os, time, importlib, re
import h5py
import math
import numpy as np
import pyqtgraph as pg

# To parse xml sequence file
import xml.etree.ElementTree as ET 

from datetime import datetime
from collections import OrderedDict

from PySide.QtCore import *
from PySide.QtGui  import *

# Import helper functions
from HelperFunctions import *

# Import all available sequence commands, in a way that classes can be used without needing to call the .py module names
# I know 'explicit is better than implicit'; this is a conscious choice in order to make the sequencee building easier to the user
##########################################
from Measurement.measurement_component import MeasurementComponent  

module_filenames = os.listdir(os.path.abspath('../Measurement/SequenceCommands/'))
for module_name in module_filenames:

    if not(module_name == '__init__.py') and module_name[-3:] == '.py':

        exec('from Measurement.SequenceCommands.' + module_name.split('.py')[0] + ' import *')
        
module_filenames = os.listdir(os.path.abspath('../Measurement/BeamScanShapes/'))
for module_name in module_filenames:

    if not(module_name == '__init__.py') and module_name[-3:] == '.py':

        exec('from Measurement.BeamScanShapes.' + module_name.split('.py')[0] + ' import *')
##########################################
 
class SetScanWidget(QWidget):
    
    def __init__(self,main_gui):
        super(SetScanWidget, self).__init__() 
        
        self.main_gui = main_gui
        
        self.layout = QGridLayout(self)

        button_row_number = 0 #just to make it easy to create more things inside the widget
        
        # Define the Measurement Widget; this is used in Measurement Component class
        self.ui = my_ui()
        
        self.label_measurement = QLabel('Measurement sequence', self)
        font = QFont("Sans Serif", 12, QFont.Bold)
        self.label_measurement.setFont(font)
        self.layout.addWidget(self.label_measurement,button_row_number,0)
        button_row_number += 1
        
        # Define scrollArea
        self.scrollArea_measurement = QScrollArea()
        self.scrollArea_measurement.setWidgetResizable(True)
        self.scrollArea_measurement.setWidget(self.ui.measurement_tab_scrollArea_content_widget)
        # Make the scroll area as wide as the widget
        self.scrollArea_measurement.setMinimumWidth(10+self.sizeHint().width()) 
        self.scrollArea_measurement.setMinimumHeight(600+self.sizeHint().height())  
        self.layout.addWidget(self.scrollArea_measurement, button_row_number, 0,8,4)
        button_row_number += 8

        self.button_load_image_sequence = QPushButton('Load image sequence', self)
        self.button_load_image_sequence.clicked.connect(lambda: self.load_image_sequence_clicked())
        self.layout.addWidget(self.button_load_image_sequence,button_row_number,0,1,2) 
        
        self.button_load_other = QPushButton('Load other sequence', self)
        self.button_load_other.clicked.connect(lambda: self.load_other_clicked())
        self.layout.addWidget(self.button_load_other,button_row_number,2,1,1) #was2 first number
        
        self.button_edit_other = QPushButton('Edit current sequence', self)
        self.button_edit_other.clicked.connect(lambda: self.edit_other_clicked())
        self.layout.addWidget(self.button_edit_other,button_row_number,3,1,1)    #was3 first number  
        button_row_number += 1
 
        self.textedit_comments = QTextEdit('Comments:', self)
        self.textedit_comments.setFixedHeight(50)
        self.layout.addWidget(self.textedit_comments,button_row_number,0,2,3)     
        self.plot_scan = pg.PlotWidget() #QWidget()
        self.layout.addWidget(self.plot_scan,button_row_number,3,4,1)   
        x = np.random.normal(size=1000)
        self.plot_scan.plot(x, x, pen=None, symbol='o')# = pg.plot(title='try')    
        
        button_row_number += 2 
         
        self.button_start = QPushButton('Start', self)
        self.layout.addWidget(self.button_start,button_row_number,0,1,1)
        self.button_start.setEnabled(False)
        self.button_start.clicked.connect(lambda: self.start_clicked())
 
        self.button_stop = QPushButton('Stop', self)
        self.layout.addWidget(self.button_stop,button_row_number,1,1,2)
        self.button_stop.setEnabled(False)
        self.button_stop.clicked.connect(lambda: self.stop_clicked())
        button_row_number += 1
          
        self.progressbar = QProgressBar()
        self.layout.addWidget(self.progressbar,button_row_number,0,1,3)    
        
        #self.layout.setColumnStretch(1)
        self.setLayout(self.layout)
        
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))    
        
        self.load_image_sequence_clicked() # by default, load the standard image sequence
        #self.button_start.setEnabled(True) # why didnt load image sequence turn it on?
        
        self.start_is_on = False
        
    def edit_other_clicked(self):
        
        os.system('start notepad++ ' + self.sequencepath)    
        
    def load_other_clicked(self):
        
        dir_ops = directory_operations.DirectoryOperations();
        self.sequencepath = dir_ops.select_file_within_preferred_tree(self.main_gui.userdirectory_slash + os.sep + 'SavedSequences','Choose your sequence file (.xml)', 'xml', 'Your user sequence file lives within the SavedSequences folder! ')
        if not self.sequencepath: # If directory is empty because user pressed cancel
            return
        else:
            self.get_sequence(self.sequencepath)
            self.button_edit_other.setEnabled(True)
        
    def load_image_sequence_clicked(self):
        
        self.sequencepath = os.path.split(os.path.split(self.main_gui.userdirectory_slash.encode('ascii','ignore'))[0])[0] + os.sep + 'MasterConfigurations' + os.sep + 'StandardSequences' + os.sep + 'ImageSequence.xml'
        self.get_sequence(self.sequencepath)
        self.button_edit_other.setDisabled(True)
        
    def get_sequence(self,sequence_filename):
        
        # Delete the sequence that was previously displayed
        for i in range(self.ui.measurement_tab_scrollArea_content_widget.layout().count()): 
            self.ui.measurement_tab_scrollArea_content_widget.layout().itemAt(i).widget().setParent(None)
        
        # Function reads in variables and code from sequence file
        # FUTURE: insert parsing error messages
        sequence = ET.parse(sequence_filename).getroot()
         
        # Initialize and populate dictionary of variables
        
        self.measurement = MeasurementComponent(self,os.path.split(sequence_filename)[1][:-4])
        self.measurement.logged_quantities = OrderedDict() # Keep the order in which variables are declared to display
        
        self.measurement.add_logged_quantity('Read_from_hardware_at_start', 
                                 dtype=bool,
                                 ro=False,
                                 initial = True,
                                 vmin=False,
                                 vmax=True,
                                 unit='',
                                 is_variable=True,
                                 displayFlag=True)
        
        # Make sure to make clear that this Zeiss beam blanker (deflector) is off, if option below is chosen,
        # ONLY AT THE VERY END OF EXPERIMENT (ie, delay between frames will have beam open for example)
        # Add the two logged quantities that must always be present in a sequence
        self.measurement.add_logged_quantity('Auto_beam_blanking_at_end', 
                                 dtype=bool,
                                 ro=False,
                                 initial = True,
                                 vmin=False,
                                 vmax=True,
                                 unit='',
                                 is_variable=True,
                                 displayFlag=True)
        ### nominal total!!!!!! Includes any beam blanking desired
        self.measurement.add_logged_quantity('Beam_lag_time_at_pixel', 
                                 dtype=float,
                                 ro=False,
                                 initial= 0.006 * 1e-3, # Corresponds to ~ 3ms/line, for a line with 512 pixels
                                 vmin= 1/self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].read_from_hardware(), # at least ~ 0.5mus or  1/max experiment clock rate, namely 2MHz for NI DAC 6363 
                                 vmax= 600, # Arbitrarily long number: 10 min per pixel!!!
                                 unit='s',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Use_TTL_beam_blanking', 
                                 dtype=bool,
                                 ro=False,
                                 initial = True,
                                 vmin=False,
                                 vmax=True,
                                 unit='',
                                 is_variable=True,
                                 displayFlag=True)
        
        # If 'Use_TTL_beam_blanking' is false, 'TTL_beam_blanking_moving_lag_time' - I'll toggle enabled/disabled conditioned on bool value of 'Use_TTL_beam_blanking'
        #time that it takes in order for the acquisition to begin once the beam moved - this is 
        #the time it actually takes for the beam to get stable
        self.measurement.add_logged_quantity('TTL_beam_blanking_moving_lag_time', 
                                 dtype=float,
                                 ro=False,
                                 initial= 1e-6, #####See what happens if this value is set to zero - possibly crash the pulse train
                                 vmin= 1e-6, ##### CHECK THAT THE MAX RATE IS 1MHZ!!!!!!! Raith Beam Blank Controller
                                 vmax= self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val,
                                 unit='s',
                                 is_variable=True,
                                 displayFlag=True)
        #### 1microsec is minimum as given by Raith hardware
        
        self.measurement.add_logged_quantity('TTL_beam_blanking_transient_lag_time', 
                                 dtype=float,
                                 ro=False,
                                 initial= 0, #####See what happens if this value is set to zero - possibly crash the pulse train
                                 vmin= 1e-6, ##### CHECK THAT THE MAX RATE IS 1MHZ!!!!!!! Raith Beam Blank Controller
                                 vmax= self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val,
                                 unit='s',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Save_time_resolved_counts', 
                                 dtype=bool,
                                 ro=False,
                                 initial = False,
                                 vmin=False,
                                 vmax=True,
                                 unit='',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Scale_x', 
                                 dtype=float,
                                 ro=False,
                                 initial= 100,
                                 vmin= 0, 
                                 vmax= 100,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Scale_y', 
                                 dtype=float,
                                 ro=False,
                                 initial= 100,
                                 vmin= 0, 
                                 vmax= 100,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Offset_x', 
                                 dtype=float,
                                 ro=False,
                                 initial= 0.0,
                                 vmin= -0.5*(1-self.measurement.logged_quantities['Scale_x'].val/100.0)*100.0, 
                                 vmax= 0.5*(1-self.measurement.logged_quantities['Scale_x'].val/100.0)*100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Offset_y', 
                                 dtype=float,
                                 ro=False,
                                 initial= 0.0,
                                 vmin= -0.5*(1-self.measurement.logged_quantities['Scale_y'].val/100.0)*100.0, 
                                 vmax= 0.5*(1-self.measurement.logged_quantities['Scale_y'].val/100.0)*100.0,
                                 unit='%',
                                 is_variable=True,
                                 displayFlag=True)
                
        self.measurement.add_logged_quantity('Update_frame_percentage', 
                                 dtype=float,
                                 ro=False,
                                 initial= 100,
                                 vmin= 0, 
                                 vmax= 100,
                                 unit='%',
                                 is_variable=False,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('No_frames', 
                                 dtype=int,
                                 ro=False,
                                 initial= 1,
                                 vmin= 1, 
                                 vmax= 500,
                                 unit='',
                                 is_variable=False,
                                 displayFlag=True)
        
        self.measurement.add_logged_quantity('Immediate_frames', 
                                 dtype=bool,
                                 ro=False,
                                 initial = True,
                                 vmin=False,
                                 vmax=True,
                                 unit='',
                                 is_variable=True,
                                 displayFlag=True)
        
        # If immediate_frames is true, Delta_t_between_frames is useless - I'll toggle enabled/disabled conditioned on bool value of Immediate_frames
        self.measurement.add_logged_quantity('Delta_t_between_frames', 
                                 dtype=float,
                                 ro=False,
                                 initial= 0.0,
                                 vmin= 0.0, 
                                 vmax= 50.0,
                                 unit='s',
                                 is_variable=True,
                                 displayFlag=True)
        
        # GET VARIABLES
        # Remove empty lines
        no_empty_lines = os.linesep.join([s for s in sequence[0].text.splitlines() if s])
        # Remove white spaces
        no_empty_lines = no_empty_lines.replace(" ","")
        # Remove commented parts of line
        for line in no_empty_lines.split("\n"):
            line = line.partition("#")[0]
            line = line.rstrip()
            if line:
                vars = line.split(",") 
                if len(vars) == 5:
                    vars.append('')
                self.measurement.add_logged_quantity(vars[0].replace('$',""),
                                             dtype=eval(vars[1]),
                                             initial = vars[2],
                                             vmin=vars[3],
                                             vmax=vars[4],
                                             unit=vars[5],
                                             ro=False,
                                             is_variable=True,
                                             displayFlag=True)

        self.measurement.add_logged_quantity('Sequence_instructions', 
                                 dtype=str,
                                 ro=True,
                                 initial = sequence[1].text,
                                 is_variable=False,
                                 displayFlag=False)  
        
        self.measurement.setup()   
            
        # Connect all the measurement variables to the measurement widget
        for logged_variable in self.measurement.control_widgets:
            self.measurement.logged_quantities[logged_variable].connect_bidir_to_widget(self.measurement.control_widgets[logged_variable])   
            
        # Make 'Delta_t_between_frames' toggle enabled/not enabled upon clicking of bool 'Immediate_frames'
        self.measurement.control_widgets['Delta_t_between_frames'][0].setDisabled( self.measurement.logged_quantities['Immediate_frames'].read_from_hardware())
        self.measurement.control_widgets['Delta_t_between_frames'][1].setDisabled(self.measurement.logged_quantities['Immediate_frames'].read_from_hardware())
        self.measurement.control_widgets['Immediate_frames'][0].clicked.connect(lambda: self.immediate_state_changed())
        
        # Make 'TTL_beam_blanking_moving_lag_time' enabled/not enabled upon clicking of bool 'Use_TTL_beam_blanker'
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][0].setEnabled( self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware())
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][1].setEnabled(self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware())
        self.measurement.control_widgets['Use_TTL_beam_blanking'][0].clicked.connect(lambda: self.use_ttl_state_changed())
        
        # Make 'TTL_beam_blanking_TRANSIENT_lag_time' enabled/not enabled upon clicking of bool 'Save_time_resolved_counts'
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][0].setEnabled( self.measurement.logged_quantities['Save_time_resolved_counts'].read_from_hardware())
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][1].setEnabled(self.measurement.logged_quantities['Save_time_resolved_counts'].read_from_hardware())
        self.measurement.control_widgets['Save_time_resolved_counts'][0].clicked.connect(lambda: self.save_tr_state_changed())
        
        # Make max of 'TTL_beam_blanking_moving_lag_time'/max of 'TTL_beam_blanking_TRANSIENT_lag_time' change as soon as 'Beam_lag_time_at_pixel' is changed
        self.measurement.control_widgets['Beam_lag_time_at_pixel'][0].valueChanged.connect(lambda: self.beam_lag_time_changed())
        
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][0].valueChanged.connect(lambda: self.beam_moving_time_changed())
        
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][0].valueChanged.connect(lambda: self.beam_TRANSIENT_time_changed())
        
        # Make min/max of 'Offset_x/y' change when 'Scale_x/y' is changed
        self.measurement.control_widgets['Scale_x'][0].valueChanged.connect(lambda: self.scale_x_changed())
        self.measurement.control_widgets['Scale_y'][0].valueChanged.connect(lambda: self.scale_y_changed())
                
        # Grab text of sequence instructions
        for key in self.measurement.logged_quantities.keys():
            sequence[1].text = sequence[1].text.replace('$' + key + '$', 'self.measurement.logged_quantities[\'' + key + '\'].val')
        for hardware_component in self.main_gui.hardware_widget.hardware.keys():
            for logged_variable in self.main_gui.hardware_widget.hardware[hardware_component].logged_quantities.keys():
                sequence[1].text = sequence[1].text.replace('$' + logged_variable + '$', 'self.main_gui.hardware_widget.hardware[\'' + hardware_component + '\'].logged_quantities[\'' + logged_variable + '\'].val')    
         
        self.commands_to_be_exec =  sequence[1].text
        
        self.button_start.setEnabled(True)
        pg.QtGui.QApplication.processEvents() #probably not necessary
       
    
    def immediate_state_changed(self):
        self.measurement.control_widgets['Delta_t_between_frames'][1].setChecked(False)
        self.measurement.logged_quantities['Delta_t_between_frames'].update_value(0.0)
        self.measurement.control_widgets['Delta_t_between_frames'][0].setDisabled(self.measurement.logged_quantities['Immediate_frames'].read_from_hardware())
        self.measurement.control_widgets['Delta_t_between_frames'][1].setDisabled(self.measurement.logged_quantities['Immediate_frames'].read_from_hardware())
    
    def use_ttl_state_changed(self):
    
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][1].setChecked(False)
        
        self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].update_value(1.0e-6) #min value
        
        if self.measurement.logged_quantities['Use_TTL_beam_blanking'].val and not self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val >= 2.0e-6: #1microsec on, 1 microsec off
            #increase beam lag time accordingly
            hlp = 1.0e-6 - (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val)
            self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value( self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val + hlp)
     
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][0].setEnabled(self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware())
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][1].setEnabled(self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware())
        
        self.measurement.control_widgets['Save_time_resolved_counts'][0].setChecked(False)
        self.measurement.control_widgets['Save_time_resolved_counts'][0].setEnabled(self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware())
        self.save_tr_state_changed()
        
    def save_tr_state_changed(self):
         
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][1].setChecked(False)    
        self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].update_value(1.0e-6) #min value #not really needs to see if lag time > 2micros too!!!
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][0].setEnabled(self.measurement.logged_quantities['Save_time_resolved_counts'].read_from_hardware())
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][1].setEnabled(self.measurement.logged_quantities['Save_time_resolved_counts'].read_from_hardware())
    
    def beam_lag_time_changed(self):
        
        self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].vmax = self.measurement.logged_quantities['Beam_lag_time_at_pixel'].read_from_hardware()
        self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].vmax = self.measurement.logged_quantities['Beam_lag_time_at_pixel'].read_from_hardware() - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].read_from_hardware()
        self.measurement.control_widgets['TTL_beam_blanking_moving_lag_time'][0].setMaximum(self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].vmax)
        self.measurement.control_widgets['TTL_beam_blanking_transient_lag_time'][0].setMaximum(self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].vmax)
    
        #Check if lag time - beam blanking > 1micros:
        if not self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val >= 1.0e-6:
            # increase the lag time accordingly
            hlp = 1.0e-6 - (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val)
            self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value( self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val + hlp)
    
        #### For TRANSIENT, it's ok, because blanking+ TRANSIENT > 1microsec, and blanking is always > 1microsec by default!
        # Check if all times are higher than 1microsec
#         if self.measurement.logged_quantities['Save_time_resolved_counts'].val:
#             if not (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val) - self.measurement.logged_quantities['TTL_beam_blanking_TRANSIENT_lag_time'].val >= 1.0e-6:
#             #increase lag time accordingly
#                 hlp = 1.0e-6 - self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val - self.measurement.logged_quantities['TTL_beam_blanking_TRANSIENT_lag_time'].val
#                 self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value( self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val + hlp)
#      
#     
    def beam_moving_time_changed(self):
        
         #Check if lag time - beam blanking > 1micros:
        if not self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val >= 1.0e-6:
            # increase the lag time accordingly
            hlp = 1.0e-6 - (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val)
            self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value( self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val + hlp)
    
    def beam_TRANSIENT_time_changed(self):
        
            # check if time_on is higher than 1microsec
            if not (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val) - self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].val >= 1.0e-6:
            #increase lag time accordingly
                hlp = 1.0e-6 - (self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val - self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].val - self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].val)
                self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value( self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val + hlp)
      
    def scale_x_changed(self):
    
        self.measurement.logged_quantities['Offset_x'].vmax = +0.5*(1-self.measurement.logged_quantities['Scale_x'].read_from_hardware()/100.0)*100.0
        self.measurement.logged_quantities['Offset_x'].vmin = -0.5*(1-self.measurement.logged_quantities['Scale_x'].read_from_hardware()/100.0)*100.0
        self.measurement.control_widgets['Offset_x'][0].setMaximum(self.measurement.logged_quantities['Offset_x'].vmax)
        self.measurement.control_widgets['Offset_x'][0].setMinimum(self.measurement.logged_quantities['Offset_x'].vmin)
    
    def scale_y_changed(self):
    
        self.measurement.logged_quantities['Offset_y'].vmax = +0.5*(1-self.measurement.logged_quantities['Scale_y'].read_from_hardware()/100.0)*100.0
        self.measurement.logged_quantities['Offset_y'].vmin = -0.5*(1-self.measurement.logged_quantities['Scale_y'].read_from_hardware()/100.0)*100.0
        self.measurement.control_widgets['Offset_y'][0].setMaximum(self.measurement.logged_quantities['Offset_y'].vmax)
        self.measurement.control_widgets['Offset_y'][0].setMinimum(self.measurement.logged_quantities['Offset_y'].vmin)
                            
    def set_sequence(self):
        
        # Load sequence and check if it is runneable
        # FUTURE: Give error if it's not an ok sequence (out of bounds etc)

        # Check for is_varied = True in logged quantities
        self.name_var_to_be_varied = []; # Instantiate lists
        self.name_var_to_be_varied_type = []; 
        self.name_var_to_be_varied_unit = [];
        
        for quantity in self.measurement.logged_quantities.keys():
            if self.measurement.logged_quantities[quantity].is_varied:
                self.name_var_to_be_varied.append(quantity)
                self.name_var_to_be_varied_type.append('Measurement')
                self.name_var_to_be_varied_unit.append(self.measurement.logged_quantities[quantity].unit)

        for hardware_component in self.main_gui.hardware_widget.hardware.keys():
            for logged_variable in self.main_gui.hardware_widget.hardware[hardware_component].logged_quantities.keys():
                if self.main_gui.hardware_widget.hardware[hardware_component].logged_quantities[logged_variable].is_varied:
                    if self.main_gui.hardware_widget.hardware[hardware_component].logged_quantities[logged_variable].ro:
                        self.my_msg_box("This should not have happened. The var is ro and yet it's being varied! Right now nothing is done, in the future will have to abort set_sequence here")
                    else:
                        self.name_var_to_be_varied.append(logged_variable)
                        self.name_var_to_be_varied_type.append(hardware_component)
                        self.name_var_to_be_varied_unit.append(self.main_gui.hardware_widget.hardware[hardware_component].logged_quantities[logged_variable].unit)
       
        self.vary_begin = [];
        self.vary_step_size = [];
        self.vary_end = [];
        self.scan = [];    
        if self.name_var_to_be_varied:
            for k in range(len(self.name_var_to_be_varied)):    
                    self.vary_begin.append(eval(self.my_repl(self.name_var_to_be_varied[k],self.name_var_to_be_varied_type[k],'.start')))
                    self.vary_step_size.append(eval(self.my_repl(self.name_var_to_be_varied[k],self.name_var_to_be_varied_type[k],'.step')))
                    self.vary_end.append(eval(self.my_repl(self.name_var_to_be_varied[k],self.name_var_to_be_varied_type[k],'.stop')))
                
                    if (self.vary_end[k]-self.vary_begin[k])%self.vary_step_size[k] <= sys.float_info.epsilon:
                        add = self.vary_step_size[k]
                    else:
                        add = 0
                    self.scan.append(np.arange(self.vary_begin[k],self.vary_end[k]+add,self.vary_step_size[k]))
                    #print str(np.arange(self.vary_begin[k],self.vary_end[k]+add,self.vary_step_size[k])) # varying arrays
                    exec(self.my_repl(self.name_var_to_be_varied[k],self.name_var_to_be_varied_type[k],'.val = None')) # Variables that are varied get a None for current value
                    if abs(self.scan[k][-1] - self.vary_end[k]) > sys.float_info.epsilon:
                        self.my_msg_box('Note that end point in scan of variable ' + self.name_var_to_be_varied[k] + ' will be %2.6f and not %2.6f because of scan step size.' % (self.scan[k][-1],self.vary_end[k]))

        # Here is the sequence made
        # Read out current values
        self.array_of_sequences = [];
        if not self.name_var_to_be_varied: # If the scan is a simple image
            string_to_be_exec = ''
            self.array_of_sequences.append( string_to_be_exec )   
        else:
            # Let's do it for 1 and 2 vary variables only
            if len(self.name_var_to_be_varied) == 1:
                for k in range(len(self.scan[0])):
                    string_to_be_exec = self.my_repl(self.name_var_to_be_varied[0],self.name_var_to_be_varied_type[0],'.update_value(' + str(self.scan[0][k]) + ")\n")
                    self.array_of_sequences.append( string_to_be_exec ) 
            elif len(self.name_var_to_be_varied) == 2:
                
                # Get info of which variable to vary in the outer loop
                msgBox = QMessageBox()
                msgBox.setText('Choose the variable for the OUTER loop - like this: \n for k in VAR_OUTER: \n       for kk in VAR_INNER: \n              Do something (usually take image)')
                msgBox.addButton(self.name_var_to_be_varied[0], QMessageBox.AcceptRole)
                msgBox.addButton(self.name_var_to_be_varied[1], QMessageBox.RejectRole)
                
                if msgBox.exec_() == QMessageBox.AcceptRole:
                    self.outer = 0
                    self.inner = 1
                else:
                    self.inner = 0
                    self.outer = 1
                
                for k in range(len(self.scan[self.outer])):
                    for kk in range(len(self.scan[self.inner])):
                        string_to_be_exec = self.my_repl(self.name_var_to_be_varied[self.outer],self.name_var_to_be_varied_type[self.outer],'.update_value(' + str(self.scan[self.outer][k])) + ")\n" + self.my_repl(self.name_var_to_be_varied[self.inner],self.name_var_to_be_varied_type[self.inner],'.update_value(' + str(self.scan[self.inner][kk]) + ")\n")
                        self.array_of_sequences.append( string_to_be_exec ) 
                    
            else:
                self.my_msg_box("More than 2 vary scans not implemented yet, program will crash now! If you need more than 2 variables to be scanned, talk to Clarice.")
                return None
                              
    def start_clicked(self):
        
        # wait until last hardware update is made
        while not self.main_gui.hardware_widget.hardware['Microscope'].cont_read_is_done:
            pass
         
        # Read from hardware in order to save correct values
        if self.measurement.logged_quantities['Read_from_hardware_at_start'].val:
         for quantity in self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities.keys():
                         self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities[quantity].hardware_read_func()
        
        self.start_is_on = True
        
        self.set_sequence()
        
        # FUTURE: Perform check if sequence is ok
        # If sequence is ok, then: 
        
        # Change status of widget objects
        self.main_gui.configuration_widget.lineedit_filesrootname.setDisabled(True) 
    
        self.main_gui.hardware_widget.scrollArea_hardware.setDisabled(True)
        
        self.main_gui.results_widget.roi_button.setDisabled(True)
        self.main_gui.results_widget.reset_roi_button.setDisabled(True)
        self.main_gui.results_widget.button_count.setDisabled(True)
        
        self.scrollArea_measurement.setDisabled(True)
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True) 
        
        self.main_gui.results_widget.fig_ch[2].lineedit_name.setText(self.main_gui.results_widget.newname2) 
        self.main_gui.results_widget.fig_ch[3].lineedit_name.setText(self.main_gui.results_widget.newname3)  
        
        self.no_ai_channels = self.main_gui.results_widget.no_ai_channels # just to make it short
        
        # Dummy figure - just to make all four figures blank
        for k in range(4): #nb counter channels
            self.main_gui.results_widget.fig_ch[k].viewer.setImage(np.zeros([10,10]))
     
        self.progressbar.setValue(0.0)
        
        # Disable Joystick and panel - not sure working
        old_joystick = self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Joystick_enabled_status'].val
        self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Joystick_enabled_status'].update_value(False)
        old_panel = self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Panel_enabled_status'].val
        self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Panel_enabled_status'].update_value(False)
        
        # Change status of hardware
        self.main_gui.hardware_widget.hardware['Microscope'].write_External_scan_enabled_status(1) # tell Microscope external scan is coming = 1
        
        # If user chooses to use TTL beam blanker, Zeiss deflection beam blanker is left open (= beam going thru aperture) and TTL beam blanker takes over completely
        # Implementation of dummy high line to leave the beam blanking line on (ie, beam cut) - used to be inside next loop
        if self.measurement.logged_quantities['Use_TTL_beam_blanking'].val:
            self.main_gui.hardware_widget.hardware['DAC'].dummy(is_high=1)
        # Turn beam physically on (note that it will be blanked because of dummy high function above)
        self.main_gui.hardware_widget.hardware['Microscope'].write_Beam_blanking_status(0)
        
        # For use with abort button
        self.abort_scan = 0
        # To update the progress bar
        loopplace = 1
        
        # To avoid multiple function calls
        # Those are not variables that can be varied, so that can read it once outside the main loop
        self.no_frames = self.measurement.logged_quantities['No_frames'].read_from_hardware() 
        self.use_ttl_bb = self.measurement.logged_quantities['Use_TTL_beam_blanking'].read_from_hardware()
        self.save_time_resolved_counts = self.measurement.logged_quantities['Save_time_resolved_counts'].read_from_hardware()
        self.experiment_clock_rate = self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].read_from_hardware()
        self.update_frame_percentage = self.measurement.logged_quantities['Update_frame_percentage'].read_from_hardware()
       
        
        # Looping over the sequences
        for k_curr in range(len(self.array_of_sequences)):
            
            if not self.abort_scan:

                # I am not reading all values from hw continuously, so everytime I need a variable, I will need to use logged_quantity.read_from_harware() function, not logged_quantity.val!
                
                # Variables are given correct values for the current k-th scan point
                exec(self.array_of_sequences[k_curr])
                
                # Give commands to be executed; the scan shape at least
                exec(self.commands_to_be_exec) 
                
                buff_out_x, buff_out_y, scan_tuple_x, scan_tuple_y = self.scan_shape.scan_pattern()
                
                # Calculate pixel size in x and y in order to display and save data; in meters
                # Pixel size in each direction is actually BEAM STEP IN EACH DIRECTION
                # Really need to do this inside the loop, as vary quantities may yield a different pixel size
                self.pixel_x = self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Pixel_size'].read_from_hardware()*1e9*self.scan_shape.pixel_scaling()[0]
                self.pixel_y = self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Pixel_size'].read_from_hardware()*1e9*self.scan_shape.pixel_scaling()[1]
                
                # Prepare buffer: no_pixels * no_points_at_same_pixel 
                self.no_pixels = self.scan_shape.no_pixels() # By default now, no_pixels always gotten by function scan_shape.no_pixels()
                self.no_points_at_same_pixel = int(round(self.measurement.logged_quantities['Beam_lag_time_at_pixel'].read_from_hardware() * self.experiment_clock_rate ))
                # Display true beam lag time at pixel after adjustment
                self.measurement.logged_quantities['Beam_lag_time_at_pixel'].update_value(float(self.no_points_at_same_pixel)/ self.experiment_clock_rate)
                self.lag_time = self.measurement.logged_quantities['Beam_lag_time_at_pixel'].val
                
                # Prepare display and read update loops
                self.no_pixels_after_which_to_update = int(round(self.update_frame_percentage/100.0 * self.no_pixels))
                # Display true percentage update after adjustment
                self.measurement.logged_quantities['Update_frame_percentage'].update_value(100.0*float(self.no_pixels_after_which_to_update)/float(self.no_pixels))
                numm = self.no_pixels // self.no_pixels_after_which_to_update # How many integer number of updates
                remaining = self.no_pixels % self.no_pixels_after_which_to_update # Remaining number of pixels to update
                
                # To avoid many function calls
                self.grid_x = self.scan_shape.shape()[0]
                self.grid_y = self.scan_shape.shape()[1]
            
                # Prepare arrays to save
                data_AI_reshaped = np.zeros([self.no_ai_channels,self.no_frames,self.grid_x,self.grid_y]) 
                data_counter_reshaped = np.zeros([2,self.no_frames,self.grid_x,self.grid_y])
                
                self.counter_clock_rate, self.int_clock_rate, timehigh, self.no_dark_count_samples, TRANSIENT, self.no_TRANSIENT_count_samples, truly_immediate, time_bet_frames  = self.main_gui.hardware_widget.hardware['DAC'].configure(self.no_pixels, self.no_points_at_same_pixel, self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].read_from_hardware(),self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].read_from_hardware(),self.no_frames,self.use_ttl_bb,self.measurement.logged_quantities['Delta_t_between_frames'].read_from_hardware(),self.measurement.logged_quantities['Immediate_frames'].val)
                #print self.no_TRANSIENT_count_samples
                # self.int_clock_rate is the rate between counter and AO clocks: how many counter points per AO point
                # no_dark_count_samples is per pixel!!! Needs to take into account how many AO points stay at pixel
                # no_TRANSIENT_count_samples is per pixel!!! Needs to take into account how many AO points stay at pixel
                # update adjusted beam blanking time and TRANSIENT blanking time
                self.measurement.logged_quantities['TTL_beam_blanking_moving_lag_time'].update_value(timehigh)
                self.measurement.logged_quantities['TTL_beam_blanking_transient_lag_time'].update_value(TRANSIENT)
                self.measurement.logged_quantities['Immediate_frames'].update_value(truly_immediate) #Needs to update Immediate_frames first bc sets Delta_t to 0
                self.measurement.logged_quantities['Delta_t_between_frames'].update_value(time_bet_frames)
                
                # Prepare time-resolved arrays
                if self.use_ttl_bb:
                    data_counter_backgd_subtracted = np.zeros([2,self.no_frames,self.grid_x,self.grid_y])
                    data_counter_bright_reshaped = np.zeros([2,self.no_frames,self.grid_x,self.grid_y])
                    data_counter_time_resolved_reshaped = np.zeros([2,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel, self.grid_x,self.grid_y])
                    data_counter_time_resolved_dark_reshaped = np.zeros([2,self.no_frames,self.no_dark_count_samples, self.grid_x,self.grid_y])
                    data_counter_time_resolved_bright_reshaped = np.zeros([2,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples, self.grid_x,self.grid_y])
                    if self.save_time_resolved_counts:
                       data_counter_time_resolved_TRANSIENT_reshaped = np.zeros([2,self.no_frames,self.no_TRANSIENT_count_samples, self.grid_x,self.grid_y])
                    
                # Prepare buffer
                x = buff_out_x.repeat(self.no_points_at_same_pixel)
                y = buff_out_y.repeat(self.no_points_at_same_pixel)
                
                stx = scan_tuple_x#.repeat(self.no_points_at_same_pixel)
                sty = scan_tuple_y#.repeat(self.no_points_at_same_pixel)
            
                scan_samples = np.zeros((x.size + y.size,), dtype=x.dtype) #no samples/no pixels == no samples per pixel
                scan_tuple = np.zeros((scan_tuple_x.size + scan_tuple_y.size,), dtype=int) #no samples/no pixels == no samples per pixel
            
                scan_samples[0::2] = x
                scan_samples[1::2] = y
                
                scan_tuple[0::2] = stx
                scan_tuple[1::2] = sty
    
                scan_tuple = np.tile(scan_tuple,self.no_frames)
                self.main_gui.hardware_widget.hardware['DAC'].load_AO_buffer(np.tile(scan_samples,self.no_frames))    
            
                # Launch tasks
                self.main_gui.hardware_widget.hardware['DAC'].start_data_acquisition()
                
                ###################################################
                
                for auxframes in range(self.no_frames):
                    
                    if not self.abort_scan:
        
                        for aux in range(numm): # Integer number of updates
                            
                            if not self.abort_scan:
                                                                
                                data_AItemp2, data_countertemp2, data_counter_time_resolvedtemp2 = self.main_gui.hardware_widget.hardware['DAC'].read_data( self.no_points_at_same_pixel* self.no_pixels_after_which_to_update) # outputs all data, time-resolved
                                
                                # Reorganizing by channel
                                data_AI_temp = np.zeros([len(data_AItemp2),self.no_pixels_after_which_to_update])
                                data_counter_temp = np.zeros([len(data_countertemp2),self.no_pixels_after_which_to_update])
                                
                                t = time.time()
                                for kk in range(self.no_ai_channels):
                                    data_AI_temp[kk] = np.mean(data_AItemp2[kk].reshape(-1,self.no_points_at_same_pixel) , axis=1)    
                                    xind = scan_tuple[aux*2*self.no_pixels_after_which_to_update:(aux+1)*2*self.no_pixels_after_which_to_update :2]
                                    yind = scan_tuple[aux*2*self.no_pixels_after_which_to_update+1:(aux+1)*2*self.no_pixels_after_which_to_update+1 :2]
                                        
                                    for jj in range(self.no_pixels_after_which_to_update): 
                                        data_AI_reshaped[kk, auxframes ,xind[jj],yind[jj]] = data_AI_temp[kk,jj]
                                elapsed = time.time() - t
                                #print "time to AI: " + str(elapsed) 
                                
                                t = time.time()
                                for kk in range(2): #nb counters
                                    data_counter_temp[kk] = np.mean(data_countertemp2[kk].reshape(-1,self.no_points_at_same_pixel) , axis=1)        
                                    xind = scan_tuple[aux*2*self.no_pixels_after_which_to_update:(aux+1)*2*self.no_pixels_after_which_to_update :2]
                                    yind = scan_tuple[aux*2*self.no_pixels_after_which_to_update+1:(aux+1)*2*self.no_pixels_after_which_to_update+1 :2]
                                    
                                    for jj in range(self.no_pixels_after_which_to_update):
                                        data_counter_reshaped[kk,auxframes, xind[jj],yind[jj]] = data_counter_temp[kk,jj]
                                        if self.use_ttl_bb:
                                            for pp in range(self.int_clock_rate*self.no_points_at_same_pixel):
                                                data_counter_time_resolved_reshaped[kk,auxframes, pp, xind[jj],yind[jj]] = data_counter_time_resolvedtemp2[kk,jj*self.int_clock_rate*self.no_points_at_same_pixel + pp]        
                                elapsed = time.time() - t
                                #print "time to counter: " + str(elapsed)   
                        
                                ###TRYING NOT TO DISPLAY ANYTHING
                                ##### IF TTL BEAM BLANKING IN USE, DISPLAY BACKGROUND CORRECTED OR ONLY BRIGHT!!!
                                
                                #if aux == 0:
                                self.display_picture(data_AI_reshaped[:,auxframes,:,:],data_counter_reshaped[:,auxframes,:,:]*self.counter_clock_rate)
                               # else:
                                  #   t = time.time()
                                  #   self.display_picture(data_AI_reshaped[:,auxframes,:,:],data_counter_reshaped[:,auxframes,:,:]*self.counter_clock_rate) 
                                  #   elapsed = time.time() - t
                                     #print "time to display: " + str(elapsed)
                                
                                self.progressbar.setValue(100.0* float(loopplace) /float(len(self.array_of_sequences)*self.no_frames*numm))
                                loopplace += 1      
                                     
                            
                        
                        if remaining and not self.abort_scan: # If remaining points are not zero
                            
                            #self.progressbar_vary.setValue(float((aux*numm+remaining)*auxframes)/float(self.no_pixels*self.no_frames))
                            
                            data_AItemp2, data_countertemp2, data_counter_time_resolvedtemp2 = self.main_gui.hardware_widget.hardware['DAC'].read_data(  self.no_points_at_same_pixel* remaining ) # outputs all data, time-resolved
                            
                            # Reorganizing by channel
                            data_AI_temp = np.zeros([self.no_ai_channels,remaining])
                            data_counter_temp = np.zeros([len(data_countertemp2),remaining])
                        
                            for kk in range(self.no_ai_channels):
                                data_AI_temp[kk] = np.mean(data_AItemp2[kk].reshape(-1,self.no_points_at_same_pixel) , axis=1)    
                                xind = scan_tuple[(numm)*2*self.no_pixels_after_which_to_update:(numm)*2*self.no_pixels_after_which_to_update+remaining*2 :2]
                                yind = scan_tuple[(numm)*2*self.no_pixels_after_which_to_update+1:(numm)*2*self.no_pixels_after_which_to_update+remaining*2+1 :2]
        
                                for jj in range(remaining):
                                    data_AI_reshaped[kk, auxframes ,xind[jj],yind[jj]] = data_AI_temp[kk,jj]
                            
                            for kk in range(2):
                                data_counter_temp[kk] = np.mean(data_countertemp2[kk].reshape(-1,self.no_points_at_same_pixel) , axis=1)        
                                xind = scan_tuple[(numm)*2*self.no_pixels_after_which_to_update:(numm)*2*self.no_pixels_after_which_to_update+remaining*2 :2]
                                yind = scan_tuple[(numm)*2*self.no_pixels_after_which_to_update+1:(numm)*2*self.no_pixels_after_which_to_update+remaining*2+1 :2]
                                
                                for jj in range(remaining):
                                    data_counter_reshaped[kk,auxframes, xind[jj],yind[jj]] = data_counter_temp[kk,jj]
                                    if self.use_ttl_bb:
                                         for pp in range(self.int_clock_rate*self.no_points_at_same_pixel):
                                             data_counter_time_resolved_reshaped[kk,auxframes, pp, xind[jj],yind[jj]] = data_counter_time_resolvedtemp2[kk,jj*self.int_clock_rate*self.no_points_at_same_pixel + pp]
                           
                                                 
                            #self.update_picture(data_AI_reshaped[:,auxframes,:,:],data_counter_reshaped[:,auxframes,:,:]*self.counter_clock_rate) 
                            self.display_picture(data_AI_reshaped[:,auxframes,:,:],data_counter_reshaped[:,auxframes,:,:]*self.counter_clock_rate) 
                     
                            self.progressbar.setValue(100.0* float(loopplace) /float(len(self.array_of_sequences)*self.no_frames*numm))
                            loopplace += 1 
                        
                        ##### After all acquired, save the rates - overwrite data_counter_reshaped - now in cps!!!!!!!!!!!
                        # for the first pass, convert to cps; all the other frames won't need this
#                         if auxframes == 0:
#                             data_counter_reshaped = self.counter_clock_rate * data_counter_reshaped 
#                         
#                             if self.use_ttl_bb:
#                                 data_counter_time_resolved_reshaped = self.counter_clock_rate * data_counter_time_resolved_reshaped
                        
                        if self.use_ttl_bb:
                            data_counter_time_resolved_dark_reshaped = data_counter_time_resolved_reshaped[:,:,0:self.no_dark_count_samples:1,:,:]
                            data_counter_time_resolved_bright_reshaped  = data_counter_time_resolved_reshaped[:,:,self.no_dark_count_samples:self.int_clock_rate*self.no_points_at_same_pixel-self.no_TRANSIENT_count_samples:1,:,:]
                            data_counter_bright_reshaped = np.mean(data_counter_time_resolved_bright_reshaped, axis=2)
                            data_counter_backgd_subtracted = data_counter_bright_reshaped - np.mean(data_counter_time_resolved_dark_reshaped, axis=2) 
                            if self.save_time_resolved_counts:
                                  data_counter_time_resolved_TRANSIENT_reshaped = data_counter_time_resolved_reshaped[:,:,self.int_clock_rate*self.no_points_at_same_pixel-self.no_TRANSIENT_count_samples-1:-1:1,:,:]
                                 
                    ###################################################
                 
                # Stop taskes
                self.main_gui.hardware_widget.hardware['DAC'].stop_data_acquisition(is_forced=self.abort_scan)
                
                # If at this point the scan is deemed successful - FUTURE: Do something if scan is not
                
                #### ORIGINAL
                #print data_counter_reshaped
                self.display_picture(data_AI_reshaped,data_counter_reshaped*self.counter_clock_rate,np.arange(1,self.no_frames+1))
                # TRY FIRST TO DISPLAY CORRECTLY in kcps
                #resulto = [ xis*self.int_clock_rate/self.lag_time for xis in data_counter_reshaped ]
                #print np.mean(resulto[0,:,:,:])
#                 self.display_picture(data_AI_reshaped,resulto,np.arange(1,self.no_frames+1))
#                 print data_counter_reshaped[1]
#                 print resulto[1]
                
                # Data saved at every sequence of frames (before the change in vary variables)
                if not self.abort_scan:
                    self.textedit_comments.setDisabled(True)
                    self.measurement.add_logged_quantity('Comments', 
                         dtype=str,
                         ro=True,
                         initial = self.textedit_comments.toPlainText()) 
                    if self.use_ttl_bb:
                        if self.save_time_resolved_counts:
                            self.save_data(k_curr,data_AI_reshaped,data_counter_reshaped*self.counter_clock_rate,data_counter_backgd_subtracted*self.counter_clock_rate, data_counter_bright_reshaped*self.counter_clock_rate,data_counter_time_resolved_reshaped*self.counter_clock_rate,data_counter_time_resolved_dark_reshaped*self.counter_clock_rate,data_counter_time_resolved_bright_reshaped*self.counter_clock_rate,data_counter_time_resolved_TRANSIENT_reshaped*self.counter_clock_rate)    
                        else:
                            self.save_data(k_curr,data_AI_reshaped,data_counter_reshaped*self.counter_clock_rate,data_counter_backgd_subtracted*self.counter_clock_rate, data_counter_bright_reshaped*self.counter_clock_rate)    
                    else:
                        self.save_data(k_curr,data_AI_reshaped,data_counter_reshaped*self.counter_clock_rate)    

                
            else: # If it's aborted
                return None
            
        # Check for auto_beam_blank - used to be inside previous loop
        if self.measurement.logged_quantities['Auto_beam_blanking_at_end'].val:
            self.main_gui.hardware_widget.hardware['Microscope'].write_Beam_blanking_status(1) 
            
        # Implementation of dummy low line to leave the beam blanking line off (ie, beam open and at the mercy of beam blanking command in RemCon)
        if self.use_ttl_bb:
            self.main_gui.hardware_widget.hardware['DAC'].dummy(is_high=0) 
                
        # After all scan points are completed, change status of widget objects
        self.main_gui.configuration_widget.lineedit_filesrootname.setEnabled(True)
        self.button_start.setEnabled(True)
        self.button_stop.setDisabled(True)
        self.main_gui.hardware_widget.scrollArea_hardware.setEnabled(True)
        self.scrollArea_measurement.setEnabled(True)

        self.main_gui.results_widget.roi_button.setEnabled(True)
        self.main_gui.results_widget.reset_roi_button.setEnabled(True)
        self.main_gui.results_widget.button_count.setEnabled(True)
        
        self.textedit_comments.setEnabled(True)
        
        #Return to old values
        self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Joystick_enabled_status'].update_value(old_joystick)
        self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Panel_enabled_status'].update_value(old_panel)
        
        if not self.measurement.logged_quantities['Scale_x'].is_varied and not self.measurement.logged_quantities['Scale_y'].is_varied:
            #print "here"
            if self.measurement.logged_quantities['Scale_x'].val != 100.0 or self.measurement.logged_quantities['Scale_y'].val != 100.0:
                self.main_gui.results_widget.roi_button.setDisabled(True)
             
                self.measurement.control_widgets['Scale_x'][0].setDisabled(True)
                self.measurement.control_widgets['Scale_y'][0].setDisabled(True)
                self.measurement.control_widgets['Offset_x'][0].setDisabled(True)
                self.measurement.control_widgets['Offset_y'][0].setDisabled(True)
                self.measurement.control_widgets['Scale_x'][1].setDisabled(True)
                self.measurement.control_widgets['Scale_y'][1].setDisabled(True)
                self.measurement.control_widgets['Offset_x'][1].setDisabled(True)
                self.measurement.control_widgets['Offset_y'][1].setDisabled(True)
            
        self.progressbar.setValue(0.0)
        
    
#     def update_picture(self,data_AI_reshaped,data_counter_reshaped): 
#          
#         #######     CHECK IF PREVIOUS CONFIGS ARE MAINTAINED OR NOT!!!!
#         self.main_gui.results_widget.fig_ch[0].viewer.setImage(data_counter_reshaped[0],autoRange=True,scale = [1,float(data_counter_reshaped[0].shape[0])/float(data_counter_reshaped[0].shape[1])], autoHistogramRange=False)
#         self.main_gui.results_widget.fig_ch[1].viewer.setImage(data_counter_reshaped[1],autoRange=True,scale = [1,float(data_counter_reshaped[1].shape[0])/float(data_counter_reshaped[1].shape[1])], autoHistogramRange=False)
#         self.main_gui.results_widget.fig_ch[2].viewer.setImage(data_AI_reshaped[0],autoRange=True,scale = [1,float(data_AI_reshaped[0].shape[0])/float(data_AI_reshaped[0].shape[1])], autoHistogramRange=False)
#         self.main_gui.results_widget.fig_ch[3].viewer.setImage(data_AI_reshaped[1],autoRange=True,scale = [1,float(data_AI_reshaped[1].shape[0])/float(data_AI_reshaped[1].shape[1])], autoHistogramRange=False)
#         time.sleep(0.2)   
#         pg.QtGui.QApplication.processEvents()
#         time.sleep(1)  

        self.start_is_on = False     
    
    def display_picture(self,data_AI_reshaped,data_counter_reshaped, xval= None):
        
        if (self.measurement.logged_quantities['Scale_x'].val == 100.0) and (self.measurement.logged_quantities['Scale_y'].val == 100.0):
            is_original = True
        else:
            is_original = False
            
        for k in range(2): #nb counter channels
            self.main_gui.results_widget.fig_ch[k].load(data=data_counter_reshaped[k],
                                           scale_size=self.grid_x*0.2, # Take 1/5 of the number of pixels of the line
                                           scale_length=self.pixel_x*self.grid_x*0.2*1e-6,
                                           scale_suffix='m',
                                           is_original=is_original,
                                           xvalues = xval
                                           )
            # Display min, max, mean for current frame. In movie, will show min/mean/max of last frame always
            ### Also change those as the slider is changed
            # right now I don't know how to get a signal for slide change
            # Pssibly too large.... where's the error?
            self.main_gui.results_widget.fig_ch[k].label_min.setText('Min ' + str("{:.3f}".format(np.amin(data_counter_reshaped[k]/1000))))
            self.main_gui.results_widget.fig_ch[k].label_mean.setText('Mean ' + str("{:.3f}".format(np.mean(data_counter_reshaped[k]/1000))))
            self.main_gui.results_widget.fig_ch[k].label_max.setText('Max ' + str("{:.3f}".format(np.amax(data_counter_reshaped[k]/1000))))
            
        
        # here k == 1
        for kk in range(self.no_ai_channels): #nb ai channels
            self.main_gui.results_widget.fig_ch[k +1 + kk].load(data=data_AI_reshaped[kk],
                                           scale_size=self.grid_x*0.2,
                                           scale_length=self.pixel_x*self.grid_x*0.2*1e-6,
                                           scale_suffix='m',
                                           is_original=is_original,
                                           xvalues = xval
                                           )
            
   
        
    def save_data(self, k_curr,data_AI_reshaped,data_counter_reshaped,data_counter_backgd_subtracted=None, data_counter_bright_reshaped=None,data_counter_time_resolved_reshaped=None, data_counter_time_resolved_dark_reshaped=None, data_counter_time_resolved_bright_reshaped=None,data_counter_time_resolved_TRANSIENT_reshaped=None):
        
        # Rotate and invert picture to match Zeiss display 
        # Those two arrays are always saved     
        counter_rotated        = np.zeros([2,self.no_frames,self.grid_y,self.grid_x])
        AI_rotated             = np.zeros([self.no_ai_channels,self.no_frames,self.grid_y,self.grid_x])
        
        if self.use_ttl_bb:
            counter_rotated_bg_sub = np.zeros([2,self.no_frames,self.grid_y,self.grid_x])  
            counter_rotated_bright = np.zeros([2,self.no_frames,self.grid_y,self.grid_x])   
            if self.save_time_resolved_counts:
                counter_time_resolved_rotated = np.zeros([2,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x])
                data_counter_time_resolved_dark_rotated   = np.zeros([2,self.no_frames,self.no_dark_count_samples, self.grid_y,self.grid_x])
                data_counter_time_resolved_bright_rotated = np.zeros([2,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples, self.grid_y,self.grid_x])
                data_counter_time_resolved_TRANSIENT_rotated = np.zeros([2,self.no_frames,self.no_TRANSIENT_count_samples, self.grid_y,self.grid_x])
               # print counter_time_resolved_rotated.shape, data_counter_time_resolved_dark_rotated.shape, data_counter_time_resolved_bright_rotated.shape, data_counter_time_resolved_TRANSIENT_rotated.shape 
                 
        for hlp in range(2): #number of counter channels
            for hlp2 in range(self.no_frames):
                counter_rotated[hlp,hlp2] = np.flipud(np.rot90(data_counter_reshaped[hlp,hlp2]))
                
                if self.use_ttl_bb:
                    counter_rotated_bg_sub[hlp,hlp2] = np.flipud(np.rot90(data_counter_backgd_subtracted[hlp,hlp2]))
                    counter_rotated_bright[hlp,hlp2] = np.flipud(np.rot90(data_counter_bright_reshaped[hlp,hlp2]))
                     
                    if self.save_time_resolved_counts:
                        for hlp3 in range(self.int_clock_rate*self.no_points_at_same_pixel):
                            counter_time_resolved_rotated[hlp,hlp2,hlp3] = np.flipud(np.rot90(data_counter_time_resolved_reshaped[hlp,hlp2,hlp3]))                
                        for hlp3 in range(self.no_dark_count_samples):
                            data_counter_time_resolved_dark_rotated[hlp,hlp2,hlp3] = np.flipud(np.rot90(data_counter_time_resolved_dark_reshaped[hlp,hlp2,hlp3]))
                        for hlp3 in range(self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples):
                            data_counter_time_resolved_bright_rotated[hlp,hlp2,hlp3] = np.flipud(np.rot90(data_counter_time_resolved_bright_reshaped[hlp,hlp2,hlp3]))
                        for hlp3 in range(self.no_TRANSIENT_count_samples):
                            data_counter_time_resolved_TRANSIENT_rotated[hlp,hlp2,hlp3] = np.flipud(np.rot90(data_counter_time_resolved_TRANSIENT_reshaped[hlp,hlp2,hlp3]))
                           # print data_counter_time_resolved_TRANSIENT_reshaped.shape
        
        for hlp in range(self.no_ai_channels):
            for hlp2 in range(self.no_frames):
                AI_rotated[hlp,hlp2] = np.flipud(np.rot90(data_AI_reshaped[hlp,hlp2]))
                        
        if k_curr == 0:
            #compare filesrootname with what existed
            if not self.main_gui.configuration_widget.filesrootname == self.main_gui.configuration_widget.lineedit_filesrootname.text():
                self.main_gui.configuration_widget.filesrootname = self.main_gui.configuration_widget.lineedit_filesrootname.text()
                self.main_gui.configuration_widget.filenumber = 1 # If root name changed, go back to index 1 in pictures
         
            # FUTURE: Save some info in the tag of hdf5 file
            i = datetime.now()  
            fname_header=self.main_gui.configuration_widget.label_foldername.text() + os.sep + i.strftime('%Y-%m-%d-%H%M') + '_' + str(self.measurement.name)+ '_' + self.main_gui.configuration_widget.lineedit_filesrootname.text() + '_'
            
            # Choose to print with 3 digits after the ,
            parameter= "{:.3f}".format(self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Magnification'].read_from_hardware()/1e3)+'kX_'+"{:.3f}".format(self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['EHT'].read_from_hardware()/1000)+'kV_'+str(self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Aperture_choice'].choices[self.main_gui.hardware_widget.hardware['Microscope'].logged_quantities['Aperture_choice'].read_from_hardware()-1][0])[0:2]+'mu_'
            
            self.fname=  fname_header + parameter + str(self.main_gui.configuration_widget.filenumber)
            self.main_gui.configuration_widget.filenumber +=1
      
            if os.path.isfile(self.fname+'.hdf5') or os.path.isfile(self.fname+'.txt') or os.path.isfile(self.fname+'.xml'): #CHECK FOR OTHER ENDINGS AS WELL
                msg=QMessageBox()
                msg.setText('File name exist, currently being overwritten because protection not implemented yet!')
                msg.exec_()
                return None
            else: # create hdf5 file
                
                # Save metadata
                self.settings_save_ini()
                
                self.h5_file=h5py.File(self.main_gui.userdirectory_slash + os.sep + 'Data' + os.sep + self.fname+'.hdf5','w-')
                root = self.h5_file['/']
                root.attrs["ScopeFoundry_version"] = 100
                
                # Saving hardware logged quantities
                h5_hardware_group = root.create_group('hardware/')
                h5_hardware_group.attrs['ScopeFoundry_type'] = "HardwareList"
                for hc_name, hc in self.main_gui.hardware_widget.hardware.items():
                    h5_hc_group = h5_hardware_group.create_group(hc_name)
                    h5_hc_group.attrs['name'] = hc.name
                    h5_hc_group.attrs['ScopeFoundry_type'] = "Hardware"
                    h5_hc_settings_group = h5_hc_group.create_group("settings")
                    
                    unit_group = h5_hc_settings_group.create_group('units')
                    for lqname, lq in hc.logged_quantities.items():
                        h5_hc_settings_group.attrs[lqname] = lq.val
                        if lq.unit:
                            unit_group.attrs[lqname] = lq.unit
                
                # Saving measurement logged quantities
                h5_measurement_group = root.create_group('measurement/')
                h5_measurement_group.attrs['ScopeFoundry_type'] = "Measurement"
                h5_mc_settings_group = h5_measurement_group.create_group("settings")
                unit_group_m = h5_mc_settings_group.create_group('units')
                for lqname, lq in self.measurement.logged_quantities.items():
                        h5_mc_settings_group.attrs[lqname] = lq.val
                        if lq.unit:
                            unit_group_m.attrs[lqname] = lq.unit
            
                h5_data_group = root.create_group('data/')
                h5_data_group.attrs['ScopeFoundry_type'] = "Data"
                
                h5_counter1_group = h5_data_group.create_group("Counter channel 1 : " + self.main_gui.results_widget.fig_ch[0].lineedit_name.text())
                h5_counter2_group = h5_data_group.create_group("Counter channel 2 : " + self.main_gui.results_widget.fig_ch[1].lineedit_name.text())
                
                h5_dataset_group = [] 
                self.dataset_call = []
                # FUTURE: chunking datasets in (grid_x, grid_y) sizes

                # Simple image or movie
                if len(self.name_var_to_be_varied) == 0: # do not reshape
                          
                    maxshape  = (self.no_frames,self.grid_y,self.grid_x)
                    dim_names = ['no_frames','pixels','pixels']
                    
                    ### future: save as sec, the no of frames, and give as array the dist no pixels, also time between frames...
                    dim_units = ['','m','m']
                    dim_arrays= [np.array(range(self.no_frames)), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                    
                    # dim_imageJ for an image takes [pixel depth, pixel height, pixel width] = [0, pixel x, pixel y] in micron - for image J uniquely
                    dim_imageJ = np.array([0,self.pixel_y,self.pixel_x])
                    
                    # Counter
                    for k in range(2):
                        h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text())'))
                        self.dataset_call.append(self.h5_create_emd_dataset(h5_dataset_group[-1], # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated[k], 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                        
                        if self.use_ttl_bb:
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " background subtracted")'))
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " background subtracted"))
                            self.dataset_call.append(self.h5_create_emd_dataset(  
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bg_sub[k], 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " bright only"))
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " bright only")'))
                            self.dataset_call.append(self.h5_create_emd_dataset(    
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bright[k], 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                    
                            if self.save_time_resolved_counts:
                                
                                maxshapetr = (self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x)
                                dim_namestr = ['no_frames','time','pixels','pixels']
                        
                                ### future: save as sec, the no of frames, and give as array the dist no pixels, also time between frames...
                                dim_unitstr = ['','s','m','m']
                                dim_arraystr =[np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrd = (self.no_frames,self.no_dark_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrd=[np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_dark_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                                
                                maxshapetrb = (self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrb=[np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrl = (self.no_frames,self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrl=[np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    counter_time_resolved_rotated[k], 
                                                                                    maxshapetr, dim_namestr, dim_unitstr, dim_arraystr, dim_imageJ))
                         
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved DARK"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved DARK")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_dark_rotated[k], 
                                                                                    maxshapetrd, dim_namestr, dim_unitstr, dim_arraystrd, dim_imageJ))
                                
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved BRIGHT"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved BRIGHT")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_bright_rotated[k], 
                                                                                    maxshapetrb, dim_namestr, dim_unitstr, dim_arraystrb, dim_imageJ))
                                
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved TRANSIENT")'))
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved TRANSIENT"))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_TRANSIENT_rotated[k], 
                                                                                    maxshapetrl, dim_namestr, dim_unitstr, dim_arraystrl, dim_imageJ))
                  
                    # Analog in
                    # here k == 1 in the usual case 
                    for kk in range(self.no_ai_channels): 
                        h5_dataset_group.append(h5_data_group.create_group("Analog channel " + str(kk+1) + " : " + self.main_gui.results_widget.fig_ch[kk+2].lineedit_name.text()))
                        self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1], # h5_dataset_group[k + 1 + kk] or [-1] will do
                                                                            AI_rotated[kk], 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                    
                    self.h5_file.close()
                
                ################# TIME RESOLVED SAVING ONLY WORKING FOR IMAGE/MOVIE, no vary yet
                elif len(self.name_var_to_be_varied) == 1: # Needs reshaping
                    
                    maxshape =(len(self.array_of_sequences),self.no_frames,self.grid_y,self.grid_x)
                    dim_names=[self.name_var_to_be_varied[0],'no_frames','pixels','pixels']
                    dim_units =[self.name_var_to_be_varied_unit[0],'', 'm','m']
                    dim_arrays=[np.array(self.scan[0]),np.array(range(self.no_frames)),np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                    dim_imageJ = np.array([0,self.pixel_y,self.pixel_x]) 
                     
                    # Counter 
                    for k in range(2):
                        #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)))
                        h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text())'))
                        self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1], 
                                                                            counter_rotated[k].reshape(1,self.no_frames,self.grid_y,self.grid_x),
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ))
                        
                        if self.use_ttl_bb:
                    
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " background subtracted"))
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " background subtracted")'))
                            self.dataset_call.append(self.h5_create_emd_dataset(   
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bg_sub[k].reshape(1,self.no_frames,self.grid_y,self.grid_x), 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " bright only"))
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " bright only")'))
                            self.dataset_call.append(self.h5_create_emd_dataset(  
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bright[k].reshape(1,self.no_frames,self.grid_y,self.grid_x), 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ))
                    
                            if self.save_time_resolved_counts:
                                
                                maxshapetr = (len(self.array_of_sequences),self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x)
                                dim_namestr = [self.name_var_to_be_varied[0],'no_frames','time','pixels','pixels']
                        
                                ### future: save as sec, the no of frames, and give as array the dist no pixels, also time between frames...
                                dim_unitstr = [self.name_var_to_be_varied_unit[0],'','s','m','m']
                                dim_arraystr =[np.array(self.scan[0]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrd = (len(self.array_of_sequences),self.no_frames,self.no_dark_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrd=[np.array(self.scan[0]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_dark_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                            
                                maxshapetrb = (len(self.array_of_sequences),self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrb=[np.array(self.scan[0]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrl = (len(self.array_of_sequences),self.no_frames,self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrl=[np.array(self.scan[0]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    counter_time_resolved_rotated[k].reshape(1,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x), 
                                                                                    maxshapetr, dim_namestr, dim_unitstr, dim_arraystr, dim_imageJ))
                        
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved DARK"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved DARK")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_dark_rotated[k].reshape(1,self.no_frames,self.no_dark_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrd, dim_namestr, dim_unitstr, dim_arraystrd, dim_imageJ))
                                
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved BRIGHT"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved BRIGHT")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_bright_rotated[k].reshape(1,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrb, dim_namestr, dim_unitstr, dim_arraystrb, dim_imageJ))
                    
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved TRANSIENT"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved TRANSIENT")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_TRANSIENT_rotated[k].reshape(1,self.no_frames,self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrl, dim_namestr, dim_unitstr, dim_arraystrl, dim_imageJ))
                        
                    # Analog
                    # here k == 1 in the usual case
                    for kk in range(self.no_ai_channels): 
                        h5_dataset_group.append(h5_data_group.create_group("Analog channel " + str(kk+1) + " : " + self.main_gui.results_widget.fig_ch[kk+2].lineedit_name.text(),))
                        self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1], 
                                                                            AI_rotated[kk].reshape(1,self.no_frames,self.grid_y,self.grid_x),
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) # h5_dataset_group[k + 1 + kk] or [-1]
                    
                    
                  
                    
                elif len(self.name_var_to_be_varied) == 2:
                    
                    maxshape =(len(self.scan[self.outer]),len(self.scan[self.inner]),self.no_frames,self.grid_y,self.grid_x)
                    dim_names=[self.name_var_to_be_varied[self.outer],self.name_var_to_be_varied[self.inner],'no_frames','pixels','pixels']
                    dim_units =[self.name_var_to_be_varied_unit[self.outer], self.name_var_to_be_varied_unit[self.inner],'', 'm','m']
                    dim_arrays=[np.array(self.scan[self.outer]), np.array(self.scan[self.inner]),np.array(range(self.no_frames)),np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                    dim_imageJ = np.array([0,self.pixel_y,self.pixel_x])
                    
                    # Counter
                    for k in range(2):
                        #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)))
                        h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text())'))
                        self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1], 
                                                                            counter_rotated[k].reshape(1,1,self.no_frames,self.grid_y,self.grid_x),
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ))
                        
                        if self.use_ttl_bb:
                     
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " background subtracted"))
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " background subtracted")'))
                            self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bg_sub[k].reshape(1,1,self.no_frames,self.grid_y,self.grid_x), 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ)) 
                            #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1)  + " bright only"))
                            h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " bright only")'))
                            self.dataset_call.append(self.h5_create_emd_dataset(  
                                                                            h5_dataset_group[-1],  # h5_dataset_group[k] or [-1] will do
                                                                            counter_rotated_bright[k].reshape(1,1,self.no_frames,self.grid_y,self.grid_x), 
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ))
                    
                            if self.save_time_resolved_counts:
                                
                                maxshapetr = (len(self.scan[self.outer]),len(self.scan[self.inner]),self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x)
                                dim_namestr = [self.name_var_to_be_varied[self.outer],self.name_var_to_be_varied[self.inner],'no_frames','time','pixels','pixels']
                        
                                ### future: save as sec, the no of frames, and give as array the dist no pixels, also time between frames...
                                dim_unitstr = [self.name_var_to_be_varied_unit[self.outer], self.name_var_to_be_varied_unit[self.inner],'','s','m','m']
                                dim_arraystr =[np.array(self.scan[self.outer]), np.array(self.scan[self.inner]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrd = (len(self.scan[self.outer]),len(self.scan[self.inner]),self.no_frames,self.no_dark_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrd=[np.array(self.scan[self.outer]), np.array(self.scan[self.inner]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_dark_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
                                
                                maxshapetrb = (len(self.scan[self.outer]),len(self.scan[self.inner]),self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrb=[np.array(self.scan[self.outer]), np.array(self.scan[self.inner]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                maxshapetrl = (len(self.scan[self.outer]),len(self.scan[self.inner]),self.no_frames,self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x)
                                dim_arraystrl=[np.array(self.scan[self.outer]), np.array(self.scan[self.inner]),np.array(range(self.no_frames)),np.array([float(x)/self.counter_clock_rate for x in range(self.no_TRANSIENT_count_samples)]), np.array(range(self.grid_y)),np.array(range(self.grid_x))]
    
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    counter_time_resolved_rotated[k].reshape(1,1,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel,self.grid_y,self.grid_x), 
                                                                                    maxshapetr, dim_namestr, dim_unitstr, dim_arraystr, dim_imageJ))
                            
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved DARK"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved DARK")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_dark_rotated[k].reshape(1,1,self.no_frames,self.no_dark_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrd, dim_namestr, dim_unitstr, dim_arraystrd, dim_imageJ))
                            
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved BRIGHT"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved BRIGHT")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_bright_rotated[k].reshape(1,1,self.no_frames,self.int_clock_rate*self.no_points_at_same_pixel-self.no_dark_count_samples-self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrb, dim_namestr, dim_unitstr, dim_arraystrb, dim_imageJ))
                                
                                #h5_dataset_group.append(h5_data_group.create_group("Counter channel " + str(k+1) + " time-resolved TRANSIENT"))
                                h5_dataset_group.append(eval('h5_counter' + str(k+1) +'_group.create_group(self.main_gui.results_widget.fig_ch[k].lineedit_name.text() + " time-resolved TRANSIENT")'))
                                self.dataset_call.append(self.h5_create_emd_dataset(
                                                                                    h5_dataset_group[-1], 
                                                                                    data_counter_time_resolved_bright_rotated[k].reshape(1,1,self.no_frames,self.no_TRANSIENT_count_samples,self.grid_y,self.grid_x), 
                                                                                    maxshapetrl, dim_namestr, dim_unitstr, dim_arraystrl, dim_imageJ))
                        
                    # Analog 
                    # here k == 1 in the usual case
                    for kk in range(self.no_ai_channels): 
                        h5_dataset_group.append(h5_data_group.create_group("Analog channel " + str(kk+1) + " : " + self.main_gui.results_widget.fig_ch[kk+2].lineedit_name.text()))
                        self.dataset_call.append(self.h5_create_emd_dataset(
                                                                            h5_dataset_group[-1], 
                                                                            AI_rotated[kk].reshape(1,1,self.no_frames,self.grid_y,self.grid_x),
                                                                            maxshape, dim_names, dim_units, dim_arrays, dim_imageJ))       
        else:
            
                if not self.use_ttl_bb:
                #if not using TTL, 1 dataset per channel
                    fac = 1
                else:
                    if not self.save_time_resolved_counts:
                    #if not saving time-resolved counts, 3 datasets per channel
                        fac = 3
                    else:
                    #7 datasets
                        fac = 7
            
                if len(self.name_var_to_be_varied) == 1:   
                    
                    for k in range(2):
                        self.dataset_call[fac*k]['data'].resize((self.dataset_call[fac*k]['data'].shape[0]+1,self.dataset_call[fac*k]['data'].shape[1],self.dataset_call[fac*k]['data'].shape[2],self.dataset_call[fac*k]['data'].shape[3]))
                        self.dataset_call[fac*k]['data'][k_curr,:,:,:] = counter_rotated[k]
                       
                        if self.use_ttl_bb:
                            
                                self.dataset_call[fac*k+1]['data'].resize((self.dataset_call[fac*k+1]['data'].shape[0]+1,self.dataset_call[fac*k+1]['data'].shape[1],self.dataset_call[fac*k+1]['data'].shape[2],self.dataset_call[fac*k+1]['data'].shape[3]))
                                self.dataset_call[fac*k+1]['data'][k_curr,:,:,:] = counter_rotated_bg_sub[k]
                                
                                self.dataset_call[fac*k+2]['data'].resize((self.dataset_call[fac*k+2]['data'].shape[0]+1,self.dataset_call[fac*k+2]['data'].shape[1],self.dataset_call[fac*k+2]['data'].shape[2],self.dataset_call[fac*k+2]['data'].shape[3]))
                                self.dataset_call[fac*k+2]['data'][k_curr,:,:,:] = counter_rotated_bright[k]
                         
                                if self.save_time_resolved_counts:
                                    
                                    self.dataset_call[fac*k+3]['data'].resize((self.dataset_call[fac*k+3]['data'].shape[0]+1,self.dataset_call[fac*k+3]['data'].shape[1],self.dataset_call[fac*k+3]['data'].shape[2],self.dataset_call[fac*k+3]['data'].shape[3],self.dataset_call[fac*k+3]['data'].shape[4]))
                                    self.dataset_call[fac*k+3]['data'][k_curr,:,:,:,:] = counter_time_resolved_rotated[k]
                                    
                                    self.dataset_call[fac*k+4]['data'].resize((self.dataset_call[fac*k+4]['data'].shape[0]+1,self.dataset_call[fac*k+4]['data'].shape[1],self.dataset_call[fac*k+4]['data'].shape[2],self.dataset_call[fac*k+4]['data'].shape[3],self.dataset_call[fac*k+4]['data'].shape[4]))
                                    self.dataset_call[fac*k+4]['data'][k_curr,:,:,:,:] = data_counter_time_resolved_dark_rotated[k]
                                    
                                    self.dataset_call[fac*k+5]['data'].resize((self.dataset_call[fac*k+5]['data'].shape[0]+1,self.dataset_call[fac*k+5]['data'].shape[1],self.dataset_call[fac*k+5]['data'].shape[2],self.dataset_call[fac*k+5]['data'].shape[3],self.dataset_call[fac*k+5]['data'].shape[4]))
                                    self.dataset_call[fac*k+5]['data'][k_curr,:,:,:,:] = data_counter_time_resolved_bright_rotated[k]
                                    
                                    self.dataset_call[fac*k+6]['data'].resize((self.dataset_call[fac*k+6]['data'].shape[0]+1,self.dataset_call[fac*k+6]['data'].shape[1],self.dataset_call[fac*k+6]['data'].shape[2],self.dataset_call[fac*k+6]['data'].shape[3],self.dataset_call[fac*k+6]['data'].shape[4]))
                                    self.dataset_call[fac*k+6]['data'][k_curr,:,:,:,:] = data_counter_time_resolved_bright_rotated[k]
                            
                    for kk in range(self.no_ai_channels): # LAst two datasets are always analog channels
                        #self.dataset_call[k+1+kk]['data'].resize((self.dataset_call[k+1+kk]['data'].shape[0]+1,self.dataset_call[k+1+kk]['data'].shape[1],self.dataset_call[k+1+kk]['data'].shape[2],self.dataset_call[k+1+kk]['data'].shape[3]))
                        #self.dataset_call[k+1+kk]['data'][k_curr,:,:,:] = AI_rotated[k]
                        self.dataset_call[-1-1+kk]['data'].resize((self.dataset_call[-1-1+kk]['data'].shape[0]+1,self.dataset_call[-1-1+kk]['data'].shape[1],self.dataset_call[-1-1+kk]['data'].shape[2],self.dataset_call[-1-1+kk]['data'].shape[3]))
                        self.dataset_call[-1-1+kk]['data'][k_curr,:,:,:] = AI_rotated[kk]
                    
                    if k_curr == len(self.array_of_sequences) - 1:
                        self.h5_file.close()
                    
                elif len(self.name_var_to_be_varied) == 2:
                    # break down into 2: outer and inner
                    
                        for k in range(2):
                            self.dataset_call[fac*k]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k]['data'].shape[2],self.dataset_call[fac*k]['data'].shape[3],self.dataset_call[fac*k]['data'].shape[4]))
                            self.dataset_call[fac*k]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:] = counter_rotated[k] #np.flipud(np.rot90(data_counter_reshaped[k]))
                        
                            if self.use_ttl_bb:
                            
                                self.dataset_call[fac*k+1]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+1]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+1]['data'].shape[2],self.dataset_call[fac*k+1]['data'].shape[3],self.dataset_call[fac*k+1]['data'].shape[4]))
                                self.dataset_call[fac*k+1]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:] = counter_rotated_bg_sub[k]
                                
                                self.dataset_call[fac*k+2]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+2]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+2]['data'].shape[2],self.dataset_call[fac*k+2]['data'].shape[3],self.dataset_call[fac*k+2]['data'].shape[4]))
                                self.dataset_call[fac*k+2]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:] = counter_rotated_bright[k]
                         
                                if self.save_time_resolved_counts:
                                    
                                    self.dataset_call[fac*k+3]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+3]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+3]['data'].shape[2],self.dataset_call[fac*k+3]['data'].shape[3],self.dataset_call[fac*k+3]['data'].shape[4],self.dataset_call[fac*k+3]['data'].shape[5]))
                                    self.dataset_call[fac*k+3]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:,:] = counter_time_resolved_rotated[k]
                                    
                                    self.dataset_call[fac*k+4]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+4]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+4]['data'].shape[2],self.dataset_call[fac*k+4]['data'].shape[3],self.dataset_call[fac*k+4]['data'].shape[4],self.dataset_call[fac*k+4]['data'].shape[5]))
                                    self.dataset_call[fac*k+4]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:,:] = data_counter_time_resolved_dark_rotated[k]
                                    
                                    self.dataset_call[fac*k+5]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+5]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+5]['data'].shape[2],self.dataset_call[fac*k+5]['data'].shape[3],self.dataset_call[fac*k+5]['data'].shape[4],self.dataset_call[fac*k+5]['data'].shape[5]))
                                    self.dataset_call[fac*k+5]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:,:] = data_counter_time_resolved_bright_rotated[k]
                                    
                                    self.dataset_call[fac*k+6]['data'].resize(( k_curr//len(self.scan[self.inner]) + 1 , min(self.dataset_call[fac*k+6]['data'].shape[1]+1, len(self.scan[self.inner])),self.dataset_call[fac*k+6]['data'].shape[2],self.dataset_call[fac*k+6]['data'].shape[3],self.dataset_call[fac*k+6]['data'].shape[4],self.dataset_call[fac*k+6]['data'].shape[5]))
                                    self.dataset_call[fac*k+6]['data'][ k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:,:] = data_counter_time_resolved_bright_rotated[k]
                        
                        for kk in range(self.no_ai_channels):  # range(2): 
                            #self.dataset_call[k+1+kk]['data'].resize((k_curr//len(self.scan[self.inner]) + 1, min(self.dataset_call[k+1+kk]['data'].shape[1]+1,len(self.scan[self.inner]) ),self.dataset_call[k+1+kk]['data'].shape[2],self.dataset_call[k+1+kk]['data'].shape[3],self.dataset_call[k+1+kk]['data'].shape[4]))
                            #self.dataset_call[k+1+kk]['data'][k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:] = AI_rotated[k] 
                            self.dataset_call[-1-1+kk]['data'].resize((k_curr//len(self.scan[self.inner]) + 1, min(self.dataset_call[-1-1+kk]['data'].shape[1]+1,len(self.scan[self.inner]) ),self.dataset_call[-1-1+kk]['data'].shape[2],self.dataset_call[-1-1+kk]['data'].shape[3],self.dataset_call[-1-1+kk]['data'].shape[4]))
                            self.dataset_call[-1-1+kk]['data'][k_curr//len(self.scan[self.inner]) , k_curr%len(self.scan[self.inner]),:,:,:] = AI_rotated[kk] 

                    
                        if k_curr == len(self.array_of_sequences) - 1:
                            self.h5_file.close()
                    
    def h5_create_emd_dataset(self,name, data,maxshape, dim_names, dim_units, dim_arrays, dim_quantum_sizes=None, shape=None, **kwargs):     
                    
        #set the emd version tag at root of h5 file
        #h5parent.file['/'].attrs['version_major'] = 0
        #h5parent.file['/'].attrs['version_minor'] = 2
        
        from matplotlib import pyplot
        pyplot.acorr
        
        # create the EMD data group
        emd_grp = name
        emd_grp.attrs['emd_group_type'] = 1
        
        if data is not None:
            shape = data.shape
        
        # data set where the N-dim data is stored
        data_dset = emd_grp.create_dataset("data", shape=shape, maxshape=maxshape, data=data, **kwargs) 
        
        if dim_quantum_sizes is not None:
            data_dset.attrs['element_size_um'] = dim_quantum_sizes ### for image J
            # pixel DEPTH/HEIGHT/WIDTH

        if dim_arrays is not None: assert len(dim_arrays) == len(shape)
        if dim_names  is not None: assert len(dim_names)  == len(shape)
        if dim_units  is not None: assert len(dim_units)  == len(shape)
        if maxshape   is not None: assert len(maxshape)   == len(shape)
        
        # Create the dimension array datasets
        for ii in range(len(shape)):
            if dim_arrays is not None:
                dim_array = dim_arrays[ii]
                dim_dtype =  dim_array.dtype            
            else:
                dim_array = None
                dim_dtype = float
            if dim_names is not None:
                dim_name = np.string_(dim_names[ii])
            else:
                dim_name = np.string_("dim" + str(ii+1))
            if dim_units is not None:
                dim_unit = np.string_(dim_units[ii])
            else:
                dim_unit = None
            if maxshape is not None:
                dim_maxshape = (maxshape[ii],)
            else:
                dim_maxshape = None
            
            # create dimension array dataset
            numbering = len(shape) - ii
            dim_dset = emd_grp.create_dataset("dim" + str(numbering), shape=(maxshape[ii],), 
                                               dtype=dim_dtype, data=dim_array, 
                                               maxshape=dim_maxshape)
#             dim_dset = emd_grp.create_dataset("dim" + str(ii+1), shape=(maxshape[ii],), 
#                                                dtype=dim_dtype, data=dim_array, 
#                                                maxshape=dim_maxshape)
            
            dim_dset.attrs['name'] = np.string_(dim_name)
            if dim_unit is not None:
                dim_dset.attrs['unit'] = np.string_(dim_unit)
                
        return emd_grp
    
    def settings_save_ini(self): 
        
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        #if save_gui:
            #config.add_section('gui')
            #for lqname, lq in self.logged_quantities.items():
               # config.set('gui', lqname, lq.val)
        #if save_hardware:
        for hc_name, hc in self.main_gui.hardware_widget.hardware.items():
                section_name = 'Hardware/'+hc_name            
                config.add_section(section_name)
                for lqname, lq in hc.logged_quantities.items():
                    #if not lq.ro or save_ro:
                    
                    if not lq.is_varied:
                        if not lq.unit is None:
                            config.set(section_name, lqname, str(lq.val) + str(lq.unit))
                        else:
                            config.set(section_name, lqname, str(lq.val))
                    else:
                        if hasattr(self, 'outer'):
                            if self.name_var_to_be_varied[self.outer] is lq.name:
                                config.set(section_name, lqname, [lq.start, lq.step, lq.stop, 'outer loop']) 
                            else:
                                config.set(section_name, lqname, [lq.start, lq.step, lq.stop, 'inner loop']) 
                        else:
                            config.set(section_name, lqname, [lq.start, lq.step, lq.stop])
        #if save_measurements:
        #for meas_name, measurement in self.measurement.items():
        section_name = 'Measurement'#+meas_name            
        config.add_section(section_name)
        for lqname, lq in self.measurement.logged_quantities.items():
                    #if not lq.ro or save_ro:
                        #print lqname
                        #print lq.val
                    if not lq.is_varied:
                        if not lq.unit is None:
                            config.set(section_name, lqname, str(lq.val) + str(lq.unit))
                        else:
                            config.set(section_name, lqname, str(lq.val))
                    else:
                        if hasattr(self, 'outer'):
                            if self.name_var_to_be_varied[self.outer] is lq.name:
                                config.set(section_name, lqname, [lq.start, lq.step, lq.stop, 'outer loop']) 
                            else:
                                config.set(section_name, lqname, [lq.start, lq.step, lq.stop, 'inner loop']) 
                        else:
                            config.set(section_name, lqname, [lq.start, lq.step, lq.stop])
        with open(self.main_gui.userdirectory_slash + os.sep + 'Data' + os.sep + self.fname +'.txt', 'wb') as configfile:
            config.write(configfile)
        
        #print "ini settings saved to", self.fname, config.optionxform
    
    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.sequence.logged_quantities[name] = lq
        return lq
        
    def stop_clicked(self):
        
        self.start_is_on = False
        self.abort_scan = 1
        
        self.main_gui.configuration_widget.lineedit_filesrootname.setEnabled(True) 
        self.main_gui.hardware_widget.scrollArea_hardware.setEnabled(True)
        self.main_gui.results_widget.roi_button.setEnabled(True)
        self.main_gui.results_widget.reset_roi_button.setEnabled(True)
        self.main_gui.results_widget.button_count.setEnabled(True)
        self.scrollArea_measurement.setEnabled(True)
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)   
    
        #if self.h5_file in globals():
           # self.h5_file.close()

        if hasattr(self, 'h5_file'):
            self.h5_file.close()
    
        #if self.h5_file:
         #   self.h5_file.close()

        #self.progressbar_vary.setValue(0.0)
        self.progressbar.setValue(0.0)
        
        # release beam blank
        if self.use_ttl_bb:
            self.main_gui.hardware_widget.hardware['DAC'].dummy(is_high=0)
      
    def my_msg_box(self,input_text):
        msgBox = QMessageBox()
        msgBox.setText(input_text)
        msgBox.exec_(); 
        
    def my_repl(self,name_var,name_var_type,rest):
        if name_var_type is 'Measurement':
            my_string = 'self.measurement.logged_quantities[\'' + name_var + '\']' + rest
        else: # name_var_type is a hardware component
            my_string = 'self.main_gui.hardware_widget.hardware[\'' + name_var_type + '\'].logged_quantities[\'' + name_var + '\']' + rest
           
        return my_string
    
    def plot_scan_pattern(self):
        
        pass
    
        # take self.scan_shape.scan_pattern [x1 y1 x2 y2 ...]
        
        #self.compute_scan_params()
            
        #self.clear_qt_attr('graph_layout')
        #self.graph_layout=pg.GraphicsLayoutWidget(border=(100,100,100))
        #self.plot_scan.addWidget(self.graph_layout)
        
        #self.clear_qt_attr('img_plot')
        #self.img_plot = self.graph_layout.addPlot()
        #self.img_item = pg.ImageItem()
        #self.img_plot.addItem(self.img_item)
        #self.img_plot.showGrid(x=True, y=True)
        #self.img_plot.setAspectLocked(lock=True, ratio=1)
        
        
        #self.clear_qt_attr('current_stage_pos_arrow')
        #self.current_stage_pos_arrow = pg.ArrowItem()
        #self.current_stage_pos_arrow.setZValue(100)
        #self.img_plot.addItem(self.current_stage_pos_arrow)
        
        #self.stage = self.gui.hardware_components['dummy_xy_stage']
        #self.stage.x_position.updated_value.connect(self.update_arrow_pos, Qt.UniqueConnection)
        #self.stage.y_position.updated_value.connect(self.update_arrow_pos, Qt.UniqueConnection)
        
        #self.graph_layout.nextRow()
        #self.pos_label = pg.LabelItem(justify='right')
        #self.pos_label.setText("=====")
        #self.graph_layout.addItem(self.pos_label)

        #self.scan_roi = pg.ROI([0,0],[1,1], movable=True)
        #self.scan_roi.addScaleHandle([1, 1], [0, 0])
        #self.scan_roi.addScaleHandle([0, 0], [1, 1])
        #self.update_scan_roi()
        #self.scan_roi.sigRegionChangeFinished.connect(self.mouse_update_scan_roi)
        
        #self.img_plot.addItem(self.scan_roi)        
        #for lqname in 'h0 h1 v0 v1 dh dv'.split():
       #     self.logged_quantities[lqname].updated_value.connect(self.update_scan_roi)
                    
        #self.img_plot.scene().sigMouseMoved.connect(self.mouseMoved)
      
class my_ui():

    def __init__(self):
        
        self.measurement_tab_scrollArea_content_widget = my_measurement_widget()
        
class my_measurement_widget(QWidget):

    def __init__(self):
        super(my_measurement_widget, self).__init__()
        self.setLayout(QVBoxLayout())
        
class Reporter(QObject):
        
        progress=Signal(int)
        done=Signal(bool)     