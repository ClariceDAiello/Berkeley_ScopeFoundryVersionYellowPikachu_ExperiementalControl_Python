'''
Results widget inside SEMGUI
'''

from PySide.QtCore import * 
from PySide.QtGui import *

import sys
import numpy as np
import pyqtgraph as pg
import functools

class SetResultsWidget(QWidget):
    
    setroi_sig = Signal(float, float)
    
    def __init__(self,main_gui):
        super(SetResultsWidget, self).__init__() # super() lets you avoid referring to the base class explicitly
                        
        self.main_gui = main_gui                        
                
        # Establish results widget layout
        self.layout = QGridLayout()
        
        self.label_results = QLabel('Results', self)
        font = QFont("Sans Serif", 12, QFont.Bold)
        self.label_results.setFont(font)
        
        self.roi_button = QPushButton("Set ROI") # Set ROI in any one of the pictures, and resize all channels of same class. For example, Analog and Counter channels are of class Counts. Spectrometer channel'd be of type Wavelength or so
        self.reset_roi_button = QPushButton("Reset ROI (to last full scale picture)")
        
        self.button_count = QPushButton("Count")
        self.button_count.clicked.connect(lambda: self.count_clicked())
        
        self.label_update_after = QLabel("Update after ")
        self.lineedit_number = QLineEdit("100")
        self.lineedit_number.setFixedSize(60, 25) 
        self.lineedit_number.returnPressed.connect(lambda: self.update_no_samples())
        self.label_samples = QLabel("samples")
        self.label_update_after.setEnabled(False)
        self.lineedit_number.setEnabled(False)
        self.label_samples.setEnabled(False)
        
        # By default, acquire 4 channels (should be plenty!), which can currently be of type 'Counter' or 'Analog'
        # If the need arises for channel of other types (ex: Andor camera), create one more type (ex: 'Camera') 
        # Below, instantiate the widgets for the channels, according to channel types and names chosen in userconfig.py
        # Each channel widget has a main plotting area (of class pyqtgraph.ImageView()), and some buttons
        self.fig_ch = []
        for k in range(len(self.main_gui.UserConfig.names_counter_channels)):
            self.fig_ch.append(ResultWidget(self,self.main_gui.UserConfig.names_counter_channels[k],'Counter',self.main_gui.hardware_widget))
        
        namesinit =  ['SE2','InLens'] ######REDO THIS
        self.no_ai_channels = 2
        ### CHANGE DISPALYED NAMES AS SOON AS CHANGES THE CHANNEL
        for k in range(self.no_ai_channels):
            self.fig_ch.append(ResultWidget(self,namesinit[k],'Analog',None))

        # Add the result widgets to the layout
        self.layout.addWidget(self.label_results,0,0,1,1)
        self.layout.addWidget(self.roi_button,0,1,1,2)
        self.layout.addWidget(self.reset_roi_button,0,3,1,2)
        self.layout.addWidget(self.button_count, 0,5,1,2)
        
        self.layout.addWidget(self.label_update_after , 0,7) #,1,2)
        self.layout.addWidget(self.lineedit_number, 0,8)#,1,2)
        self.layout.addWidget(self.label_samples , 0,9)#,1,2)
        
        size_widget = 6
        size_skip = [7,7,13,13] # This value is not helping to place label_results at same height than other title labels #13 = 6+7
        size_helper = [0,size_widget,0,size_widget]
        for k in range(len(self.fig_ch)):
            self.fig_ch[k].setFixedWidth(600)
            self.layout.addWidget(self.fig_ch[k], size_skip[k], size_helper[k], size_widget, size_widget)
            
        self.label_dets = QLabel("Choose SEM detectors")
        self.button_AI = dict()
        self.button_AI['SE2'] = QCheckBox()
        self.button_AI['SE2'].setText('SE2')
        self.button_AI['SE2'].setChecked(True)
        
        self.button_AI['InLens'] = QCheckBox()
        self.button_AI['InLens'].setText('InLens')
        self.button_AI['InLens'].setChecked(True)
        
        self.button_AI['VPSE'] = QCheckBox()
        self.button_AI['VPSE'].setText('VPSE')
        self.button_AI['VPSE'].setChecked(False)
        
        self.layout.addWidget(self.label_dets,0,12) #9)
        self.layout.addWidget(self.button_AI['SE2'],0,14) #was 13
        self.layout.addWidget(self.button_AI['InLens'],0,16) #15    
        self.layout.addWidget(self.button_AI['VPSE'],0,18)#17
        
        self.check_AI_channels()
        
        self.button_AI['SE2'].clicked.connect(lambda: self.check_AI_channels())     
        self.button_AI['InLens'].clicked.connect(lambda: self.check_AI_channels())   
        self.button_AI['VPSE'].clicked.connect(lambda: self.check_AI_channels())   

        # Set results widget layout
        self.setLayout(self.layout)
        
        # Change all ROIs together
        self.fig_ch[0].roi.sigRegionChangeFinished.connect(lambda: self.on_roi_signal_emitted(0,1,2,3))
        self.fig_ch[1].roi.sigRegionChangeFinished.connect(lambda: self.on_roi_signal_emitted(1,0,2,3))
        self.fig_ch[2].roi.sigRegionChangeFinished.connect(lambda: self.on_roi_signal_emitted(2,1,0,3))
        self.fig_ch[3].roi.sigRegionChangeFinished.connect(lambda: self.on_roi_signal_emitted(3,1,2,0))
        
        # Change all Sliders together
        #works with patched class
        self.fig_ch[0].viewer.sigTimeChanged.connect(lambda: self.on_slider_signal_emitted(0,1,2,3))
        self.fig_ch[1].viewer.sigTimeChanged.connect(lambda: self.on_slider_signal_emitted(1,0,2,3))
        self.fig_ch[2].viewer.sigTimeChanged.connect(lambda: self.on_slider_signal_emitted(2,1,0,3))
        self.fig_ch[3].viewer.sigTimeChanged.connect(lambda: self.on_slider_signal_emitted(3,1,2,0))
        
        
        self.roi_button.clicked.connect(self.set_roi)
        self.reset_roi_button.clicked.connect(self.reset_roi)
        
    def check_AI_channels(self):
        # This is the only place in the code where the 'Experiment_clock_rate' is changed
        # The number of AI channels determines the max (and current!) 'Experiment_clock_rate'
        
        # 7 CASES: no channel, 1 or 2 enabled
        if not self.button_AI['SE2'].isChecked() and not self.button_AI['InLens'].isChecked() and not self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value('')
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 2.0e6 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(True)
            self.no_ai_channels = 0
            self.newname2 = ''
            self.newname3 = ''
            
        if self.button_AI['SE2'].isChecked() and not self.button_AI['InLens'].isChecked() and not self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['SE2'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 2.0e6 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(True)
            self.no_ai_channels = 1
            self.newname2 = 'SE2'
            self.newname3 = ''
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON3 \r')
            
        if not self.button_AI['SE2'].isChecked() and self.button_AI['InLens'].isChecked() and not self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['InLens'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 2.0e6 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(True)
            self.no_ai_channels = 1
            self.newname2 = 'InLens'
            self.newname3 = ''
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON4 \r')
            
        if not self.button_AI['SE2'].isChecked() and not self.button_AI['InLens'].isChecked() and self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['VPSE'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 2.0e6 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(True)
            self.no_ai_channels = 1
            self.newname2 = 'VPSE'
            self.newname3 = ''
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON5 \r')
            
        if self.button_AI['SE2'].isChecked() and self.button_AI['InLens'].isChecked() and not self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['SE2'] + ',' + self.main_gui.hardware_widget.hardware['DAC'].AIdict['InLens'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 5.0e5 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(False)
            self.no_ai_channels = 2
            self.newname2 = 'SE2'
            self.newname3 = 'InLens'
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON6 \r')
             
        if self.button_AI['SE2'].isChecked() and not self.button_AI['InLens'].isChecked() and self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['SE2'] + ',' + self.main_gui.hardware_widget.hardware['DAC'].AIdict['VPSE'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 5.0e5 # In Hz
            self.button_AI['SE2'].setEnabled(True)
            self.button_AI['InLens'].setEnabled(False)
            self.button_AI['VPSE'].setEnabled(True) 
            self.no_ai_channels = 2
            self.newname2 = 'SE2'
            self.newname3 = 'VPSE'
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON7 \r')
               
        if not self.button_AI['SE2'].isChecked() and self.button_AI['InLens'].isChecked() and self.button_AI['VPSE'].isChecked():
            self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['AI_channels_machine_names'].update_value(self.main_gui.hardware_widget.hardware['DAC'].AIdict['InLens'] + ',' + self.main_gui.hardware_widget.hardware['DAC'].AIdict['VPSE'])
            self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock = 5.0e5 # In Hz
            self.button_AI['SE2'].setEnabled(False)
            self.button_AI['InLens'].setEnabled(True)
            self.button_AI['VPSE'].setEnabled(True) 
            self.no_ai_channels = 2 
            self.newname2 = 'InLens'
            self.newname3 = 'VPSE'
            # Send macro to REMCON
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON1 \r')
            self.main_gui.hardware_widget.hardware['Microscope'].send_cmd('MAC REMCON8 \r')
            
        # Set new max and current value for 'Experiment_clock_rate' based on how many AI channels
        self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].vmax = self.main_gui.hardware_widget.hardware['DAC'].max_exp_clock
        self.main_gui.hardware_widget.hardware['DAC'].control_widgets['Experiment_clock_rate'][0].setMaximum(self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].vmax)
        self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].update_value(self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].vmax)
        # Set new min and current value for 'Counter_clock_rate' based on updated value of 'Experiment_clock_rate'
        self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Counter_clock_rate'].vmin = self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].read_from_hardware()
        self.main_gui.hardware_widget.hardware['DAC'].control_widgets['Counter_clock_rate'][0].setMinimum(self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Counter_clock_rate'].vmin)
        self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Counter_clock_rate'].update_value(self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Counter_clock_rate'].vmin)
        # Set min for 'Beam_lag_time_at_pixel' based on updated value of 'Experiment_clock_rate'
        self.main_gui.hardware_widget.hardware['DAC'].control_widgets['Experiment_clock_rate'][0].valueChanged.connect(lambda: self.exp_clock_changed())
    
    def exp_clock_changed(self):
        
        self.main_gui.scan_widget.measurement.logged_quantities['Beam_lag_time_at_pixel'].vmin = 1/self.main_gui.hardware_widget.hardware['DAC'].logged_quantities['Experiment_clock_rate'].read_from_hardware()
        self.main_gui.scan_widget.measurement.control_widgets['Beam_lag_time_at_pixel'][0].setMinimum(self.main_gui.scan_widget.measurement.logged_quantities['Beam_lag_time_at_pixel'].vmin)
        
    def reset_roi(self):
        
        self.fig_ch[0].roi.setVisible(True)
        self.fig_ch[1].roi.setVisible(True)
        self.fig_ch[2].roi.setVisible(True)
        self.fig_ch[3].roi.setVisible(True)
        
        # resetting scale to 100% 
        xscale = 100.0
        yscale = 100.0
        
        self.main_gui.scan_widget.measurement.logged_quantities['Scale_x'].update_value(xscale * 100.0)
        self.main_gui.scan_widget.measurement.logged_quantities['Scale_y'].update_value(yscale * 100.0)
        
        # resetting offset to 0% 
        xoffset = 0
        yoffset = 0
        
        self.main_gui.scan_widget.measurement.logged_quantities['Offset_x'].update_value(xoffset)
        self.main_gui.scan_widget.measurement.logged_quantities['Offset_y'].update_value(yoffset)
        
        # load original full scale image                        
        for k in range(4):
            
            original_image = self.fig_ch[k].original_image_data
            original_scale = self.fig_ch[k].original_scale_size
            original_scale_length = self.fig_ch[k].original_scale_length
            original_suffix = self.fig_ch[k].original_scale_suffix
                        
            self.fig_ch[k].load(data=original_image,
                                scale_size=original_scale,
                                scale_length=original_scale_length,
                                scale_suffix=original_suffix,
                                is_original=False, # so that the original is not overwritten with the original again
                                xvalues = self.fig_ch[k].xvalues)
            
        
        self.roi_button.setEnabled(True)
        
        self.main_gui.scan_widget.measurement.control_widgets['Scale_x'][0].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Scale_y'][0].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Offset_x'][0].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Offset_y'][0].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Scale_x'][1].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Scale_y'][1].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Offset_x'][1].setEnabled(True)
        self.main_gui.scan_widget.measurement.control_widgets['Offset_y'][1].setEnabled(True)
    
    def set_roi(self):
        
        my_roi = self.fig_ch[0].roi
        my_img = self.fig_ch[0].viewer.image
        
        #now image has Z!!! (== no frames)
        #I'm surprised that it works by dividing both by shape[1], regardless if there are more pixels in x or y
        ########## NEEDS TO CORRECT FOR HIGHER DIMENSIONAL IMAGES
        # now dividing by shape[-2] to correct for higher dimensional images
        xscale = my_roi.size()[0]/my_img.shape[-2] * 100.0
        yscale = my_roi.size()[1]/my_img.shape[-2] * 100.0
        
         # NOW IMAGE HAS Z 
        xoffset = ((my_roi.pos()[0] + my_roi.size()[0]/2.0)/my_img.shape[-2] - 1.0/2.0) *100.0 
        yoffset =  ((my_roi.pos()[1] + my_roi.size()[1]/2.0)/my_img.shape[-2] - 1.0/2.0) *100.0
        
        # Apparently, ROI is a rectangle whose left corner is the origin
        # every pic has a size in pixels corresponding to the largest of the grid dimensions
        # Check if this offset is correct for the case when fixed ratio (square) pictures are displayed!!!!!!!
        
        self.main_gui.scan_widget.measurement.logged_quantities['Scale_x'].update_value(xscale)
        self.main_gui.scan_widget.measurement.logged_quantities['Scale_y'].update_value(yscale)
        
        self.main_gui.scan_widget.measurement.logged_quantities['Offset_x'].update_value(xoffset)
        self.main_gui.scan_widget.measurement.logged_quantities['Offset_y'].update_value(yoffset)
        
        self.roi_button.setEnabled(False)
        
        #tried before with setMovable, didn't work
        self.fig_ch[0].roi.setVisible(False)
        self.fig_ch[1].roi.setVisible(False)
        self.fig_ch[2].roi.setVisible(False)
        self.fig_ch[3].roi.setVisible(False)
        
        self.roiused_sig.emit()
    
    def on_roi_signal_emitted(self, k, a, b, c):
                
        pos = self.fig_ch[k].roi.pos()
        self.fig_ch[a].roi.setPos(pos, update=True, finish=False)
        self.fig_ch[b].roi.setPos(pos, update=True, finish=False)
        self.fig_ch[c].roi.setPos(pos, update=True, finish=False)
        
        size = self.fig_ch[k].roi.size()
        self.fig_ch[a].roi.setSize(size, update=True, finish=False)
        self.fig_ch[b].roi.setSize(size, update=True, finish=False)
        self.fig_ch[c].roi.setSize(size, update=True, finish=False)
        
        ####### modified autohist to True below!
        if not self.fig_ch[k].viewer.image is None:
            self.fig_ch[k].viewerzoom.setImage(self.fig_ch[k].roi.getArrayRegion(self.fig_ch[k].viewer.image,self.fig_ch[k].viewer.imageItem),autoHistogramRange=True)
            
        if not self.fig_ch[a].viewer.image is None:
            self.fig_ch[a].viewerzoom.setImage(self.fig_ch[a].roi.getArrayRegion(self.fig_ch[a].viewer.image,self.fig_ch[a].viewer.imageItem),autoHistogramRange=True)
            
        if not self.fig_ch[b].viewer.image is None:
            self.fig_ch[b].viewerzoom.setImage(self.fig_ch[b].roi.getArrayRegion(self.fig_ch[b].viewer.image,self.fig_ch[b].viewer.imageItem),autoHistogramRange=True)
            
        if not self.fig_ch[c].viewer.image is None:
            self.fig_ch[c].viewerzoom.setImage(self.fig_ch[c].roi.getArrayRegion(self.fig_ch[c].viewer.image,self.fig_ch[c].viewer.imageItem),autoHistogramRange=True)
        
        
        
    def on_slider_signal_emitted(self, k, a, b, c):
        ##### CHANGE ROI AS WELL
        #### cHANGE COUNTS DISPLAYED TOO
        #### does not work too well - why?
        #print "onepass"        
                
        (ind, time) = self.fig_ch[k].viewer.timeIndex(self.fig_ch[k].viewer.timeLine)
        #print "ind=" + str(ind)
        #print "time=" + str(time)
        
        self.fig_ch[a].viewer.currentIndex = ind
        self.fig_ch[b].viewer.currentIndex = ind
        self.fig_ch[c].viewer.currentIndex = ind
        
        self.fig_ch[a].viewer.timeLine.setPos(time)
        self.fig_ch[b].viewer.timeLine.setPos(time)
        self.fig_ch[c].viewer.timeLine.setPos(time)
        
        self.fig_ch[a].viewer.updateImage()
        self.fig_ch[b].viewer.updateImage()
        self.fig_ch[c].viewer.updateImage()
        
        QCoreApplication.processEvents()
        
    def count_clicked(self):
        
        if str(self.button_count.text()) == 'Count':
            self.label_update_after.setEnabled(True)
            self.lineedit_number.setEnabled(True)
            self.label_samples.setEnabled(True)
            self.main_gui.scan_widget.button_start.setDisabled(True)
            QCoreApplication.processEvents()
            self.button_count.setText('Stop count')
            self.main_gui.hardware_widget.hardware['DAC'].count_continuously() 
            
           
            #print  'start is ' + str(self.main_gui.scan_widget.button_start.isEnabled())
            
        elif str(self.button_count.text()) == 'Stop count':
            self.label_update_after.setEnabled(False)
            self.lineedit_number.setEnabled(False)
            self.label_samples.setEnabled(False)
            self.main_gui.scan_widget.button_start.setEnabled(True)
            QCoreApplication.processEvents()
            self.button_count.setText('Count')
            self.main_gui.hardware_widget.hardware['DAC'].stop_count_continuously() 
            #print  'start is ' + str(self.main_gui.scan_widget.button_start.isEnabled())
            
    def update_no_samples(self):
        
        self.main_gui.hardware_widget.hardware['DAC'].update_after = int(round(float(self.lineedit_number.text())))
        self.lineedit_number.setText(str(int(round(float(self.lineedit_number.text())))))
        
