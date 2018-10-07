import numpy as np

class PyDAQmx_simu():
 
 	def __init__(self):
 		
	 	self.DAQmx_Val_Task_Unreserve = 0
	
	 	self.DAQmx_Val_Task_Commit = 0
	
	 	self.DAQmx_Val_Cfg_Default = 0
	 
	 	self.DAQmx_Val_RSE = 0

	 	self.DAQmx_Val_NRSE = 0
    
	 	self.DAQmx_Val_Diff = 0
    
	 	self.DAQmx_Val_PseudoDiff = 0
	
		self.DAQmx_Val_Rising = 0
	
		self.DAQmx_Val_GroupByScanNumber = 0
	
		self.DAQmx_Val_Volts = 0
	
		self.DAQmx_Val_FiniteSamps = 0
	
		self.DAQmx_Val_ContSamps = 0
	
		self.DAQmx_Val_CountUp = 0
		
		self.Task = 0
		
		self.DAQmx_Val_Acquired_Into_Buffer = 0
		

	def DAQmxCreateTask(self, name, var):
		return 0

	def DAQError(self):
		return 0
	
	def byref(self,status):
		return status
	
	def create_string_buffer(self,buffSize):
	    return np.zeros(buffSize)
	   
	def DAQmxGetSysDevNames(self,buff,buffSize):
		return 0
	
	def bool32(self,input):
		return np.bool_(input)
	
	def uInt32(self,input):
		return np.uint32(input)

	def float64(self,input):
		return np.float64(input)
	
	def int32(self,input):
		return np.int32(input)

	def uInt64(self,input):
		return np.uint64(input)
	
	def TaskHandle(self,input=0):
		return np.uInt32(input)
	
 	#def Task(self):
	#	pass
	
# class Task(PyDAQmx_simu):
# 	
# 	def __init__(self):
# 		
# 		self.AutoRegisterDoneEvent = 0
# 	
# 	def ClearTask(self):
# 		pass
