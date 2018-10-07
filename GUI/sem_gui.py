'''
SEMGUI widget to control Supra SEM @ Molecular Foundry
'''

import sys, os, importlib

# Append to Python path the parent directory, with all source files
sys.path.append(os.path.dirname(os.getcwd()))

from PySide.QtCore import * 
from PySide.QtGui import *

# Import main configuration file
from MasterConfigurations.main_config import MainConfig 

# Import helper functions
from HelperFunctions import *

# Import 4 widgets that constitute the main SEMGUI widget
from set_configuration import SetConfigurationWidget
from set_hardware import SetHardwareWidget
from set_results import SetResultsWidget
from set_scan import SetScanWidget

# For threading 
import threading
import time
import Tkinter


class SEMGUI(QWidget):

    def __init__(self, *args, **kwargs):
        super(SEMGUI, self).__init__() # super() lets you avoid referring to the base class explicitly
        
        # Choose user directory 
        self.MainConfig = MainConfig();
        dir_ops = directory_operations.DirectoryOperations();
        self.userdirectory_slash = dir_ops.select_directory_within_preferred_tree(self.MainConfig.preferred_tree,'Choose your user directory (where config file is)','Your user directory lives within the Users folder! ')
        if not self.userdirectory_slash: # If directory empty because user pressed cancel
            self.flag_to_close=True
            self.close()
            return
        else:
            self.flag_to_close=False
        
        # Give directory with . instead of / (Unix) or \ (Windoof): /Users/Clarice -> Users.Clarice
        helper_dir = os.path.split(os.path.split(self.userdirectory_slash.encode('ascii','ignore'))[0])[1] + '.' + os.path.split(self.userdirectory_slash.encode('ascii','ignore'))[1]
        # Deal below with some common path issues, namely spaces and () in directory name
        self.userdirectory_dot = helper_dir.replace(" ","\ ").replace("(","\(").replace(")","\)") + '.user_config'
        
        # Import userconfig file
        help = importlib.import_module(self.userdirectory_dot)
        self.UserConfig = help.UserConfig();
        
        print "FoundryScope starting up..."
        
        QMessageBox.information(self, 'Forget it not!','Turn on PMTs and Raith beam blanker...', QMessageBox.Ok, QMessageBox.Ok)

        # Establish GUI widget layout
        self.layout = QGridLayout(self)
        
        # Add widgets to GUI 
        no_columns = 1
        no_rows = 8
        # Configuration widget
        self.configuration_widget = SetConfigurationWidget(self)
        self.layout.addWidget(self.configuration_widget,0,0,1,no_columns)
        
        # Hardware widget
        self.hardware_widget = SetHardwareWidget(self)  
        self.hardware_widget.setFixedWidth(650)
        self.layout.addWidget(self.hardware_widget,0,1,no_rows,no_columns)
        
        # Results widget      
        self.results_widget = SetResultsWidget(self)
        self.layout.addWidget(self.results_widget,0,2,no_rows,no_columns) 
         
        # Sequence widget, which will control the other 3 widgets
        self.scan_widget = SetScanWidget(self)
        self.scan_widget.setFixedWidth(650)
        self.layout.addWidget(self.scan_widget,1,0,no_rows-1,no_columns) 
        
        # Do readings from microscope continuously
        #self.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.scan_widget.start_is_on)
        
        
        self.hardware_widget.button_readfromhardware.clicked.connect(lambda: self.hardware_widget.newfc()) 
        
        # Set GUI widget layout
        self.setLayout(self.layout)
        
        
        #self.do_thing()
        
        #QTimer.singleShot(5000, lambda: self.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.scan_widget.start_is_on))
        #QApplication.processEvents() 
        
        #timer = QTimer()
        # Connect it to f
        #timer.timeout.connect(self.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.scan_widget.start_is_on))
        # Call f() every 5 seconds
        #timer.start(5000)
        
         # Create new thread object.
        #d = DoSomething(self)
        #QObject.connect(d, SIGNAL('some_signal'))#, signalHandler, Qt.QueuedConnection)
        # Start new thread.
        #d.start()
         
        
        #self.mt = MyThread(self)
        #self.mt.start()
        #self.check_thread()

        #while mt.isAlive():
         #   self.update()

    def do_thing(self):
        
        QCoreApplication.processEvents() 
        
        try:
        # Do things
            self.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.scan_widget.start_is_on)
        finally:
            QTimer.singleShot(5000, self.do_thing())
    
    
        
#     def check_thread(self):
#     # Still alive? Check again in half a second
#         if self.mt.isAlive():
#             QTimer.singleShot(5000,self.check_thread())
#             QApplication.processEvents() 
#             
#             #self.after(500, self.check_thread)
#         else:
#             print "mt crashed somehow"    
        
    def closeEvent(self,event):
        
        if self.flag_to_close == False:
            reply = QMessageBox.question(self, 'Goodbye?',"Are you sure you want to exit FoundryScope?\n If yes, don't forget to turn off the PMTs \n and the Raith beam blanker!", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:  
                event.accept()
            else:
                event.ignore()  
        else:
            self.setAttribute(Qt.WA_DeleteOnClose)
            event.accept()     
            
class DoSomething(QThread):
    def __init__(self,main_gui):
        QThread.__init__(self)
        
        self.main_gui = main_gui

    def run(self):
        time.sleep(3)
        QApplication.processEvents() 
        self.main_gui.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.main_gui.scan_widget.start_is_on)
        QApplication.processEvents() 
        self.emit(SIGNAL('some_signal'))
        
def signalHandler():
    # We got signal!
    print 'Got signal!'
    sys.exit(0)
        
# class MyThread(threading.Thread):
# 
#     def __init__(self, main_gui):
#         threading.Thread.__init__(self)
#         
#         self.main_gui = main_gui
# 
#     def run(self):
#         print "Step Two"
#         self.main_gui.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(self.main_gui.scan_widget.start_is_on)
#         time.sleep(2) 

def do_thing(main_gui):
        
        QApplication.processEvents() 
        
        try:
        # Do things
            main_gui.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(main_gui.scan_widget.start_is_on)
        finally:
            QTimer.singleShot(5000, do_thing(main_gui))

#########################################################################################################################
#########################################################################################################################              
            
if __name__ == '__main__': 
    app = QApplication(sys.argv)
    main_window = SEMGUI()
    main_window.setWindowTitle('FoundryScope Supra SEM @ Molecular Foundry')
    main_window.show()
    #do_thing(main_window)
    #t = threading.Thread(target=main_window.hardware_widget.hardware['Microscope'].continuously_read_from_hardware(main_window.scan_widget.start_is_on))
    #t.start()
    sys.exit(app.exec_())
    
