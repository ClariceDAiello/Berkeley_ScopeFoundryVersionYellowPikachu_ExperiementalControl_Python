
import pyqtgraph

from PySide import  QtCore, QtGui

class LoggedQuantity(QtCore.QObject):

    updated_value = QtCore.Signal((float,),(int,),(bool,), (), (str,),) # signal sent when value has been updated
    updated_text_value = QtCore.Signal(str)
    updated_choice_index_value = QtCore.Signal(int) # emits the index of the value in self.choices
    
    ############################ CDA: DO SOMETHING SO THAT THEY ALL NEED TO BE INITIALIZED, DONT GIVE ANY OTHER VALUE OW CAN CRASH SOFTWARE!!!!!!
    def __init__(self, name, dtype=float, 
                 hardware_read_func=None, hardware_set_func=None, 
                 initial=0, fmt="%10.10f",
                 ro = False,
                 unit = None,
                 vmin=None, vmax=None,displayFlag=True, choices=None,is_variable=None,start=0,step=0,stop=0,is_varied=False):
    
        QtCore.QObject.__init__(self)
        
        self.no_decimals = 10
        
        self.is_varied = is_varied
        self.is_variable = is_variable
        self.name = name
        self.dtype = dtype
        if dtype is int: # allows int type to be written in scientific form, ex: 1e3
           self.val =  dtype(float(initial))
           self.vmin = dtype(float(vmin))
           self.vmax = dtype(float(vmax))
        elif dtype is bool:   
           if type(initial) is bool:
               self.val = initial
           elif type(initial) is str:    
               self.val = eval(initial)
           self.vmin = False
           self.vmax = True
        else:    
           self.val = dtype(initial)
           self.vmin = dtype(vmin)
           self.vmax = dtype(vmax)
           
        self.hardware_read_func = hardware_read_func
        self.hardware_set_func = hardware_set_func
        self.fmt = fmt # string formatting string. This is ignored if dtype==str
        self.unit = unit
        self.start = start
        self.step = step
        self.stop = stop
        self.displayFlag = displayFlag
        self.choices = choices # must be tuple [ ('name', val) ... ]
        self.ro = ro # Read-Only
        
        self.oldval = None
        
    def read_from_hardware(self, send_signal=True):
        if self.hardware_read_func:
            self.oldval = self.val
            #print "read_from_hardware", self.name
            self.val = self.dtype(self.hardware_read_func())
            #if send_signal:
               # self.send_display_updates()
        if send_signal:
                self.send_display_updates()
        return self.val

    @QtCore.Slot(str)
    @QtCore.Slot(float)
    @QtCore.Slot(int)
    @QtCore.Slot(bool)
    @QtCore.Slot()
    def update_value(self, new_val=None, update_hardware=True, send_signal=True):
        self.oldval = self.val
        
        if new_val == None:
            new_val = self.sender().text()
        self.val = self.dtype(new_val)
        if update_hardware and self.hardware_set_func:
            self.hardware_set_func(self.val)
        if send_signal:
            self.send_display_updates()
            
        ######################## hard code HERE DEPENDENCIES AMONG SYSTEM PARAMS
            
    def send_display_updates(self, force=False):
        #print "send_display_updates: {} force={}".format(self.name, force)
        if (self.oldval != self.val) or (force):
            
            #print "send display updates", self.name, self.val, self.oldval
            if self.dtype == str:
                self.updated_value[str].emit(self.val)
                self.updated_text_value.emit(self.val)
            else:
                self.updated_value[str].emit( self.fmt % self.val )
                self.updated_text_value.emit( self.fmt % self.val )
            self.updated_value[float].emit(self.val)
            self.updated_value[int].emit(self.val)
            self.updated_value[bool].emit(self.val)
            self.updated_value[()].emit()
            
            if self.choices is not None:
                choice_vals = [c[1] for c in self.choices]
                if self.val in choice_vals:
                    self.updated_choice_index_value.emit(choice_vals.index(self.val) )
            self.oldval = self.val
        else:
            #print "\t no updates sent", (self.oldval != self.val) , (force), self.oldval, self.val
            pass
            
            
    def update_choice_index_value(self, new_choice_index, **kwargs):
        self.update_value(self.choices[new_choice_index][1], **kwargs)
        
    def update_varied(self,val,wid,start,step,stop):
        
        self.is_varied = val
        
        if val:
           start.show() # was setVisible(True)
           step.show()
           stop.show()
           wid.setEnabled(False)
             
        else:
           self.start = None
           self.stop = None
           self.step = None
           start.setValue(0.0)
           step.setValue(0.0)
           stop.setValue(0.0)
           start.hide() # was setVisible(False)
           step.hide()
           stop.hide()
           wid.setEnabled(True)
            
         
    def update_start(self,val):
        
         self.start = self.dtype(val)
     
    def update_step(self,val):
    
         self.step = self.dtype(val)
     
    def update_stop(self,val):
    
         self.stop = self.dtype(val)
    
    def connect_bidir_to_widget(self, widget):
      
        if type(widget[0]) == QtGui.QCheckBox:
            
            self.updated_value[bool].connect(widget[0].setChecked)
            #original was uncommented
            widget[0].toggled[bool].connect(self.update_value)
            if self.ro:
                widget[0].setEnabled(False)
        elif type(widget[0]) == QtGui.QLineEdit:
            self.updated_text_value[str].connect(widget[0].setText)
            if self.ro:
                widget[0].setReadOnly(True)   
                #original was uncommented
            widget[0].textChanged[str].connect(self.update_value)
        elif type(widget[0]) == QtGui.QComboBox:
            # need to have a choice list to connect to a QComboBox
            assert self.choices is not None 
            widget[0].clear() # removes all old choices
            for choice_name, choice_value in self.choices:
                widget[0].addItem(choice_name, choice_value)
            self.updated_choice_index_value[int].connect(widget[0].setCurrentIndex)
            #original was uncommented
            widget[0].currentIndexChanged.connect(self.update_choice_index_value)
            
        elif isinstance(widget[0],QtGui.QDoubleSpinBox): #type(widget[0]) == QtGui.QDoubleSpinBox: #.ScientificDoubleSpinBox: #pyqtgraph.widgets.SpinBox.SpinBox: <-- original
            suffix = "" #self.unit # TAKING AWAY ALL UNITS
            if self.unit is None:
                suffix = ""
            if self.dtype == int:
                        integer = True
                        minStep=1
                        step=1
            else:
                integer = False
               
                       
            widget[0].setDecimals(self.no_decimals)  
            widget[0].setMinimum(self.vmin) 
            widget[0].setMaximum(self.vmax)  
            widget[0].setKeyboardTracking(False)
            
            widget[0].setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
            
            if self.dtype == int:
                    widget[0].setDecimals(0)
    
                  
            if self.ro:
                widget[0].setEnabled(False)
                widget[0].setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                widget[0].setReadOnly(True)
                
            #ORIGINAL
            self.updated_value[float].connect(widget[0].setValue)
           
            #original was uncommented
            widget[0].valueChanged.connect(self.update_value)                 
            self.send_display_updates(force=True)
            self.widget = widget[0]
            
            
            if not self.ro:
                is_varied = widget[1]
                start = widget[2]
                step = widget[3]
                stop = widget[4]
                
                #if widget is a QDoubleSpinBox, then definitely self.is_variable = True
                # Start, step stop QLineEdit
                start.setKeyboardTracking(False)
                step.setKeyboardTracking(False)   
                stop.setKeyboardTracking(False) 
                if self.vmin is not None:
                    start.setMinimum(self.vmin)
                    
                    stop.setMinimum(self.vmin)
                if self.vmax is not None:
                    start.setMaximum(self.vmax)
                    step.setMaximum(self.vmax)
                    step.setMinimum(-self.vmax) #enables scans going down in absolute value
                    stop.setMaximum(self.vmax)
                    
                # This works
                start.setDecimals(self.no_decimals)
                step.setDecimals(self.no_decimals)
                stop.setDecimals(self.no_decimals)
                
                start.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                step.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                stop.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
                
                start.setKeyboardTracking(False)
                step.setKeyboardTracking(False)
                stop.setKeyboardTracking(False)
                  
                if self.dtype == int:
                    start.setDecimals(0)
                    step.setDecimals(0)
                    stop.setDecimals(0)
                
                widget[1].stateChanged[int].connect(lambda: self.update_varied(widget[1].isChecked(),widget[0],widget[2],widget[3], widget[4]))           
                widget[2].valueChanged[float].connect(self.update_start)   
                widget[3].valueChanged[float].connect(self.update_step)
                widget[4].valueChanged[float].connect(self.update_stop)    
                start.setValue(0.0)
                step.setValue(0.0)
                stop.setValue(0.0)
                
        elif type(widget[0]) == QtGui.QLabel:
            self.updated_text_value.connect(widget[0].setText)
        else:
            raise ValueError("Unknown widget type")



def print_signals_and_slots(obj):
    for i in xrange(obj.metaObject().methodCount()):
        m = obj.metaObject().method(i)
        if m.methodType() == QtCore.QMetaMethod.MethodType.Signal:
            print "SIGNAL: sig=", m.signature(), "hooked to nslots=",obj.receivers(QtCore.SIGNAL(m.signature()))
        elif m.methodType() == QtCore.QMetaMethod.MethodType.Slot:
            print "SLOT: sig=", m.signature()