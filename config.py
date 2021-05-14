import os
import time
import logging
import numpy as np
import cantools
from scipy import signal
from writeUploadRemoveFileClass import WriteFile
from logging.handlers import TimedRotatingFileHandler

vehicle_db = cantools.database.load_file('./Ccode/Vehicle_Sensor/canvehicle.Dbc')

header_input_str='Time,Speed,Brake,Gyro_Y,Gyro_X,Acc_Y_FM,Gyro_Z,Acc_X_FM,Acc_Z_FM,Acc_Z_Whl_LF,Acc_Y_Whl_LF,Acc_X_Whl_LF,Acc_Z_Whl_RF,Acc_Y_Whl_RF,Acc_X_Whl_RF,Acc_Y_Whl_LR,Acc_X_Whl_LR,Acc_Z_Whl_LR,Acc_Y_Whl_RR,Acc_X_Whl_RR,Acc_Z_Whl_RR,Acc_X_RM,Acc_Y_RM,Acc_Z_RM'



header_result_str='Time,Dis_Dmp_LF,Dis_Dmp_LR,Dis_Dmp_RF,Dis_Dmp_RR,WFT_Fx_LF,WFT_Fx_LR,WFT_Fx_RF,WFT_Fx_RR,WFT_Fy_LF,WFT_Fy_LR,WFT_Fy_RF,WFT_Fy_RR,WFT_Fz_LF,WFT_Fz_LR,WFT_Fz_RF,WFT_Fz_RR,WFT_Mx_LF,WFT_Mx_LR,WFT_Mx_RF,WFT_Mx_RR,WFT_My_LF,WFT_My_LR,WFT_My_RF,WFT_My_RR,WFT_Mz_LF,WFT_Mz_LR,WFT_Mz_RF,WFT_Mz_RR'




# header_input_str = 'Acc_X_Whl_FL,Acc_Y_Whl_FL,Acc_Z_Whl_FL,\
# Acc_X_Whl_FR,Acc_Y_Whl_FR,Acc_Z_Whl_FR,\
# Acc_X_Whl_RL,Acc_Y_Whl_RL,Acc_Z_Whl_RL,\
# Acc_X_Whl_RR,Acc_Y_Whl_RR,Acc_Z_Whl_RR,\
# Dis_Dmp_FR,Dis_Dmp_FL,Dis_Dmp_RL,Dis_Dmp_RR,\
# Acc_X_FM,Acc_Y_FM,Acc_Z_FM,\
# Acc_X_RM,Acc_Y_RM,Acc_Z_RM'


# upload param
admin_ip = 'wy@202.121.180.27'
password = '^ac6Pox0ROMt'
source_fold = '/IVHM/'
onedrive_fold = './'
destination_fold = '/home/wy/matlab_example/scpTest/'

# write param
step_num = 1


threashold_spd = 1

class Param:  
    def __init__(self, freque, spdfre, step_time, nAll_channel, nOu_a, nIn_b, nOu_b, r, d, nPre_channel, theta_path):
        self.freque    = freque
        self.spdfre    = spdfre
        self.step_time = step_time
        self.nAll_channel = nAll_channel
        self.nOu_a     = nOu_a
        self.nIn_b     = nIn_b
        self.nOu_b     = nOu_b
        self.r         = r
        self.d         = d
        self.nPre_channel = nPre_channel
        self.theta_path= theta_path


    def displayParam(self):
        print("frequency : ", self.freque, ", step_time: ", self.step_time, ", nAll_channel: ", self.nAll_channel, ", output_dim: ", self.nOu_a)


def get_time():
	# Func : to get the current time
	time_tup = time.localtime(time.time())
	format_time='%Y_%m_%d-%H_%M_%S'
	cur_time = time.strftime(format_time, time_tup)
	return cur_time

