'''
Hardware widget inside SEMGUI
'''

from PySide.QtCore import *
from PySide.QtGui import *

from collections import OrderedDict

# Import helper functions
from HelperFunctions import *

class SetHardwareWidget(QWidget):
    
    def __init__(self,main_gui):
        super(SetHardwareWidget, self).__init__() # super() lets you avoid referring to the base class explicitly

        # Define the Hardware Widget; this is used in Hardware Component class
        self.ui = my_ui()
        
        self.main_gui = main_gui
        
        # Instantiate hardware dictionary
        self.hardware = {}
        
        if self.main_gui.MainConfig.Simulate_experiment:
           print "Simulating hardware components..."    
           simu_string = '_simu'
        else:
           print "Adding hardware components..."  
           simu_string = '' 
            
        self.cont_read_is_done = True
        # Import hardware components
        # FUTURE: import all available files hardware files from the hardware folder 
        # original
        exec('from Hardware.SEM.sem_zeiss' + simu_string + ' import SEMZeiss as Microscope')
        # hack
        #exec('from Hardware.SEM.sem_zeiss' + '_simu' + ' import SEMZeiss as Microscope')
        self.add_hardware_component(Microscope(self,self.main_gui)) #makes self.hardware['Microscope'] WHICH IS A DICT; values accessible via self.hardware['Microscope'].EHT.val
        exec('from Hardware.DataAcquisitionCard.dac_ni' + simu_string + ' import DACNI as DAC')
        self.add_hardware_component(DAC(self,self.main_gui))
        #print "Hardware components added!"  
        
        # Define Load and Save Buttons
        self.label_hardware = QLabel('Config of hardware', self)
        font = QFont("Sans Serif", 12, QFont.Bold)
        self.label_hardware.setFont(font)
        self.button_loadconfig = QPushButton('Load config', self)
        self.button_loadconfig.setVisible(False)
        self.button_saveconfig = QPushButton('Save config', self)
        self.button_saveconfig.setVisible(False)
        self.label_namecurrenthardwareconfig = QLabel('Name of current hardware config:', self)
        self.label_namecurrenthardwareconfig.setVisible(False)
        
        self.label_warning = QLabel("<font color=\"red\">Enter a value and press return</font> <font color=\"black\">or use arrows to set new value!</font>", self)

        # Define scrollArea
        self.scrollArea_hardware = QScrollArea()
        self.scrollArea_hardware.setWidgetResizable(True)
        self.scrollArea_hardware.setWidget(self.ui.hardware_tab_scrollArea_content_widget)
        # Make the scroll area as wide as the widget
        self.scrollArea_hardware.setMinimumWidth(10+self.sizeHint().width())    
        
        # Defining the layout
        self.layout = QGridLayout()

        self.layout.addWidget(self.label_hardware, 0, 0,1,1)
        #self.layout.addWidget(self.button_loadconfig, 0, 1,1,1)  
        #self.layout.addWidget(self.button_saveconfig, 0,2,1,1)  
        self.layout.addWidget(self.label_warning, 1, 0)
        self.layout.addWidget(self.label_namecurrenthardwareconfig,2,0)
        self.layout.addWidget(self.scrollArea_hardware, 3, 0, 1, 3)
        
        self.button_readfromhardware = QPushButton('Read from hardware',self)
        #self.button_readfromhardware.clicked.connect(lambda: self.newfc())  ##### CANT MAKE THIS WORK!!!!!! 
        self.layout.addWidget(self.button_readfromhardware, 0, 2,1,1)  
       
        #self.button_readfromhardware.clicked.connect(lambda: self.read_from_all_hardware())
        
        self.setLayout(self.layout)
        
        for hardware_component in self.hardware.keys():
            for logged_variable in self.hardware[hardware_component].control_widgets:
                # Connect all the hardware components to the hardware widget
                # Changes in the widget are reflected in logged quantities
                self.hardware[hardware_component].logged_quantities[logged_variable].connect_bidir_to_widget(self.hardware[hardware_component].control_widgets[logged_variable])
            # Read from hardware; return the current state of all logged quantities pertaining to the hardware components 
            self.hardware[hardware_component].read_from_hardware() 
            # FUTURE: save this as the initial config of the day
            
        
        #self.button_readfromhardware.clicked.connect(lambda: self.newfc())   
            
   
    def add_hardware_component(self,hc):
        
        self.hardware[hc.name] = hc 
        
    def newfc(self):
        #pass
        #print "from inside functionm"
        
        self.cont_read_is_done = False
        
        for hardware_component in self.hardware.keys():
             self.hardware[hardware_component].read_from_hardware() 
           
        self.cont_read_is_done = True 

class my_ui():

    def __init__(self):

        self.hardware_tab_scrollArea_content_widget = my_hardware_widget()


class my_hardware_widget(QWidget):

    def __init__(self):
        super(my_hardware_widget, self).__init__()
        self.setLayout(QVBoxLayout())