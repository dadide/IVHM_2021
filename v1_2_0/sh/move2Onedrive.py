import os
import time
import logging
import numpy as np
from logging.handlers import TimedRotatingFileHandler

def setUpLogger(log_name):
    log_fold = '/home/efc/SJTUdrive/move_log/'
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


class UploadRemoveFile:
    def __init__(self, source_fold, destination_fold):
        self.source_fold = source_fold
        self.destination_fold = destination_fold
        self.logger = setUpLogger("Move")

    def getFoldSize(self, file_fold):
        fold = self.source_fold + file_fold
        size = sum( os.path.getsize(fold + f) for f in os.listdir(fold) if os.path.isfile(fold + f) ) /1024 /1024
        size = round(size, 2)
        return size

    def findFullFile(self, file_fold):
        INDEX_OF_FLAG = -5
        files = os.listdir(self.source_fold + file_fold)
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

    def checkAndGenerateDateFold(self, file_fold, file_name):
        #  '%Y_%m_%d-%H_%M_%S' 2021_01_01-
        date_foldpath = self.destination_fold + file_fold + file_name[5:10]
        is_exist = os.path.exists(date_foldpath)
        if not is_exist:
            os.makedirs(date_foldpath)
        return date_foldpath


    def moveFile(self, file_fold, file_name):
        date_foldpath = self.checkAndGenerateDateFold(file_fold, file_name)
        moveCommand = 'mv ' + self.source_fold + file_fold + file_name + ' ' + date_foldpath
        print(moveCommand) 
        exit_code = os.system(moveCommand)
        # exit_code = 1
        
        if exit_code != 0:
            log_flag = 1
            self.generateLog(moveCommand, log_flag)
        else:
            log_flag = 0
            self.generateLog(moveCommand, log_flag)
        return exit_code


    def findMoveFile(self, file_fold):
        full_file_list = self.findFullFile(file_fold)
        for i in range(0, len(full_file_list)):
            file_name = full_file_list[i]
            self.moveFile(file_fold, file_name)


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



if __name__ == "__main__":
    source_fold = '/home/efc/xiansensor_exp/'
    destination_fold = '/home/efc/SJTUdrive/'
    inputUpRm = UploadRemoveFile(source_fold, destination_fold)

    while 1 :
        file_fold = 'input/' # or 'result/', 'speed/'
        inputUpRm.findMoveFile(file_fold)

        file_fold = 'result/' # or 'result/', 'speed/'
        inputUpRm.findMoveFile(file_fold)

        file_fold = 'speed/' # or 'result/', 'speed/'
        inputUpRm.findMoveFile(file_fold)

        file_fold = 'log/' # or 'result/', 'speed/'
        inputUpRm.findMoveFile(file_fold)
