import os

def mnchdir(path):
	if(os.path.isfile(path)):
		os.remove(path) # What if its in use??
	if(not os.path.exists(path)):
		os.mkdir(path)
	os.chdir(path)