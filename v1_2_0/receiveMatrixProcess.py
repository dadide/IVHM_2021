import cantools
import time
import platform
import config
import numpy as np
from ctypes import *
from scipy import signal

#-------------------------------------Load dynamic lib-----------------------------------------

Can_SO = cdll.LoadLibrary('./Ccode/Can/libusbcan.so') #  can lib
CanFD_SO = cdll.LoadLibrary('./Ccode/CanFD/libusbcanfd.so') #  canFD lib


can0_SO = cdll.LoadLibrary('./Ccode/Vehicle_Sensor/can0.so') #  lib of sensors for estimating data
can1_SO = cdll.LoadLibrary('./Ccode/Model_Sensor/can1.so') #  lib of sensors for estimating data
canfd0_SO = cdll.LoadLibrary('./Ccode/Model_Sensor/canfd0.so') #  lib of sensors for estimating data 
canfd1_SO = cdll.LoadLibrary('./Ccode/Model_Sensor/canfd1.so') #  lib of sensors for estimating data  

vehicle_db = cantools.database.load_file('./Ccode/Vehicle_Sensor/canvehicle.Dbc')
# -------------can 0------------------------------
dim_can0=2
# id_num_can0=1

# -------------can 1------------------------------
dim_can1=6
id_num_can1=2

# -------------canfd 0------------------------------
dim_canfd0=6
id_num_canfd0=2

# # -------------canfd 1------------------------------
dim_canfd1=9
id_num_canfd1=3



def p0End():
	Can_SO.VCI_ResetCAN(USBCAN2,DEVICE_INDEX,CHANNEL0)
	Can_SO.VCI_ResetCAN(USBCAN2,DEVICE_INDEX,CHANNEL1)
	Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX,CHANNEL0)
	Can_SO.VCI_CloseDevice(USBCAN2,DEVICE_INDEX,CHANNEL1)

	CanFD_SO.VCI_ResetCAN(USBCANFD_200U,DEVICE_INDEX,ZCANFD_CHANNEL0)
	CanFD_SO.VCI_ResetCAN(USBCANFD_200U,DEVICE_INDEX,ZCANFD_CHANNEL1)
	CanFD_SO.VCI_CloseDevice(USBCANFD_200U,DEVICE_INDEX)




#--------------------------------Config can device function---------------------------------------------------
# def input_thread():
#	input()

