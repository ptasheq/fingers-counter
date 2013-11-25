from __future__ import division
import cv2, cv
import numpy as np
import time

def getBrightness(frame, n):
	tmp = np.vsplit(frame, n**0.5)
	tmp2 = []
	for j in [np.hsplit(i, n**0.5) for i in tmp]:
		for k in j:
			tmp2.append(np.average(k))
	return tmp2

class FirstFrame:
	def __init__(self, frame, w, h):
		self._width, self._height = w, h
		self._frame = frame	
		self._avgs = getBrightness(frame, 16)

	def getImg(self):
		return self._frame

	def getAvgs(self):
		return self._avgs


class FingersCounter:
	def __init__(self, cap):
		cv2.namedWindow("Fingers Counter", cv2.CV_WINDOW_AUTOSIZE)
		cv.SetMouseCallback("Fingers Counter", mouseCallback)
		self._cap = cap
		self._clock = 0;

	def initCamera(self):
		cameraReady = False
		retval, frame = cap.read()
		avg = np.average(frame)	
		while cameraReady == False:
			try:
				cv2.imshow("Fingers Counter", frame)
				if (avg != np.average(frame)):
					cameraReady = True
			except Exception, e:
				print("Known library error happened - continue")
				time.sleep(3)
			try:
				avg = np.average(frame)	
			except Exception, e:
				time.sleep(3)
			retval, frame = cap.read()

		frame = cv2.cvtColor(frame, cv.CV_RGB2GRAY)	
		self._firstFrame = FirstFrame(frame, 640, 480) 
		self._lastAvgs = self._firstFrame.getAvgs()

	def run(self):
		self.initCamera()
		while self.display() < 0 and notClicked:
			continue

	def display(self):
		retval, frame = cap.read()
		frame = cv2.cvtColor(frame, cv.CV_RGB2GRAY)	

		img = cv2.absdiff(frame, self._firstFrame.getImg())

		retval, thresh = cv2.threshold(img, 30, 100, cv2.THRESH_BINARY)
		if time.clock() - self._clock > 0.25:
			self._clock = time.clock()
			tmp = getBrightness(frame, 16) 
			'''for x, y in zip(tmp, self._lastAvgs):
				TODO: insert here brightness calibration'''
			self._lastAvgs = tmp
		cv2.imshow("Fingers Counter", thresh)
		return cv2.waitKey(30)

def mouseCallback(event, x, y, a, b):
	global notClicked
	if (notClicked):
		notClicked = (event != cv2.EVENT_LBUTTONUP) 

if __name__ == '__main__':
	global notClicked	
	notClicked = True
	cap = cv2.VideoCapture(0)
	cap.set(cv.CV_CAP_PROP_FRAME_WIDTH, 640)
	cap.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
	fc = FingersCounter(cap)
	fc.run()
	cap.release()
	del cap