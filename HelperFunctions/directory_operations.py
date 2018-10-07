import os, importlib

from datetime import datetime

from PySide.QtCore import * 
from PySide.QtGui import *

class DirectoryOperations(QWidget):
     
     def __init__(self):
         super(DirectoryOperations, self).__init__()
    
     def select_directory_within_preferred_tree(self,preferred_tree,text_of_prompt, warning = None): 
        
        dialog = QFileDialog()
        userdirectory =  dialog.getExistingDirectory(self,text_of_prompt, preferred_tree)
        dialog.close()
        
        if userdirectory: # Only goes here if cancel has not been pressed; if cancel has been pressed, userdirectory is empty and thus false
            while not os.path.abspath(os.path.split(userdirectory.encode('ascii','ignore'))[0]) == os.path.abspath(preferred_tree): # If you are not within the input preferred_tree
                dialog = QFileDialog()
                userdirectory =  dialog.getExistingDirectory(self, warning + text_of_prompt, preferred_tree)
                dialog.close()
                if not userdirectory: # User can press cancel 
                    return userdirectory
        
        return userdirectory
    
     def select_file_within_preferred_tree(self,preferred_tree,text_of_prompt, type, warning = None): 
        
        if type is 'xml':
           open_type = "XML Files (*.xml), *.xml"
        else:
           msgBox = QMessageBox()
           msgBox.setText('Error: type of file not yet implemented in DirectoryOperations.select_file_within_preferred_tree')
           msgBox.exec_(); 
        
        dialog = QFileDialog()
        userfile =  dialog.getOpenFileName(self,text_of_prompt, preferred_tree,open_type)
        dialog.close()
        
        if userfile[0]:
            while not os.path.abspath(os.path.split(userfile[0].encode('ascii','ignore'))[0]) == os.path.abspath(preferred_tree): # if cancel has been pressed, ie, if userfile is an empty string OR if you are not within the input preferred_tree
                dialog = QFileDialog()
                userfile =  dialog.getOpenFileName(self, warning + text_of_prompt, preferred_tree,open_type)
                dialog.close()
                if not userfile[0]:
                   return userfile[0]
        
        return userfile[0]
    
     def update_directory(self,preferred_tree): # Creates directory stamped with current time

        i = datetime.now()
        preferred_folder =  preferred_tree + i.strftime('%Y-%m-%d-%H%M')
        if not os.path.exists(preferred_folder):
           os.mkdir(preferred_folder)
        return preferred_folder
    
     def rename_directory(self,preferred_tree,current_name, text_of_prompt):
        
        new_name, ok = QInputDialog.getText(self, '', text_of_prompt, QLineEdit.Normal, current_name)
        if ok and not os.path.exists(preferred_tree + os.sep + new_name):
           os.rename(preferred_tree + os.sep + current_name, preferred_tree + os.sep + new_name)
           return preferred_tree + os.sep + new_name
        else:
           if ok: #ie naming was wrong
                msgBox = QMessageBox()
                msgBox.setText('Directory already existed! Renaming aborted.')
                msgBox.exec_(); 
           return preferred_tree + os.sep + current_name
           