#!/usr/bin/env python3
"""Plot the live microphone signal(s) with matplotlib.

Matplotlib and NumPy have to be installed.

"""
import json
import argparse
import Queue as queue
import sys
import requests
import datetime
#import predict #import Prediction
import numpy as np
import threading
import time as ti
from PyQt4 import QtGui
from task import task_enroll as do_enroll
from gui.utils import write_wav, read_wav
from gui.interface import ModelInterface
import soundfile as sf
from pygame import mixer
def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
NPDtype = 'int16'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-w', '--window', type=float, default=200, metavar='DURATION',
    help='visible time slot (default: %(default)s ms)')
parser.add_argument(
    '-i', '--interval', type=float, default=30,
    help='minimum time between plot updates (default: %(default)s ms)')
parser.add_argument(
    '-b', '--blocksize', type=int, help='block size (in samples)')
parser.add_argument(
    '-r', '--samplerate', type=float, help='sampling rate of audio device')
parser.add_argument(
    '-n', '--downsample', type=int, default=10, metavar='N',
    help='display every Nth sample (default: %(default)s)')
parser.add_argument(
    'channels', type=int, default=[1], nargs='*', metavar='CHANNEL',
    help='input channels to plot (default: the first)')
parser.add_argument(
    '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
args = parser.parse_args()
if any(c < 1 for c in args.channels):
    parser.error('argument CHANNEL: must be >= 1')
mapping = [c - 1 for c in args.channels]  # Channel numbers start with 1
q = queue.Queue()
onsetRecent = False
dataQueue = queue.Queue()
iteration = 1
recData = []
pause = False
check = False
threshold = 0.1
halfShowLength = 5000
app = QtGui.QApplication(sys.argv)
e = 0
fail = False
voiceMode = True
#time.sleep(5)
#playback = False

# colorDict = [
#     ('coughing', '#5db0ea'),
#     #('dog-bark', '#ffd785'),
#     #('door-bell', '#5cebb6'),
#     ('door-open', '#c2d0dc'),
#    # ('dyerMachine', '#dae2ea'),
#     #('fire-alarm', '#aa0000'),
#     ('flushing', '#ddaaff'),
#    # ('fondoSilencio', '#ff00b9'),
#     #('fondoTranquilo', '#00ff99'),
#     ('glassBroken', '#ff3c3d'),
#     ('knockingDoor', '#61a661'),
#     #('shower', '#dae2e1'),
#     #('stew', '#36648b'),
#    # ('toothBrushing', '#5d9377'),
#    # ('vacuum', '#daa520'),
#     #('washingDishes', '#f47069'),
#     #('washingMachine', '#98162a'),
#     ]
# colors = [
# '#5db0ea',
# '#c2d0dc',
# '#ddaaff',
# '#ff3c3d',
# '#61a661'
# ]
def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    global pause
    
    if pause:
        return
    if status:
        file = sys.stderr
        print(status, file)
    q.put(indata[ : , mapping])
    # dataQueue.put(indata.copy().flatten())
    # if dataQueue.qsize() > 40:#about 1.s
    #     data = []
    #     while dataQueue.empty() == False:
    #         data = np.concatenate((data, dataQueue.get()))
    #     recData = np.concatenate((recData, data))
    #     max = np.max(data)
    #     onset_frames = librosa.onset.onset_detect(y=data, sr=16000)
    #     e = len(onset_frames)
    #     if  e < 8 or max > 0.7:
    #         predict.wave = v
    #         predict.stop = datetime.datetime.now()
    #         predict.lock.release()

        # if len(onset_frames) < 4:
        #     if onsetRecent == False:
        #         onsetRecent = True
        #         predict.wave = data
        #         predict.startIndex = len(rawYData)
        #     else:
        #         predict.wave = np.concatenate((predict.wave, data))
        # elif onsetRecent == True:
        #     onsetRecent = False
        #     predict.wave = np.concatenate((predict.wave, data))
        #     predict.stop = datetime.datetime.now()
        #     predict.lock.release()

def sendData(link, data, timestart):
    global pause
    global voiceMode
    global fail
    global rawYData
    global e
    
    time = datetime.datetime.now()
    #print(time.strftime('%Y-%m-%d %H:%M:%S'))
    jsonData = {'wave': data.tolist(),
            'sr': 16000,
            'time_start': time.strftime('%Y-%m-%d %H:%M:%S'),
	    'user_id_id': 1}

    jsonData = json.dumps(jsonData, sort_keys=True)
    r = requests.post(url=link,data= jsonData)	
    print("The response is:%s" % r.text)
    trigger = json.loads(r.text)["Trigger"]
    labelsound = str(json.loads(r.text)["Labels"])
    #trigger = r.json()
    #trigger = trigger[0]['Trigger']
    print trigger
    if voiceMode and trigger == True:
        voiceMode = False
        pause = True
        print 'pause'
        model = ModelInterface.load("m.out")
        #fs,array = read_wav("start.mp3")
        #sd.play(array,fs)
        mixer.init(16000)
        mixer.music.load('start.mp3')
        mixer.music.play()
        ti.sleep(2)
        print "Recording Voice..."
        samplerate = 44100  # Hertz
        duration = 5 #8s
        predictData = sd.rec(int(samplerate * duration), samplerate=samplerate,
                channels=1, blocking = True)
        signal = np.array(predictData).flatten()
        #VAD filter
        
        #-------
        label = model.predict(samplerate, signal)
        if label == 'unknown':
            mixer.music.load('fail.mp3')
            mixer.music.play()
            ti.sleep(3)
            
            print "Recording Voice..."
            predictData = sd.rec(int(samplerate * duration), samplerate=samplerate,
                channels=1, blocking = True)
            signal = np.array(predictData).flatten()
            label1 = model.predict(samplerate, signal)
            #print label1
            if label1 == "unknown":
                fail = True
                mixer.music.load('fail.mp3')
                mixer.music.play()
                ti.sleep(3)
                notifyFailer(labelsound)
        if(fail == False):
            mixer.music.load('success.mp3')
            mixer.music.play()
            ti.sleep(30) 
        #predictData = np.asarray(predictData,dtype="float32")
        #write_wav("test.wav",samplerate,signal)
        #sf.write("test.wav", signal, samplerate)
        
        print "done"
        rawYData= []
        e = 0
        fail = False
        pause = False
        voiceMode = True
        
def notifyFailer(labelsound):
    time = datetime.datetime.now()
    time =time.strftime('%Y-%m-%d %H:%M:%S')
    requests.post(url="http://172.29.192.70:8000/noti/send?verify=0&labelsound="+labelsound+"&time_start=" +time, data = "")
    print "fail"

def update_plot(frame):
    """This is called by matplotlib for each plot update.

    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.
    """

    global iteration
    global rawYData
    global plotdata
    global check
    global e
    if pause == False:
        data =[]
        while True:
            try:
                data = q.get_nowait()
            except queue.Empty:
                break
        data = np.array(data)
        if data.size:
            ydata = data[:,0]
            # t = threading.Thread(target=sendData, args=[urlServer, ydata, 0])
            # t.daemon = True
            # t.start()
            rawYData = np.concatenate((rawYData, ydata))
            #print len(rawYData)
            if len(rawYData) >= 80000 * (e + 1):
           
                senddata = rawYData[e * 80000 : 80000 * (e + 1)]
                max = np.max(senddata)
                e += 1
                print max
                if max > 0.1:
                    print('send')
                    #senddata = np.multiply(senddata, (0.5/max))
                    t = threading.Thread(target=sendData, args=[urlServer, senddata, 0])
                    
                    t.daemon = True
                    t.start()
            # if len(rawYData) >= iteration * 16000:
            #     pre = iteration
            #     iteration += 1
            #     t = threading.Thread(target=sendData, args=[urlServer, ydata[pre * 16000 : iteration * 16000], 0])
            #     t.daemon = True
            #     t.start()


            #if rawYData.

    temp = (1 - (sliderVal / 100)) * len(rawYData)
    temp = int(temp)
    startInterval = temp - halfShowLength
    endInterval = temp + halfShowLength
    if endInterval > len(rawYData):
        endInterval = len(rawYData)
        startInterval = endInterval - 2 * halfShowLength
    if (startInterval < 0):
        startInterval = 0
    d = (endInterval - startInterval)
    plotdata[int(2 * halfShowLength - d):] = rawYData[int(startInterval): int(endInterval)]
    for column, line in enumerate(lines):
         line.set_ydata(plotdata[:])




    # if check:
    #     for e in barArray:
    #         e.remove()
    #     barArray.clear()
    #     for i in predict.items:
    #         if endInterval > i.xPos >= startInterval:
    #             for j in range (0, 5):
    #                 e = ax.bar(x=i.xPos - startInterval , height=i.percentage[j], width=i.width, bottom=-1 + i.bottom[j], align='center',
    #                            color=colors[j])
    #                 barArray.append(e)


def on_changed(val):
    global pause
    global sliderVal
    sliderVal = val
    pause = True
def unpause(e):
    global pause
    pause = False
    #sd.stop()
def pause(e):
	global pause
	pause = True
def playBack(e):
    global pause
    global recData
    if pause == False:
        pause = True
    if len(recData) > 4800000:
        playBackAudio = recData[(len(recData) - 4800000):]
    else:
        playBackAudio = recData
    sd.play(playBackAudio, 16000)
def checked(e):
    global check
    check = not check
def enroll (e):
    global pause
    pause = True
    do_enroll('./demotrain/*', 'm.out')
try:
    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    import sounddevice as sd
    import librosa
    from matplotlib.widgets import Slider, Button

    if args.list_devices:
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = 16000#device_info['default_samplerate']
    urlServer = 'http://172.29.192.70:8000/label/predict'
    startInterval = 0
    endInterval = 0
    rawYData = []
    xAxis = np.arange(2 * halfShowLength)
    plotdata = np.zeros(2 * halfShowLength)
    sliderVal = 0.5

    #length = 640#int(args.window * args.samplerate / (1000 * args.downsample))
    #print(length)
    #plotdata = np.zeros((length, len(args.channels)))
    #fig, ax = plt.subplots()
    #lines = ax.plot(plotdata)
    # if len(args.channels) > 1:
    #     ax.legend(['channel {}'.format(c) for c in args.channels],
    #               loc='lower left', ncol=len(args.channels))
    #
    #ax.set_yticks([0])
    #ax.yaxis.grid(True)
    #ax.tick_params(bottom='off', top='off', labelbottom='off',
    #               right='off', left='off', labelleft='off')
    #fig, ax = plt.subplots()
    #fig.tight_layout(pad=0)
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    lines = ax.plot(plotdata)
    ax.axis((0, 2 * halfShowLength, -1, 1))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom='off', top='off', labelbottom='off',
                   right='off', left='off', labelleft='off')
    plt.subplots_adjust(left=0.1, bottom=0.25)
    axcolor = 'lightgoldenrodyellow'
    axTime = plt.axes([0.25, 0.1, 0.65, 0.03])#, facecolor=axcolor)
    timeSlider = Slider(axTime, 'Time', 0, 100.0, valinit=sliderVal)
    timeSlider.on_changed(on_changed)

    playPos = plt.axes([0.2, 0.025, 0.1, 0.04])
    playButton = Button(playPos, 'Play', color=axcolor, hovercolor='0.975')
    playButton.on_clicked(unpause)
    enrollPos = plt.axes([0.5, 0.025, 0.1, 0.04])
    enrollButton = Button(enrollPos, 'Enroll', color=axcolor, hovercolor='0.975')
    enrollButton.on_clicked(enroll)
    # checkPos = plt.axes([0.5, 0.025, 0.1, 0.04])
    # checkButton = Button(checkPos, 'Check', color=axcolor, hovercolor='0.975')
    # checkButton.on_clicked(checked)
    # stopPos = plt.axes([0.8, 0.025, 0.1, 0.04])
    # stopButton = Button(stopPos, 'Stop', color=axcolor, hovercolor='0.975')
    # stopButton.on_clicked(playBack)
    stream = sd.InputStream(
        device=args.device, channels=max(args.channels),
        samplerate=args.samplerate, callback=audio_callback)
    ani = FuncAnimation(fig, update_plot, interval=args.interval)

    # patches = []
    # for i in colorDict:
    #     e = mpatches.Patch(color=i[1], label=i[0])
    #     patches.append(e)

    #fig2, ax2 = plt.subplots()
    #ax2.legend(handles=patches)
    with stream:
        plt.show()
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))




