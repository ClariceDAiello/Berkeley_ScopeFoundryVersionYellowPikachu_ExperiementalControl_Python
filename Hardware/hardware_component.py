from PySide.QtCore import *
from PySide.QtGui  import *
from HelperFunctions.logged_quantity import LoggedQuantity
from HelperFunctions.scientific_double_spin_box import ScientificDoubleSpinBox
from collections import OrderedDict
import pyqtgraph as pg

class HardwareComponent(QObject):

    def add_logged_quantity(self, name, **kwargs):
        lq = LoggedQuantity(name=name, **kwargs)
        self.logged_quantities[name] = lq
        return lq

#     def add_operation(self, name, op_func):
#         """type name: str
#            type op_func: QtCore.Slot
#         """
#         self.operations[name] = op_func   
            
    def __init__(self, gui):
        """type gui: BaseGUI
        """        
        QObject.__init__(self)

        self.gui = gui
        
        self.operations = OrderedDict()
    
        self.setup() #setup function declared inside each particular hardware component
        
        self._add_control_widgets_to_hardware_tab()
        
        #self.has_been_connected_once = False
        
        #self.is_connected = False
        
#     def setup(self):
#         """
#         Runs during __init__, before the hardware connection is established
#         Should generate desired LoggedQuantities, operations
#         """
#         raise NotImplementedError()

    def _add_control_widgets_to_hardware_tab(self):
        cwidget = self.gui.ui.hardware_tab_scrollArea_content_widget
        
        self.controls_groupBox = QGroupBox(self.name)
        
        #self.controls_groupBox.setFixedHeight(900)
        
        #self.controls_formLayout = QFormLayout()
        
        self.controls_formLayout = QVBoxLayout()

        self.controls_groupBox.setLayout(self.controls_formLayout)
        
        cwidget.layout().addWidget(self.controls_groupBox)
          
        self.control_widgets = OrderedDict()
        my_k = 0
        for lqname, lq in self.logged_quantities.items():
            if lq.displayFlag == True:
            
                #instead add the label box to the hboxes


                if lq.choices is not None:
                    widget = QComboBox()
                elif lq.dtype in [int, float]:
                    widget = ScientificDoubleSpinBox() #pg.SpinBox() <- original
                elif lq.dtype in [bool]:
                    widget = QCheckBox()  
                elif lq.dtype in [str]:
                    widget = QLineEdit()
                
                my_height = 25  # 25 #original 25
                widget.setFixedSize(75, my_height) 
                unit_box = QLabel(lq.unit)
                unit_box.setFixedSize(25, my_height) 
                is_varied = QCheckBox()
                is_varied.setFixedSize(25, my_height) 
                
                #hbox = QHBoxLayout() #
                hbox = QWidget()
                hbox.setLayout(QHBoxLayout()) #
       
                start = ScientificDoubleSpinBox() #QDoubleSpinBox()
                start.setFixedSize(60, my_height) 
                step = ScientificDoubleSpinBox() #QDoubleSpinBox()
                step.setFixedSize(60, my_height) 
                stop = ScientificDoubleSpinBox() #QDoubleSpinBox()
                stop.setFixedSize(60, my_height) 
                
                name_box = QLabel(lqname)
                name_box.setFixedSize(150, my_height)
                
                name_box.setContentsMargins(0, 0, 0, 0);
                unit_box.setContentsMargins(0, 0, 0, 0);
                start.setContentsMargins(0, 0, 0, 0);
                step.setContentsMargins(0, 0, 0, 0);
                stop.setContentsMargins(0, 0, 0, 0);
                is_varied.setContentsMargins(0, 0, 0, 0);
                widget.setContentsMargins(0, 0, 0, 0);

                cont_height = 35
                self.container0 = QWidget()
                self.container0.setLayout(QHBoxLayout())
                self.container0.layout().addWidget(name_box, 0)
                self.container0.setFixedHeight(cont_height)
                self.container0.setContentsMargins(0, 0, 0, 0);

                self.container = QWidget()
                self.container.setLayout(QHBoxLayout())
                self.container.layout().addWidget(unit_box, 0)
                self.container.setFixedHeight(cont_height)
                self.container.setContentsMargins(0, 0, 0, 0);
                #self.container.setFixedWidth(30)
                
                self.container2 = QWidget()
                self.container2.setLayout(QHBoxLayout())
                self.container2.layout().addWidget(widget, 0)
                self.container2.setFixedHeight(cont_height)
                self.container2.setContentsMargins(0, 0, 0, 0);
                #self.container2.setFixedWidth(75)
                
                self.container3 = QWidget()
                self.container3.setLayout(QHBoxLayout())
                self.container3.layout().addWidget(start, 0)
                self.container3.setFixedHeight(cont_height)
                self.container3.setContentsMargins(0, 0, 0, 0);
                #self.container3.setFixedWidth(60)
                
                self.container4 = QWidget()
                self.container4.setLayout(QHBoxLayout())
                self.container4.layout().addWidget(step, 0)
                self.container4.setFixedHeight(cont_height)
                self.container4.setContentsMargins(0, 0, 0, 0);
                #self.container4.setFixedWidth(60)
                
                self.container5 = QWidget()
                self.container5.setLayout(QHBoxLayout())
                self.container5.layout().addWidget(stop, 0)
                self.container5.setFixedHeight(cont_height)
                self.container5.setContentsMargins(0, 0, 0, 0);
                #self.container5.setFixedWidth(60)  
                
                self.container6 = QWidget()
                self.container6.setLayout(QHBoxLayout())
                self.container6.layout().addWidget(is_varied, 0)
                self.container6.setFixedHeight(cont_height)
                self.container6.setContentsMargins(0, 0, 0, 0);
                #self.container6.setFixedWidth(10) 
               
                hbox.layout().addWidget(self.container0, 0)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()

                hbox.layout().addWidget(self.container, 1)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()
                hbox.layout().addWidget(self.container2, 2)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()
                hbox.layout().addWidget(self.container6, 3)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()
                hbox.layout().addWidget(self.container3, 4)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()
                hbox.layout().addWidget(self.container4, 5)
                hbox.layout().addStretch()
                hbox.layout().setSpacing(0)
                hbox.layout().addStretch()
                hbox.layout().addWidget(self.container5, 6)
                
                start.setVisible(False)
                step.setVisible(False)
                stop.setVisible(False)
                
                self.controls_formLayout.setSpacing(0);
               
                hbox.setFixedHeight(42)
                hbox.setContentsMargins(0, 0, 0, 0)
                hbox.adjustSize()
                
                self.controls_formLayout.addWidget(hbox, Qt.AlignTop)

                self.control_widgets[lqname] = [widget, is_varied, start, step, stop]
                
                if not lq.is_variable:
                   is_varied.hide()
                
                
            

        self.op_buttons = OrderedDict()
        for op_name, op_func in self.operations.items(): 
            op_button = QtGui.QPushButton(op_name)
            op_button.clicked.connect(op_func)
            self.controls_formLayout.addRow(op_name, op_button)
        

        # should not need to read from hw if it is truly bidirectional; after a couple of secs at most should load params
       
        

    @Slot()    
    def read_from_hardware(self):
        for name, lq in self.logged_quantities.items():
           # print "read_from_hardware", name
            lq.read_from_hardware()
            