# FOR sensor data receive
class DBC_INFO(Structure):
	_fields_ = [("matrix_column_value", c_int),
				("matrix_row", c_int),
				("frequency", c_int),
				("matrix_row_value", c_int),
				("timestamp",c_int),#int timestamp;
				("calcul_batch",c_int),
				('id_num_can',c_int)
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
	 init_config.AccCode	= 0
	 init_config.AccMask	= 0xFFFFFFFF
	 init_config.Reserved   = 0
	 init_config.Filter	 = 1
	 init_config.Timing0	= 0x00
	 init_config.Timing1	= Brate
	 init_config.Mode	   = 0
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


# -------------------------------------------config canfd function---------------------------------------
#Terminating resistor
class Resistance(Structure):
	_fields_=[("res",c_uint8)
			  ]
			  
class ZCAN_MSG_INFO(Structure):
	_fields_=[("txm",c_uint,4), # TXTYPE:0 normal,1 once, 2self
			  ("fmt",c_uint,4), # 0-can2.0 frame,  1-canfd frame
			  ("sdf",c_uint,1), # 0-data frame, 1-remote frame
			  ("sef",c_uint,1), # 0-std_frame, 1-ext_frame
			  ("err",c_uint,1), # error flag
			  ("brs",c_uint,1), # bit-rate switch ,0-Not speed up ,1-speed up
			  ("est",c_uint,1), # error state 
			  ("pad",c_uint,19)]


#CAN Message Header
class ZCAN_MSG_HDR(Structure):  
	_fields_=[("ts",c_uint32),  #timestamp
			  ("ID",c_uint32),  #can-id
			  ("info",ZCAN_MSG_INFO),
			  ("pad",c_uint16),
			  ("chn",c_uint8),  #channel
			  ("len",c_uint8)]  #data length

#CAN2.0-frame
class ZCAN_20_MSG(Structure):  
	_fields_=[("msg_header",ZCAN_MSG_HDR),
			  ("Data",c_ubyte*8)]


class abit_config(Structure):
	_fields_=[("tseg1",c_uint8),
			  ("tseg2",c_uint8),
			  ("sjw",c_uint8),
			  ("smp",c_uint8),
			  ("brp",c_uint16)]

class dbit_config(Structure):
	_fields_=[("tseg1",c_uint8),
			  ("tseg2",c_uint8),
			  ("sjw",c_uint8),
			  ("smp",c_uint8),
			  ("brp",c_uint16)]


class ZCANFD_INIT(Structure):
	_fields_=[("clk",c_uint32),
			  ("mode",c_uint32),
			  ("abit",abit_config),
			  ("dbit",dbit_config)]


def canfd_start(Devicetype,DeviceIndex,Channel):
	Res	 = Resistance()
	Res.res = RES_ON
	CanFD_SO.VCI_SetReference(Devicetype,DeviceIndex,Channel,CAN_TRES,byref(Res))
	canfd_init=ZCANFD_INIT()	   #1M+1M
	canfd_init.clk		 =   60000000
	canfd_init.mode		=   0
	canfd_init.abit.tseg1  =   7
	canfd_init.abit.tseg2  =   2
	canfd_init.abit.sjw	=   2
	canfd_init.abit.smp	=   0
	canfd_init.abit.brp	=   4
	canfd_init.dbit.tseg1  =   7
	canfd_init.dbit.tseg2  =   2
	canfd_init.dbit.sjw	=   2
	canfd_init.dbit.smp	=   0
	canfd_init.dbit.brp	=   4
	ret=CanFD_SO.VCI_InitCAN(Devicetype,DeviceIndex,Channel,byref(canfd_init))
	if ret ==0:
		print("init failed!")
	else:
		print("init success!")
	ret=CanFD_SO.VCI_StartCAN(Devicetype,DeviceIndex,Channel)


# ----------------------------can device parameter setting--------------------------------------------------- 
ZCAN_DEVICE_TYPE  = c_uint32
ZCAN_DEVICE_INDEX = c_uint32
ZCAN_Reserved	 = c_uint32
ZCAN_CHANNEL	  = c_uint32
LEN			   = c_uint32

USBCAN2	   =   ZCAN_DEVICE_TYPE(4)
DEVICE_INDEX  =   ZCAN_DEVICE_INDEX(0)
Reserved	  =   ZCAN_Reserved(0)

# specify which channel to receive data 0--> channel 0	  1--> channel 1
CHANNEL0	   =   ZCAN_CHANNEL(0) # for receiving acceleration 
CHANNEL1	   =   ZCAN_CHANNEL(1) # for receiving time and speed 

Brate0=0x1C # bode rate for channel 0 
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


# ----------------------------   run canFD device config-------------------------------------------
RES_ON			= 1  #Resistance setting
RES_OFF		   = 0
CAN_TRES		  = 0x18 #Resistance address
USBCANFD_200U =   ZCAN_DEVICE_TYPE(33)
DEVICE_INDEX  =   ZCAN_DEVICE_INDEX(0)
ZCANFD_CHANNEL0 =   ZCAN_CHANNEL(0)
ZCANFD_CHANNEL1 =   ZCAN_CHANNEL(1)

# close can if they open unexpectally 
ret=CanFD_SO.VCI_CloseDevice(USBCANFD_200U,DEVICE_INDEX)

open_flag=CanFD_SO.VCI_OpenDevice(USBCANFD_200U,DEVICE_INDEX,Reserved)
if open_flag ==0:
 	print("Open Canfd device fail!")
else:
 		print("Open Canfd device success!")

# start can 
canfd_start(USBCANFD_200U,DEVICE_INDEX,ZCANFD_CHANNEL0)
canfd_start(USBCANFD_200U,DEVICE_INDEX,ZCANFD_CHANNEL1)


# -------------my function------------------------------
def receive_can_data(calcul_batch, frequ, nPre_channel, decode_time):
	matrix_row_value = frequ * calcul_batch

	s1_time = time.time()
	# ---------------------------------------can 0---------------------------------------
	# EPTAccelActuPosHSC1
	# BrkPdlDrvrAppdPrsHSC1
	# BrkPdlPos_h1HSC1
	# VehSpdAvgDrvnHSC1
	
	spd_list_can0 = []
	brk_list_can0 = []
	obj_can0 = (ZCAN_CAN_OBJ * 100000)()
	spd_mat_can0 = np.zeros([frequ * calcul_batch, 1], np.float64) - 1
	brk_mat_can0 = np.zeros([frequ * calcul_batch, 1], np.float64) - 1
	
	# tmp_can0 = np.asarray(mat_can0)
	# dataptr_can0 = tmp_can0.ctypes.data_as(POINTER(c_double))
	# dbc_info_can0 = DBC_INFO(dim_can0, 0, frequ, matrix_row_value, 0, calcul_batch, id_num_can0)

	# # ---------------------------------------can 1---------------------------------------
	obj_can1 = (ZCAN_CAN_OBJ * matrix_row_value)()
	mat_can1 = np.zeros([frequ * calcul_batch, dim_can1], np.float64) - 1
	tmp_can1 = np.asarray(mat_can1)
	dataptr_can1 = tmp_can1.ctypes.data_as(POINTER(c_double))
	dbc_info_can1 = DBC_INFO(dim_can1, 0, frequ, matrix_row_value, 0, calcul_batch, id_num_can1)

	# # ---------------------------------------canfd 0---------------------------------------

	obj_canfd0 = (ZCAN_20_MSG * matrix_row_value)()
	mat_canfd0 = np.zeros([frequ * calcul_batch, dim_canfd0], np.float64) - 1
	tmp_canfd0 = np.asarray(mat_canfd0)
	dataptr_canfd0 = tmp_canfd0.ctypes.data_as(POINTER(c_double))
	dbc_info_canfd0 = DBC_INFO(dim_canfd0, 0, frequ, matrix_row_value, 0, calcul_batch, id_num_canfd0)

	# ---------------------------------------canfd 1---------------------------------------

	obj_canfd1 = (ZCAN_20_MSG * matrix_row_value)()
	mat_canfd1 = np.zeros([frequ * calcul_batch, dim_canfd1], np.float64) - 1
	tmp_canfd1 = np.asarray(mat_canfd1)
	dataptr_canfd1 = tmp_canfd1.ctypes.data_as(POINTER(c_double))
	dbc_info_canfd1 = DBC_INFO(dim_canfd1, 0, frequ, matrix_row_value, 0, calcul_batch, id_num_canfd1)

	init_time = time.time() - s1_time
	print('init_time: ' + str(init_time))

	for i in range(0, calcul_batch):
		# ------------------------------------sleep for fixed time--------------------------------------------
		# if i == 9:
		# 	time.sleep(0.985 - decode_time - init_time)
		# else:
		time.sleep(1 - decode_time - init_time)
		init_time = 0
		s2_time = time.time()

		# # ---------------------------------------receive data from can 0---------------------------------------
		max_num_can0 = Can_SO.VCI_GetReceiveNum(USBCAN2, DEVICE_INDEX, CHANNEL0)  # preview the number of data in cache
		act_num_can0 = Can_SO.VCI_Receive(USBCAN2, DEVICE_INDEX, CHANNEL0, byref(obj_can0), max_num_can0, 100)
		print(max_num_can0, act_num_can0)
		# ---------------------------------------receive data from can 1---------------------------------------
		max_num_can1 = Can_SO.VCI_GetReceiveNum(USBCAN2, DEVICE_INDEX, CHANNEL1)  # preview the number of data in cache
		act_num_can1 = Can_SO.VCI_Receive(USBCAN2, DEVICE_INDEX, CHANNEL1, byref(obj_can1), max_num_can1, 100)
		print(max_num_can1, act_num_can1)

		# ---------------------------------------receive data from canfd 0---------------------------------------
		max_num_canfd0 = CanFD_SO.VCI_GetReceiveNum(USBCANFD_200U, DEVICE_INDEX, ZCANFD_CHANNEL0)
		act_num_canfd0 = CanFD_SO.VCI_Receive(USBCANFD_200U, DEVICE_INDEX, ZCANFD_CHANNEL0, byref(obj_canfd0),
											  max_num_canfd0, 100)
		print(max_num_canfd0, act_num_canfd0)

		# ---------------------------------------receive data from canfd 1---------------------------------------
		max_num_canfd1 = CanFD_SO.VCI_GetReceiveNum(USBCANFD_200U, DEVICE_INDEX, ZCANFD_CHANNEL1)
		act_num_canfd1 = CanFD_SO.VCI_Receive(USBCANFD_200U, DEVICE_INDEX, ZCANFD_CHANNEL1, byref(obj_canfd1),
											  max_num_canfd1, 100)
		print(max_num_canfd1, act_num_canfd1)

		# ////////////////////////////////////////////decode//////////////////////////////////////////////////////
		# --------------------------------------can0 (vehicle sensor)-----------------------------------------------
		
		spd_temp_list = speedDecode(obj_can0, act_num_can0)
		spd_list_can0.extend( spd_temp_list )

		brk_temp_list = brakeDecode(obj_can0, act_num_can0)
		brk_list_can0.extend( brk_temp_list )		
		
		# -------------------------------------- can1 (IMU, 6 dimentions) -----------------------------------------------------
		if act_num_can1 > 0:
			can1_SO.DBC_Decode(byref(obj_can1), act_num_can1, i, dataptr_can1, byref(dbc_info_can1))
		# ---------------------------------------canfd0 (Accelerators 1,2   6 dimentions)----------------------------------------
		if act_num_canfd0 > 0:
			canfd0_SO.DBC_Decode(byref(obj_canfd0), act_num_canfd0, i, dataptr_canfd0, byref(dbc_info_canfd0))
		# ---------------------------------------canfd1 (Accelerators 3,4,5   9 dimentions) ----------------------------------------
		if act_num_canfd1 > 0:
			canfd1_SO.DBC_Decode(byref(obj_canfd1), act_num_canfd1, i, dataptr_canfd1, byref(dbc_info_canfd1))

		decode_time = time.time() - s2_time
		print(dbc_info_can1.matrix_row, dbc_info_canfd0.matrix_row, dbc_info_canfd1.matrix_row)
		print('decode_time: ' + str(decode_time))

	# --------------------------------------can0 (vehicle sensor)-----------------------------------------------
	spd_array_can0 = np.asarray(spd_list_can0)
	brk_array_can0 = np.asarray(brk_list_can0)

	print(brk_array_can0)
	
	try:

		spd_array_can0 = signal.resample_poly(spd_array_can0, frequ * calcul_batch, spd_array_can0.shape[0])
		spd_mat_can0 = spd_array_can0.reshape(spd_array_can0.shape[0], 1)

		brk_array_can0 = signal.resample_poly(brk_array_can0, frequ * calcul_batch, brk_array_can0.shape[0])
		brk_mat_can0 = brk_array_can0.reshape(brk_array_can0.shape[0], 1)
	
	except Exception as e:

		spd_mat_can0 = np.zeros([frequ * calcul_batch, 1], np.float64) - 1
		brk_mat_can0 = np.zeros([frequ * calcul_batch, 1], np.float64) + 1

	# ----------------------------------------------------------------------------------------------------------
#header_input_str='Speed,brake,Gyro_Y,Gyro_X,Acc_Y_FM,Gyro_Z,Acc_X_FM,Acc_Z_FM,Acc_Z_Whl_LF,Acc_Y_Whl_LF,Acc_X_Whl_LF,Acc_Z_Whl_RF,Acc_Y_Whl_RF,Acc_X_Whl_RF,Acc_Y_Whl_LR,Acc_X_Whl_LR,Acc_Z_Whl_LR,Acc_Y_Whl_RR,Acc_X_Whl_RR,Acc_Z_Whl_RR,Acc_X_RM,Acc_Y_RM,Acc_Z_RM'

	combined_matrix = np.hstack((spd_mat_can0, brk_mat_can0, mat_can1, mat_canfd0, mat_canfd1))
	
	combined_matrix[:,1+nPre_channel] = -combined_matrix[:,1+nPre_channel]  # Gyro_X
	combined_matrix[:,4+nPre_channel] = -combined_matrix[:,4+nPre_channel]  # Acc_X_FM
	combined_matrix[:,7+nPre_channel] = -combined_matrix[:,7+nPre_channel]  # Acc_Y_Whl_LF
	combined_matrix[:,9+nPre_channel] = -combined_matrix[:,9+nPre_channel]  # Acc_Z_Whl_RF
	combined_matrix[:,13+nPre_channel] = -combined_matrix[:,13+nPre_channel]  # Acc_X_Whl_LR
	combined_matrix[:,16+nPre_channel] = -combined_matrix[:,16+nPre_channel]  # Acc_X_Whl_RR
	combined_matrix[:,18+nPre_channel] = -combined_matrix[:,18+nPre_channel]  # Acc_X_RM
	combined_matrix[:,19+nPre_channel] = -combined_matrix[:,19+nPre_channel]  # Acc_Y_RM

	# print(combined_matrix.shape)

	#-----------------------------------------------------------------------------------------------------------
	mean_spd = spd_array_can0.mean()
	if mean_spd > config.threashold_spd:
		spd_flag = 1
	else:
		spd_flag = 0

	return (combined_matrix, decode_time, spd_flag)


def speedDecode(obj_can0, act_num_can0):
	temp_list = []

	if act_num_can0 > 0:
		count = 0
		while count < act_num_can0:
			#print(obj_can0[count].ID)
			if (obj_can0[count].ID == 0x3d1):  # ID of speed channel
				spd = vehicle_db.decode_message(obj_can0[count].ID, obj_can0[count].Data)
				
				#print(spd)
				for k, v in spd.items():
					if k == 'VehSpdAvgDrvnHSC5':  # name of speed channel VehSpdAvgDrvnHSC1
						if v == 'km/h (0x0 - 0x7FFF)':
							temp_list.append(0)
						else:
							spd = float(v)
							temp_list.append(spd)
						break
			count = count + 1
	# print(temp_list)
	return temp_list



def brakeDecode(obj_can0, act_num_can0):
	temp_list = []

	if act_num_can0 > 0:
		count = 0
		while count < act_num_can0:
			#print(obj_can0[count].ID)
			if (obj_can0[count].ID == 0xf1):  # ID of speed channel
				brake = vehicle_db.decode_message(obj_can0[count].ID, obj_can0[count].Data)
				
				#print(brake)
				for k, v in brake.items():
				 	brake = float(v)
				 	temp_list.append(brake)
				 		
			count = count + 1
	# print(temp_list)
	return temp_list



