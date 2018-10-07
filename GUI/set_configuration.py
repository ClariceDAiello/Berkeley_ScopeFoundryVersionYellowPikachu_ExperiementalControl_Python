'''
Configuration widget inside SEMGUI
'''

import os

from PySide.QtCore import *
from PySide.QtGui  import *

from datetime import datetime

# Import helper functions
from HelperFunctions import *

class SetConfigurationWidget(QWidget):
    
    def __init__(self,main_gui):
        super(SetConfigurationWidget, self).__init__() # super() lets you avoid referring to the base class explicitly
        
        self.main_gui = main_gui
        self.foldername = ''
        self.filenumber = 1 # set to 1 this index, which that tracks the number of different experiments inside the same folder
        
        # Establish configuration widget layout
        self.layout = QGridLayout(self)

        # Add contents to widget
        self.label_config = QLabel('Config of data saving', self)
        font = QFont("Sans Serif", 12, QFont.Bold)
        self.label_config.setFont(font)
        
        self.button_updatedir = QPushButton('Update dir', self)
        self.button_updatedir.clicked.connect(lambda: self.update_foldername_label())

        self.button_changedir = QPushButton('Rename dir', self)
        self.button_changedir.clicked.connect(lambda: self.rename_current_folder())
        
        self.label_folder = QLabel('Folder:', self)
        self.label_foldername = QLabel('', self)
        self.update_foldername_label()

        self.label_filesrootname = QLabel('Files root name:', self)
        self.lineedit_filesrootname = QLineEdit('', self)
        self.filesrootname = self.lineedit_filesrootname.text()

        self.layout.addWidget(self.label_config,0,0,1,2)
        self.layout.addWidget(self.button_updatedir,0,2,1,1)
        self.layout.addWidget(self.button_changedir,0,3,1,1)
        self.layout.addWidget(self.label_folder,1,0,1,1)
        self.layout.addWidget(self.label_foldername,1,1,1,3)
        self.layout.addWidget(self.label_filesrootname,2,0,1,1)
        self.layout.addWidget(self.lineedit_filesrootname,2,1,1,3)

        self.setLayout(self.layout)
        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))
        
    def update_foldername_label(self):
       
        dir_ops = directory_operations.DirectoryOperations();
        preferred_folder = dir_ops.update_directory(self.main_gui.userdirectory_slash + os.sep + 'Data' + os.sep)
        if self.foldername is preferred_folder: # ie updated dir is the same because user clicked too fast
            pass
        else:
            self.foldername = preferred_folder
            self.label_foldername.setText(os.path.split(self.foldername)[1])
            self.filenumber = 1
       
    def rename_current_folder(self):
       
       dir_ops = directory_operations.DirectoryOperations();
       new_path = dir_ops.rename_directory(os.path.split(self.foldername)[0],os.path.split(self.foldername)[1],'Rename your current folder (still lives inside your Data folder!)')
       self.foldername = new_path
       self.label_foldername.setText(os.path.split(self.foldername)[1])