class ResultWidget(QWidget):
    
    roisignal = Signal() #not doing anything, right?

    def __init__(self, parent,name,typechannel,hardware_widget=None):    
        self.parent = parent    
        super(ResultWidget, self).__init__(self.parent)
        
        # temporary original image to put back on the screen when the roi is reset
        self.original_image_data = None
        
        
        self.name = name
        self.typechannel = typechannel
        
        self.layout = QGridLayout()

        self.label_type = QLabel(self.typechannel, self)
        self.lineedit_name = QLineEdit(self.name, self) 
        self.popout_button = QPushButton("Pop out")
        self.popout_button.setVisible(False)
        
         
        self.img_display = QWidget() 
        self.img_display.setLayout(QGridLayout())
        
        size_widget = 11
        self.layout.addWidget(self.img_display, 0, 0,size_widget, size_widget)
        self.layout.addWidget(self.label_type,size_widget ,0 , 1,1)
        self.layout.addWidget(self.lineedit_name, size_widget, 1,1,1)
        self.layout.addWidget(self.popout_button, size_widget, 2,1,1)
        if self.typechannel is 'Counter':
            self.label_min = QLabel('Min', self)
            self.label_mean = QLabel('Mean', self)
            self.label_max = QLabel('Max', self)
            self.label_cps = QLabel('(kcps)', self)
            self.layout.addWidget(self.label_min, size_widget, 3,1,1)
            self.layout.addWidget(self.label_mean, size_widget, 4,1,1)
            self.layout.addWidget(self.label_max, size_widget, 5,1,1)
            self.layout.addWidget(self.label_cps, size_widget, 6,1,1)
        
        self.setLayout(self.layout)
        
        pg.setConfigOptions(useWeave=False) # Weave will significantly increase the loading time
        
        
