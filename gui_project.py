import sys
import numpy as np
from PyQt4 import QtGui
from gui_enroll import EnrollGui
import pyaudio

class Gui(QtGui.QMainWindow):
	def __init__(self):
		super(Gui,self).__init__()
		self.setWindowTitle("Bla bla bla")
		self.resize(500,300)
	#	self.guidesign()
	#def guidesign(self):
	#	enrollbtn = QtGui.QPushButton("Enroll",self)
	#	enrollbtn.move(100,200)
	#	enrollbtn.clicked.connect(self.enroll)
	#	soundeventbtn =QtGui.QPushButton("Sound Event Detection",self)
	#	soundeventbtn.resize(soundeventbtn.minimumSizeHint())
	#	soundeventbtn.move(300,200)
	#	self.show()
	def enroll(self):
		self.dialog = EnrollGui()
		self.close()
		self = self.dialog
		self.show()
	#def soundevent(self):
	
#if __name__ == "__main__":
#	app = QtGui.QApplication(sys.argv)
#	GUI = Gui()
#	sys.exit(app.exec_())
	
