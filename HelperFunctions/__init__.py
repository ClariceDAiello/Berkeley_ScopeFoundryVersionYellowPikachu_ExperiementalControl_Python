import sys, os, glob
sys.dont_write_bytecode = True # If this is true, Python won't try to write .pyc or .pyo files on the import of source modules
 
# Import all .py modules from the current folder
modules = glob.glob(os.path.dirname(__file__)+"/*.py")
__all__ = [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f)]