#        # ORIGINAL
#         #self.viewer = pg.ImageView()
        self.viewer = PatchedImageView()                  #pg.ImageView() # Instantiate class ImageView for displaying
        self.img_display.layout().addWidget(self.viewer,0,0,4,4)
        
        
        
        ######### TEST - FUTURE
#         self.viewer = pg.ImageView()
#         self.slider = QSlider(Qt.Horizontal)
#         self.slider.setMinimum(0)
#         self.slider.setMaximum(5)
#         self.slider.setSingleStep(1)
#         self.slider.setPageStep(1)
#         self.slider.setTickPosition(QSlider.TicksBothSides)
#         self.slider.valueChanged.connect(self.callback_slider)
#         self.img_display.layout().addWidget(self.viewer,0,0,4,4)
#         self.img_display.layout().addWidget(self.slider,1,0,1,4)
        
        
       
        self.viewerzoom = pg.ImageView() # Instantiate class ImageView for displaying
        self.img_display.layout().addWidget(self.viewerzoom,0,5,1,1)
       
        # HIDE ALL THE CRAP
        self.viewer.ui.roiBtn.hide()
        self.viewer.ui.menuBtn.hide()
        self.viewer.view.setMouseEnabled(x = False,y = False)
        self.viewer.ui.histogram.axis.mouseDragEvent=None
        
        # want to disable the slider to be changed with the mouse
        #self.viewer.ui.timeSlider.setMouseEnabled(False)
       
       # original did use these 3 lines
        #self.viewer.ui.histogram.plot.hide()
        #self.viewer.ui.histogram.region.hide()
        #self.viewer.ui.histogram.item.layout.removeItem(self.viewer.ui.histogram.vb)
   
        # ORIGINAL
        self.viewerzoom.ui.histogram.setVisible(False)
        self.viewerzoom.ui.roiBtn.setVisible(False)
        self.viewerzoom.ui.menuBtn.setVisible(False)
        
        self.roi=pg.ROI([0,0])
        self.viewer.view.addItem(self.roi)
      
        self.scale=hao_scale(size=10,suffix='m')
        self.scale.setParentItem(self.viewer.view)
        self.scale.anchor((1,1),(1,1),offset=(-40,-20))
        
        # FUTURE: get rid of histogram and keep contrast bar
     
        ########## TEST
       
