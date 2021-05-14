import receiveMatrixProcess
import estimateOutputProcess
from writeUploadRemoveFileClass import UploadRemoveFile, WriteFile
import time
import os
import config
import numpy as np
from ctypes import *
from multiprocessing import Process, Queue

# 2021.3.16----channel add!

matrix_test_flag = 0

def receiveMatrixFun(p, queue_matrix):

    if matrix_test_flag == 1:
        print('matrix_test_flag == 1')
        config.testFun(p, 1, queue_matrix)      # generate data we need to test
    else:
        print('matrix_test_flag == 0')
        count = 1

        logger = config.setUpLogger("receive")
        # AbnormityWriter = WriteFile('abnormity/', config.step_num)   #so every 30s*10=5min will generate a abnormal csv 
        
        # abnorm_threshold = np.zeros([1, p.nIn_a]) + 100
        # abnorm_threshold = np.array([100, 100, 100, 100, 100, 100, 100, 100, 100])

        decode_time = 0.5
       

        while True:
            # receiveMatrixProcess.receive_data(dataptr, p.step_time, p.freque)
            (mat1, decode_time, spd_flag) = receiveMatrixProcess.receive_can_data(p.step_time, p.freque, p.nPre_channel, decode_time)
            # print(mat1)
            # print(spd_flag)
            #spd_flag = 1
            if spd_flag == 1:
                mat_str = mat1.tostring()
                queue_matrix.put(mat_str)

                # abnormity = np.sum( (abs(mat1) > abnorm_threshold), axis=0)
                # AbnormityWriter.save2File(abnormity.reshape(1, p.nIn_a)) 

                message = 'Received no.%d step data ---- computing!' % count
                print(message)
                logger.info(message)

                count = count + 1
            else:

                message = 'Received data when low speed or stopping ---- not compute'
                print(message)
                logger.info(message)

                config.generateBlankTxtFile()




def estimateOutputFun(p, queue_matrix):

    
    ResultWriter = WriteFile('result/', config.step_num)
    InputWriter = WriteFile('input/', config.step_num)

    [theta_a3d, theta_b3d, mean_in, mean_out] = estimateOutputProcess.loadTheta(p)
    last_r_d = np.zeros([p.r + p.d, p.nAll_channel])
    
    logger = config.setUpLogger("estimate")

    while True:
        try:
            if queue_matrix.empty():
                time.sleep(1)
            else:
                batch_input = estimateOutputProcess.getDataFromQueue(queue_matrix, p)
                stacked_batch_input = np.vstack((last_r_d, batch_input))

                last_r_d = batch_input[-(p.r + p.d):, :]

                t1 = time.time()
                [phi_a, phi_b, y_batch_true_b, ks, ke] = estimateOutputProcess.constructData(p, mean_in, stacked_batch_input)
                model_index = estimateOutputProcess.chooseModel(phi_b, theta_b3d, y_batch_true_b, ks, ke)
                y_batch_pred_a = estimateOutputProcess.estimateOutput(phi_a, theta_a3d, model_index, mean_out, ks, ke)
                t2 = time.time()

                ResultWriter.save2File(y_batch_pred_a, p)                                              
                InputWriter.save2File(batch_input, p)
                t3 = time.time()
                message = 'estimate consumes:{:0.2f}, write consumes:{:0.2f}'.format(t2-t1, t3-t2)
                logger.info(message)
                print(message)
        except Exception as e:
            print(e)
            break


def uploadRmFileFun():
    UpRm = UploadRemoveFile(config.admin_ip, config.password, config.source_fold, config.destination_fold)
    while True:
        try:
            UpRm.findUploadRemoveFile('input/')
            time.sleep(1)
            UpRm.findUploadRemoveFile('result/')
            time.sleep(1)
            UpRm.findUploadRemoveFile('log/')
            time.sleep(1)
            UpRm.findUploadRemoveFile('abnormity/')
            time.sleep(1)     
        except:
            break

if __name__ == "__main__":

    # p = config.Param(512, 10, 10, 22, 28, 18, 3, 20, 0, 'MTheta/') # before changing
    p = config.Param(512, 10, 10, 23, 28, 18, 3, 20, 0, 2, 'MTheta/')  # after changing

    # p = config.Param(512, 10, 10, 9, 70, 6, 3, 50, 0, 'MTheta/')    #canfd1


    # freque, spdfre, step_time, nAll_channel, nOu_a, nIn_b, nOu_b, r, d, nPre_channel, theta_path      

    queue_matrix = Queue()


    # process1 = Process(target=receiveMatrixFun, kwargs={"p":p, "queue_matrix":queue_matrix})
    # process2 = Process(target=receiveSpeedFun, kwargs={"p":p, "queue_speed":queue_speed})
    process3 = Process(target=estimateOutputFun, kwargs={"p":p, "queue_matrix":queue_matrix})
    # process4 = Process(target=uploadRmFileFun, kwargs={})

    # process1.start()
    # process2.start()   
    process3.start()
    # process4.start()

    try:
        receiveMatrixFun(p, queue_matrix)
        # process1.join()
        # process2.join()
        process3.join()

        # process4.join()
    except Exception as e:
        # process1.terminate()
        # process1.join()

        # process2.terminate()
        # process2.join()
        print(e)
        process3.terminate()
        process3.join()

        # process4.terminate()
        # process4.join()

        receiveMatrixProcess.p0End()
        print("Finished successfully!")
        
