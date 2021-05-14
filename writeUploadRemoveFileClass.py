import os
import time
import config
import numpy as np

class WriteFile():
    def __init__(self, fold, step_num):
        self.fold = fold       
        self.step_num = step_num
        self.file_count = 1
        # self.logger = config.setUpLogger("write")
   
    def getFileName(self):
        INDEX_OF_FLAG = -5
        cur_time = config.get_time()

        date_folder = config.onedrive_fold + self.fold + cur_time[5:10] +'/'
        is_exist = os.path.exists(date_folder)
        if not is_exist:
            os.makedirs(date_folder)
        
        files = os.listdir(date_folder)
        not_full_file = [i for i in files if i[INDEX_OF_FLAG]!='F' and i[INDEX_OF_FLAG+1:]=='.csv']
        
        if len(not_full_file) == 0:
            file_name = cur_time + '-' + str(self.file_count) + '-1.csv'
            with open(date_folder + file_name, 'a+') as f:
                if self.fold == 'input/':
                    f.write(config.header_input_str+'\n')
                elif self.fold == 'result/':
                    f.write(config.header_result_str+'\n')
                # elif self.fold == 'speed/':
                #     f.write(config.header_speed_str+'\n')
                # else:
                #     f.write("Maybe wrong folder!\n")
        elif len(not_full_file) == 1:           
            file_name = not_full_file[0]
        else:
            # log_flag = 0
            # command = str(not_full_file)
            # self.generateLog(command, log_flag)
            file_name = 'somethingwrong.txt'

        return file_name, date_folder

    def save2File(self, npArray, p):

        # freque, spdfre, step_time, nIn_a, nOu_a, nIn_b, nOu_b, r, d, theta_path
        INDEX_OF_FLAG = -5
        
        timeArray=np.linspace(0, p.step_time*config.step_num, p.freque*p.step_time*config.step_num, endpoint=False)
        timeArray = timeArray.reshape(p.freque*p.step_time*config.step_num, 1)
        
        npArray = np.hstack((timeArray, npArray))

        [file_name, date_folder] = self.getFileName()
        with open(date_folder + file_name, 'a+') as f:
            np.savetxt(f, npArray, fmt='%.4f', delimiter=',')

        # change name for current files
        self.file_count = self.file_count + 1
        if file_name[INDEX_OF_FLAG] != str(self.step_num):
            new_file_name = file_name[:INDEX_OF_FLAG] + str(int(file_name[INDEX_OF_FLAG])+1) + file_name[INDEX_OF_FLAG+1:]
        else:
            new_file_name = file_name[:INDEX_OF_FLAG] + 'F' + file_name[INDEX_OF_FLAG+1:]
        os.rename(date_folder + file_name, date_folder + new_file_name)
        exitcode = os.system('chmod 777 ' + date_folder + new_file_name)
        #print(date_folder)
        # # logging
        # log_flag = 1
        # command = file_name + ' to new filename: ' + new_file_name
        # self.generateLog(command, log_flag)

    # def generateLog(self, command, log_flag):
    #     if log_flag == 0:
    #         message = 'Error!!! Because there are more than one not-full files: ' + command
    #         self.logger.error(message)
    #     elif log_flag == 1:
    #         message = 'Success~~ Change old filename: ' + command
    #         self.logger.debug(message)

# if __name__ == "__main__":
#     fold = './input/'
#     step_num = 5
#     a = WriteFile(fold, step_num)
#     for i in range(1,9):
#         print(i)
#         result = np.zeros([3,10]) + i
#         a.save2File(result)



class UploadRemoveFile:
    def __init__(self, admin_ip, password, onedrive_fold, destination_fold):
        self.admin_ip = admin_ip
        self.password = password
        self.onedrive_fold = onedrive_fold
        self.destination_fold = destination_fold
        self.logger = config.setUpLogger("upRm")

    def getFoldSize(self, file_fold):
        fold = self.onedrive_fold + file_fold
        size = sum( os.path.getsize(fold + f) for f in os.listdir(fold) if os.path.isfile(fold + f) ) /1024 /1024
        size = round(size, 2)
        return size

    def findFullFile(self, file_fold):
        INDEX_OF_FLAG = -5
        files = os.listdir(self.onedrive_fold + file_fold)
        full_files = [i for i in files if i[INDEX_OF_FLAG]=='F' or i[INDEX_OF_FLAG+1]!='.' and i!='.DS_Store']    
        
        if full_files == []:
            log_flag = -1
            emptyCommand = file_fold
            self.generateLog(emptyCommand, log_flag)
        else:
            log_flag = -2
            fullCommand = file_fold + ' folder size is ' + str(self.getFoldSize(file_fold)) + 'Mb' # + '. Files are ' + str(full_files)
            self.generateLog(fullCommand, log_flag)
        return full_files

    def uploadFile(self, file_fold, file_name):
        uploadCommand = 'sshpass -p ' + self.password + ' scp -P 996 -C ' + self.onedrive_fold + file_fold \
                        + file_name + ' ' + self.admin_ip + ':' + self.destination_fold + file_fold
        # print(uploadCommand)
        exit_code = os.system(uploadCommand)
        # exit_code = 1
        
        if exit_code != 0:
            log_flag = 1
            self.generateLog(uploadCommand, log_flag)
        else:
            log_flag = 0
            self.generateLog(uploadCommand, log_flag)
        return exit_code

    def removeFile(self, file_fold, file_name):
        removeCommand = 'rm ' + self.onedrive_fold + file_fold + file_name 
        # print(removeCommand)
        exit_code = os.system(removeCommand)
        # exit_code = 2
        if exit_code != 0:
            log_flag = 1
            self.generateLog(removeCommand, log_flag)
        else:
            log_flag = 0
            self.generateLog(removeCommand, log_flag)
        # return exit_code

    def findUploadRemoveFile(self, file_fold):
        full_file_list = self.findFullFile(file_fold)
        for i in range(0, len(full_file_list)):
            file_name = full_file_list[i]
            if self.uploadFile(file_fold, file_name) == 0:
                self.removeFile(file_fold, file_name)
            else:
                break

    def generateLog(self, command, log_flag):
        if log_flag == 0:
            message = 'Success~~ ' + command
            self.logger.info(message)
        elif log_flag == 1 :
            message = 'Failed!!! ' + command
            self.logger.warning(message)
        elif log_flag == -1:
            message = 'Please wait, empty in ' + command
            self.logger.warning(message)
        elif log_flag == -2:
            message = command
            self.logger.info(message)



# if __name__ == "__main__":
#     admin_ip = 'wy@202.121.180.27'
#     password = '123'
#     # onedrive_fold = '/IVHM/'
#     onedrive_fold = './'
#     destination_fold = '/home/wy/matlab_example/scpTest/'
#     inputUpRm = UploadRemoveFile(admin_ip, password, onedrive_fold, destination_fold)

#     file_fold = 'input/' # or 'result/', 'speed/'

#     inputUpRm.findUploadRemoveFile(file_fold)

    # flag = 1 
    # if flag == 1:
    #     file_name = 'result.csv'
    #     ec1 = inputUpRm.uploadFile(file_fold, file_name)
    #     ec2 = inputUpRm.removeFile(file_fold, file_name)
    # else:
    #     full_file_list = inputUpRm.findFullFile(file_fold)
    #     print(full_file_list)
    #     for i in range(0, len(full_file_list)):
    #         file_name = full_file_list[i]
    #         inputUpRm.uploadFile(file_fold, file_name)
    #         inputUpRm.removeFile(file_fold, file_name)

