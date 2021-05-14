import os
import time
import numba
import config
import numpy as np
from scipy.io import loadmat
import writeUploadRemoveFileClass



def loadTheta(p):
	
	# Func: To get the saved 3d theta matrix
	
	# theta_a3d_name = "MTheta_" + str(p.nIn_a) + 'I' + str(p.nOu_a) + 'O'	#"MTheta_18I6O.mat"
	# theta_b3d_name = "MTheta_" + str(p.nIn_b) + 'I' + str(p.nOu_b) + 'O'	#"MTheta_12I2O.mat"

	# theta_a3d_name = "MTheta_22I70O"
	# theta_b3d_name = "MTheta_16I6O"

	theta_a3d_name = "MTheta_21I28O"
	theta_b3d_name = "MTheta_18I3O"
	mean_in_name = "mean_in"
	mean_out_name = "mean_out"

	theta_a3d = loadmat(config.source_fold + p.theta_path + theta_a3d_name)
	theta_b3d = loadmat(config.source_fold + p.theta_path + theta_b3d_name)
	mean_in   = loadmat(config.source_fold + p.theta_path + mean_in_name)
	mean_out  = loadmat(config.source_fold + p.theta_path + mean_out_name)

	theta_a3d = theta_a3d["MTheta"]									  #得到 theta_a，是一个三维array
	theta_b3d = theta_b3d["MTheta"] 
	mean_in   = mean_in["mean_in"]
	mean_out  = mean_out["mean_out"] 

	# print(theta_a3d.shape)

	theta_a3d = theta_a3d[:, 0:(p.r+1+p.d)*(p.nAll_channel-p.nPre_channel), :]
	theta_b3d = theta_b3d[:, 0:(p.r+1+p.d)*p.nIn_b, 0:p.nOu_b]

	print((p.r+1+p.d)*(p.nAll_channel-p.nPre_channel))

	# print(theta_a3d.shape)
	# print(theta_b3d.shape)

	return theta_a3d, theta_b3d, mean_in, mean_out


def constructData(p, mean_in, batch_input):

	# Func: To get the Phi , Y from batch_input and corresponding index_slice

	input_index_a = list(range(0+p.nPre_channel, p.nAll_channel))
	input_index_b = list(range(0+p.nPre_channel, p.nIn_b+p.nPre_channel))
	output_index_b = list(range(p.nIn_b+p.nPre_channel, p.nIn_b+p.nOu_b+p.nPre_channel))
	# print(input_index_a, input_index_b, output_index_b)

	batch_input_a = batch_input[:, input_index_a] - mean_in
	batch_input_b = batch_input[:, input_index_b]
	y_batch_true_b = batch_input[:, output_index_b]
	
	batch_input_b = batch_input_b - batch_input_b.mean(axis=0)
	y_batch_true_b = y_batch_true_b - y_batch_true_b.mean(axis=0)
	
	# message = 'Dimension check----'+str(batch_input_a.shape) + ' '+str(batch_input_b.shape)+ ' '+str(y_batch_true_b.shape)
	# print(message)
	
	# print(batch_input_a.shape)
	# print(batch_input_b.shape)
	# print(y_batch_true_b.shape)

	phi_a, phi_b, ks, ke = constructPhi(p.r, p.d, batch_input_a, batch_input_b, p.nAll_channel-p.nPre_channel, p.nIn_b)

	return phi_a, phi_b, y_batch_true_b, ks, ke


@numba.jit(nopython=True)
def constructPhi(r, d, batch_input_a, batch_input_b, nIn_a, nIn_b):
	# Func: To get the Phi according to r,d,batch_input_a,batch_input_b	

	ks = r
	ke = batch_input_a.shape[0]-d-1
	
	phi_a = np.zeros(((ke-ks+1), (d+r+1)*nIn_a))
	phi_b = np.zeros(((ke-ks+1), (d+r+1)*nIn_b))

	# print(batch_input_b.shape, phi_a.shape, phi_b.shape)
	
	for i in range(0, ke-ks+1):
		for j in range(0, d+r+1):
			phi_a[i, (j*nIn_a):((j+1)*nIn_a)] = batch_input_a[ks+d+i-j,:]
			phi_b[i, (j*nIn_b):((j+1)*nIn_b)] = batch_input_b[ks+d+i-j,:]

	return phi_a, phi_b, ks, ke


def chooseModel(phi_b, theta_b3d, y_batch_true_b, ks, ke):

	# Func: To choose model from the possible working conditions
	
	y_batch_pred_b = np.zeros([theta_b3d.shape[0], phi_b.shape[0], theta_b3d.shape[-1]])
	
	for i in range(theta_b3d.shape[-1]):
		# print(phi_b.shape, theta_b3d[:,:,i].shape)
		y_batch_pred_b[:,:,i] = np.matmul(phi_b, theta_b3d[:,:,i].T).T

	y_diff = np.square(y_batch_pred_b - y_batch_true_b[ks:ke+1, :])
	
	mse = y_diff.sum(axis = 1)
	
	mse = mse.sum(axis = 1)

	return mse.argmin(axis = 0)


def estimateOutput(phi_a, theta_a3d, model_index, mean_out, ks, ke):
	
	# Func: To estimate these interested outputs and write the numpy array to .txt files
	# Todo: Check whether np.set_printoptions works or not?

	theta = theta_a3d[model_index,:,:]

	# estimate here!

	y_batch_pred_a = np.dot(phi_a, theta) + mean_out

	return y_batch_pred_a


def getDataFromQueue(queue_matrix, p):
	
	mat_str = queue_matrix.get()
	batch_input = np.fromstring(mat_str, dtype=np.float64)
	batch_input = batch_input.reshape(p.step_time * p.freque, p.nAll_channel)
	return batch_input


def getCalculateFlag(batch_speed):

	calcu_flag = 0

	if batch_speed[0] > 0.1 or batch_speed[-1] > 0.1:
		calcu_flag = 1
		
	return calcu_flag