def setUpLogger(log_name):
    log_fold = './log/'
    is_exist = os.path.exists(log_fold)
    if not is_exist:
        os.makedirs(log_fold)

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)        
    handler = TimedRotatingFileHandler(log_fold + log_name + ".log", 
                                    when="m",
                                    interval=5)    #backupCount=2   
    formatter = logging.Formatter("--%(asctime)s--%(levelname)s--%(message)s", \
                                datefmt="%Y-%m-%d %H:%M:%S")                                     
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def testFun(p, flag, que):
    count = 1

    # if flag==1:
    #     AbnormityWriter = WriteFile('abnormity/', step_num)
    #     abnorm_threshold = np.zeros([1, p.nAll_channel]) + 100

    while True:
        try:
            if flag==1:
                mat = np.arange(p.freque*p.step_time*p.nAll_channel, dtype=np.float64).reshape(p.freque*p.step_time, p.nAll_channel)

            
            elif flag==2:
                mat = np.arange(p.spdfre*p.step_time, dtype=np.float64).reshape(p.spdfre*p.step_time, 1)  #,dtype=np.float64
            
            mat_str = mat.tostring()
            que.put(mat_str)

            message = str(flag) + ' count is ' + str(count) + ', queue size : ' + str(que.qsize())
            print(message)

            count = count + 1
            # if count > 10:
            #     break
            
            time.sleep(p.step_time)
        except(KeyboardInterrupt):
            break

def myresample(mat, calcul_batch, frequ):
    resample_mat = mat
    for c in range(0, mat.shape[1]):
        if mat[0, c] != -1:
            vec = mat[:, c]
            vec = vec[np.where(vec!=-1)]
            vec_new = signal.resample(vec, calcul_batch*frequ)
            resample_mat[:, c] = vec_new                   
    return resample_mat

    vec = mat[np.where(mat!=-1)]
    mat_new = signal.resample(mat, calcul_batch*frequ)
    return mat_new

def myspeedDecodeResample(obj_can0, act_num_can0, frequ):
    print('I am into decoding...')
    count=0
    list_can0=[]
    while count < act_num_can0:
        print('I am into decodingdecoding while...')
        count = count+1
        if (obj_can0[count].ID == 0x353):  # ID of speed channel
            print('I am into decoding while if...')
            spd = vehicle_db.decode_message(obj_can0[count].ID, obj_can0[count].Data)
            print('I finish decoding...')
            for k, v in spd.items():
                if k == 'VehSpdAvgDrvnHSC1':  # name of speed channel VehSpdAvgDrvnHSC1
                    print('k == VehSpdAvgDrvnHSC1:')
                    if v == 'km/h (0x0 - 0x7FFF)':
                        print('km/h (0x0 - 0x7FFF)')
                        list_can0.append(0)
                    else:
                        print('end')
                        spd = float(v)
                        list_can0.append(spd)
                    break        
    mat_can0 = np.asarray(list_can0)
    print('np.asarray')
    mat_can0 = signal.resample(mat_can0, frequ)
    print('resample')
    mat_can0 = mat_can0.reshape(mat_can0.shape[0], 1)
    print('reshape')

    return  mat_can0


def generateBlankTxtFile():

    blank_input_path = './input/'+get_time()[5:10] +'/'
    blank_input_date_file = './input/'+get_time()[5:10] 
    blank_result_path = './result/'+get_time()[5:10] +'/'
    blank_result_date_file = './result/'+get_time()[5:10] 

    is_exist = os.path.exists(blank_input_path)
    if not is_exist:
        os.makedirs(blank_input_path)

    is_exist = os.path.exists(blank_result_path)
    if not is_exist:
        os.makedirs(blank_result_path)
    os.system('chmod 777 ' + blank_input_date_file)
    
    with open(blank_input_path + get_time() + '.txt', 'w') as f:
        f.write('No need for computing')
    os.system('chmod 777 ' + blank_input_path + get_time() + '.txt')
    #os.chmod(blank_input_path)

    os.system('chmod 777 ' + blank_result_date_file)
    with open(blank_result_path + get_time() + '.txt', 'w') as f:
        f.write('No need for computing')
    
    os.system('chmod 777 ' + blank_result_path + get_time() + '.txt')
    