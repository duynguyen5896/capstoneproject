import sys
import shutil
import os
import glob
import traceback
import time
import numpy as np
from PyQt4 import uic
from scipy.io import wavfile
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore,QtGui

import pyaudio
from gui.utils import read_wav, write_wav, time_str, monophonic
from gui.interface import ModelInterface
from task import task_enroll as enroll

FORMAT=pyaudio.paInt16
NPDtype = 'int16'
class RecorderThread(QThread):
    def __init__(self, main):
        QThread.__init__(self)
        self.main = main

    def run(self):
        self.start_time = time.time()
        while True:
            data = self.main.stream.read(1)
            i = ord(data[0]) + 256 * ord(data[1])
            if i > 32768:
                i -= 65536
            stop = self.main.add_record_data(i)
            if stop:
                break

class EnrollGui(QtGui.QMainWindow):
    FS = 8000
    def __init__(self):
        super(EnrollGui,self).__init__()
        self.setWindowTitle("Enroll")
        self.resize(500,300)
        self.statusBar()
        self.guidesign()
    def guidesign(self):
        self.usernameTextBox = QLineEdit(self)
        self.usernameTextBox.setAlignment(Qt.AlignRight)
        self.usernameTextBox.move(200,100)
        self.usernameTextBox.setPlaceholderText("Enter Username .... ")
        self.startbtn  = QtGui.QPushButton("Recording", self)
        self.startbtn.setFocus()
        self.stopbtn = QtGui.QPushButton("Stop", self)
        self.enrollbtn = QtGui.QPushButton("Enroll", self)
        self.enrollbtn.clicked.connect(self.do_enroll)
        self.startbtn.clicked.connect(self.start_enroll_record)
        self.stopbtn.clicked.connect(self.stop_enroll_record)
        self.startbtn.move(50,200)
        self.stopbtn.move(200,200)
        self.enrollbtn.move(350,200)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_callback)
    def timer_callback(self):
		self.record_time += 1
		self.status("Recording..." + time_str(self.record_time))
		self.update_all_timer()
    def start_enroll_record(self):
		self.enrollWav = None
		self.start_record()
    def stop_enroll_record(self):
		self.stop_record()
		print self.recordData[:300]
		signal = np.array(self.recordData, dtype=NPDtype)
		self.enrollWav = (EnrollGui.FS, signal)
		# TODO To Delete
		filename = self.usernameTextBox.text()
		path = "\\enrolldata\\" + filename + '\\'
		path = os.getcwd() + path
		print path
		os.mkdir(path, 0755)
		write_wav(path + 'enroll.wav', *self.enrollWav)
    def start_record(self):
		self.pyaudio = pyaudio.PyAudio()
		self.status("Recording...")

		self.recordData = []
		self.stream = self.pyaudio.open(format=FORMAT, channels=1, rate=EnrollGui.FS,
		                input=True, frames_per_buffer=1)
		self.stopped = False
		self.reco_th = RecorderThread(self)
		self.reco_th.start()

		self.timer.start(1000)
		self.record_time = 0
		self.update_all_timer()

    def status(self, s=""):
        	self.statusBar().showMessage(s)

    def update_all_timer(self):
		s = time_str(self.record_time)
    def add_record_data(self, i):
			self.recordData.append(i)
			return self.stopped
    def stop_record(self):
		self.stopped = True
		self.reco_th.wait()
		self.timer.stop()
		self.stream.stop_stream()
		self.stream.close()
		self.pyaudio.terminate()
		self.status("Record stopped")
    def do_enroll(self):	
		enroll('./enrolldata/*', 'm.out')