#     def callback_slider(self):
#  
#         val = self.slider.sliderPosition()
#         print int(val)
#         
#          
#         data_to_plot = self.data[int(round(val)), :, :]
#  
#         self.viewer.setImage(data_to_plot, autoRange=False, scale = [1,float(self.data.shape[0])/float(self.data.shape[1])], autoHistogramRange=False)
#  
#         self.viewer.ui.histogram.setHistogramRange(np.min(self.data),np.max(self.data))    
        
    def load(self, data, scale_size, scale_length, scale_suffix, is_original,xvalues=None):
        
        if is_original:
            self.original_image_data = data
            self.original_scale_size = scale_size
            self.original_scale_length = scale_length
            self.original_scale_suffix = scale_suffix
            
        
        self.roi.setPos([0,0])
        self.roi.setSize([10*0.5,10*0.5])
        
        self.roi.addScaleHandle([1, 1], [0, 0])
    
        if xvalues is not None: 
            if len(xvalues) == 1:
                self.viewer.setImage(data[0,:,:], autoRange=True, scale = [1,float(data.shape[1])/float(data.shape[2])], autoHistogramRange=True)
                self.xvalues = xvalues
            else:
                self.viewer.setImage(data, autoRange=True, scale = [1,float(data.shape[1])/float(data.shape[2])], autoHistogramRange=True,xvals = xvalues)
                self.xvalues = xvalues
                print "self.xv given"
        else: #display while scanning
            self.viewer.setImage(data, autoRange=True, scale = [1,float(data.shape[0])/float(data.shape[1])], autoHistogramRange=True)
            self.xvalues = None
            #print "self.xv deleted"
        self.scale.size=scale_size
        self.scale.length=scale_length
        self.scale.suffix=scale_suffix
        self.scale.text.setText(pg.functions.siFormat(scale_length, suffix=scale_suffix))
        self.scale.updateBar()
        self.histogram=self.viewer.ui.histogram
        
        # Get rid of z slides
        #self.viewer.timeLine.hide()
        
        
        
        pg.QtGui.QApplication.processEvents()
        
        # maxx = maxy bc the ROI looks at the picture size, not at no pixels, and the aspect ratio for display is always 1
        #max = np.max(data.shape)
        
        if xvalues is not None:
           self.roi.maxBounds = QRectF(0.0,0.0,data.shape[1]*1,data.shape[2]*float(data.shape[1])/float(data.shape[2]))
        else:
           self.roi.maxBounds = QRectF(0.0,0.0,data.shape[0]*1,data.shape[1]*float(data.shape[0])/float(data.shape[1])) 
        
        self.viewerzoom.setImage(self.roi.getArrayRegion(self.viewer.image,self.viewer.imageItem))
        
    ###### Maybe need for correct scaling of histogram?
    #self.hist = pg.HistogramLUTItem()
    #self.hist.vb.setLimits(yMin=0, yMax=16000)
         
class hao_scale(pg.ScaleBar):
    parent2=None
    def __init__(self, *args, **kwargs):
        super(hao_scale, self).__init__(*args, **kwargs)
 
 
    def setParentItem(self, parent):
        self.parent2=parent
        self.pcene=parent.scene()
        self.pcene.addItem(self)
  
    def parentItem(self):
        return self.parent2
  
    def remove(self):
        self.pcene.removeItem(self)
        
# from http://stackoverflow.com/questions/32586149/pyqtgraphs-imageview-does-not-emit-time-changed-signal
class PatchedImageView(pg.ImageView):
    def timeLineChanged(self):
        (ind, time) = self.timeIndex(self.timeLine)
        self.sigTimeChanged.emit(ind, time)
        if self.ignoreTimeLine:
            return
        self.play(0)
        if ind != self.currentIndex:
            self.currentIndex = ind
            self.updateImage()