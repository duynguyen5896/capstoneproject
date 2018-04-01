import os
from task import task_enroll as enroll
#def save_wavfile():

#def pre_enroll(username):
#	directory = './enrolldata/' + username + '/';
#	try:
#		os.makedirs(directory)
#	except OSError as e:
#   		if e.errno != errno.EEXIST:
#        		raise
	
if __name__ == '__main__':
	
	enroll('./enrolldata/*', 'm.out')
