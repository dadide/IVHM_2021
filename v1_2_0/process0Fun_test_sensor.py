import cantools
#import processmainFun # comment out for testing 
import time
import platform
import numpy as np
from ctypes import *


#-------------------------------------Load dynamic lib-----------------------------------------

Can_SO = cdll.LoadLibrary('./Ccode/Can/libusbcan.so') #  can lib
#CanFD_SO = cdll.LoadLibrary('./Ccode/can/libusbcanfd.so') #  canFD lib


#Integrated_Sensor_SO = cdll.LoadLibrary('./Ccode/can/libusbcan.so')  # integrated vehicle lib 
Model_Sensor_can1_SO = cdll.LoadLibrary('./Ccode/Model_Sensor/Model_Sensor_can1.so') #  lib of sensors for estimating data  


# ------------------------------------sensor data ----------------------------------------
can1_dim=9
can1_num_ID=3;
#can2_dim=6

#--------------------------------Config can device function---------------------------------------------------
def input_thread():
   input()

# FOR sensor data receive
class DBC_INFO(Structure):
	_fields_ = [("matrix_column_value", c_int),
				("matrix_row", c_int),
				("filled_column", c_int),
				("matrix_row_value", c_int),
				("timestamp",c_int)#int timestamp;
				]


class ZCAN_CAN_INIT_CONFIG(Structure):
    _fields_ = [("AccCode",c_int),
                ("AccMask",c_int),
                ("Reserved",c_int),
                ("Filter",c_ubyte),
                ("Timing0",c_ubyte),
                ("Timing1",c_ubyte),
                ("Mode",c_ubyte)]

class ZCAN_CAN_OBJ(Structure):
    _fields_ = [("ID",c_uint32),
                ("TimeStamp",c_uint32),
                ("TimeFlag",c_uint8),
                ("SendType",c_byte),
                ("RemoteFlag",c_byte),
                ("ExternFlag",c_byte),
                ("DataLen",c_byte),
                ("Data",c_ubyte*8),
                ("Reserved",c_ubyte*3)]


def can_start(DEVCIE_TYPE,DEVICE_INDEX,CHANNEL,Brate):
     init_config  = ZCAN_CAN_INIT_CONFIG()
     init_config.AccCode    = 0
     init_config.AccMask    = 0xFFFFFFFF
     init_config.Reserved   = 0
     init_config.Filter     = 1
     init_config.Timing0    = 0x00
     init_config.Timing1    = Brate
     init_config.Mode       = 0
     # Initialize the  Can channel 
     Init_flag=Can_SO.VCI_InitCAN(DEVCIE_TYPE,DEVICE_INDEX,CHANNEL,byref(init_config))
     if Init_flag ==0:
         print("InitCAN fail!")
     else:
         print("InitCAN success!")
      #Start  Can channel    
     start_flag=Can_SO.VCI_StartCAN(DEVCIE_TYPE,DEVICE_INDEX,CHANNEL)
     if start_flag ==0:
         print("StartCAN fail!")
     else:
         print("StartCAN success!")
     return start_flag


def receive_can1_data(matptr,calcul_batch, frequ,sensor_dim):


	Addr=0
	matrix_row_value=calcul_batch*frequ
	obj_sensor=(ZCAN_CAN_OBJ*matrix_row_value)() # struct of data, timestamp, ID
	dbc_info = DBC_INFO(sensor_dim, 0, 0, matrix_row_value,0)

	while 1:
		# ------------------------------------get data matrix--------------------------------------------
		max_sensor_num = Can_SO.VCI_GetReceiveNum(USBCAN2,DEVICE_INDEX,CHANNEL1) # preview the number of data in cache 
		if max_sensor_num:
			
			act_sensor_num = Can_SO.VCI_Receive(USBCAN2,DEVICE_INDEX,CHANNEL1,byref(obj_sensor),min(max_sensor_num,matrix_row_value*can1_num_ID-Addr),0)
			time.sleep(0.1)
			print(max_sensor_num,act_sensor_num,Addr,matrix_row_value*can1_num_ID-Addr)
			Addr=Addr+act_sensor_num
			print(matrix_row_value*3-Addr)
			Model_Sensor_can1_SO.DBC_Decode(byref(obj_sensor), act_sensor_num, matptr, byref(dbc_info)) 
			if Addr == matrix_row_value*can1_num_ID:
				break	
					
		



def combine_matrix_data(matptr, calcul_batch, frequ):


	mat1 = np.zeros([frequ*calcul_batch, can1_dim], np.float64)
	tmp1 = np.asarray(mat1)
	dataptr1 = tmp1.ctypes.data_as(POINTER(c_double))

	receive_can1_data(dataptr1, calcul_batch, frequ,can1_dim)
	return mat1




def p0End():
	Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX,CHANNEL0)
	Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX,CHANNEL1)

# --------------------------------------------------just for testing---------------------------------------------------------
if __name__ == '__main__':

# ----------------------------   run can device config-------------------------------------------


	# ----------------------------can device parameter setting--------------------------------------------------- 
	ZCAN_DEVICE_TYPE  = c_uint32
	ZCAN_DEVICE_INDEX = c_uint32
	ZCAN_Reserved     = c_uint32
	ZCAN_CHANNEL      = c_uint32
	LEN               = c_uint32

	USBCAN2       =   ZCAN_DEVICE_TYPE(4)
	DEVICE_INDEX  =   ZCAN_DEVICE_INDEX(0)
	Reserved      =   ZCAN_Reserved(0)

# specify which channel to receive data 0--> channel 0      1--> channel 1
	CHANNEL0       =   ZCAN_CHANNEL(0) # for receiving acceleration 
	CHANNEL1       =   ZCAN_CHANNEL(1) # for receiving time and speed 

	Brate0=0x14 # bode rate for channel 0 
	Brate1=0x14 # bode rate for channel 1
# close can if they open unexpectally 
	bRel0=Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX, CHANNEL0) # close can 1
	bRel1=Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX, CHANNEL1)  # close can 2

# open device
	open_flag=Can_SO.VCI_OpenDevice(USBCAN2,DEVICE_INDEX,Reserved) # open device 
	
	if open_flag ==0:
	 	print("Opendevice fail!")
	else:
     		print("Opendevice success!")

# start can 
	canstart0 = can_start(USBCAN2,DEVICE_INDEX,CHANNEL0,Brate0) # start can 0
	canstart1 = can_start(USBCAN2,DEVICE_INDEX,CHANNEL1,Brate1) # start can 1

# define buffer 
#vci_can_obj_time = (VCI_CAN_OBJ * 2500)()  # Buffer
#vci_can_obj_data = (VCI_CAN_OBJ * 100000)()  # Buffer

# -------------------------------mock ------------------------------------------
	frequ = 512  		# sample frequency
	calcul_batch = 10  	# calculate batch time
	nIn_a = 21  		# the input number of A model

	mat = np.zeros([frequ*calcul_batch, nIn_a], np.float64)
	# get the pointer of a smat
	tmp = np.asarray(mat)
	dataptr = tmp.ctypes.data_as(POINTER(c_double))
	print('start receiving data')
	count = 1 
	while True:
		try:			
			mat1=combine_matrix_data(dataptr, calcul_batch, frequ)
			print('------------finish----------------' + str(count) )
			count = count + 1
			# np.savetxt("test_sensor_data.csv",mat1,delimiter=",")
			# print(mat1)
			# bRel0=Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX, CHANNEL0) # close can 1
			# bRel1=Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX, CHANNEL1)  # close can 2
		except(KeyboardInterrupt):
			p0End()
			print("Finished Successfully")
