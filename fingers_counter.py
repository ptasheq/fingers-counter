from __future__ import division
import cv2, cv 
import numpy as np
from math import ceil
import time

def getBrightness(frame, n):
	tmp = np.vsplit(frame, n**0.5)
	tmp2 = []
	for j in [np.hsplit(i, n**0.5) for i in tmp]:
		for k in j:
			tmp2.append(np.average(k))
	return tmp2

def getBrightnessChange(lastFrameAvgs, newFrame, parts):
	newFrameAvgs = getBrightness(newFrame, parts) 

	# a is number of brightened rectangles, b is number of darkened rectangles
	a, b = 0,0; minxy, minyx = 1000, 1000
	for x, y in zip(newFrameAvgs, lastFrameAvgs):
		if x > y + 3: #x > 1.04*y:
			a += 1
			if minxy > x - y:
				minxy = x - y
		elif x + 3 < y: #1.04*x < y:
			b += 1
			if minyx > y - x:
				minyx = y - x
	val = 0

	#if we image is generally brightened we want to brighten first frame also
	if a > parts / 2: 
		val = ceil(1.2*minxy)
	elif b > parts / 2:
		val = -ceil(1.2*minyx)

	return newFrameAvgs, int(val)

class FirstFrame:
	def __init__(self, frame, w, h, parts):
		self._width, self._height = w, h
		self._frame = frame	
		self._avgs = getBrightness(frame, parts)

	def getImg(self):
		return self._frame

	def getAvgs(self):
		return self._avgs

	def adjustBrightness(self, val):
		if val != 0:
			print(val)
			print(time.clock())
			x = np.add(self._frame, val).astype(np.uint8)

			# we substract - some values will go thorugh 0
			if val < 0: 
				#divide works like floor() we get zero when cell is less than val, one otherwise
				y = np.array(np.divide(self._frame, abs(val)), np.bool) 
				self._frame = np.multiply(x, y).astype(np.uint8)
				
			# we add - some values will go through 255
			else:
				y = np.array(np.divide(x, val), np.bool)
				#we have to first set to zero, then add inverted because we will set bad cells at 255 
				self._frame = np.add(np.multiply(x, y), np.add(y, 255)).astype(np.uint8)

			print(time.clock())
			#self._frame = x



class FingersCounter:
	def __init__(self, cap):
		cv2.namedWindow("Fingers Counter", cv2.CV_WINDOW_AUTOSIZE)
		cv.SetMouseCallback("Fingers Counter", mouseCallback)
		self._cap = cap
		self._clock = 0
		self._parts = 16

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
		self._firstFrame = FirstFrame(frame, 640, 480, self._parts) 
		self._lastAvgs = self._firstFrame.getAvgs()

	def run(self):
		self.initCamera()
		while self.display() < 0 and notClicked:
			continue

	def display(self):
		retval, frame = cap.read()
		frame = cv2.cvtColor(frame, cv.CV_RGB2GRAY)	

		img = cv2.absdiff(frame, self._firstFrame.getImg())

		if time.clock() - self._clock > 0.2:
			self._clock = time.clock()
			self._lastAvgs, val = getBrightnessChange(self._lastAvgs,
			                                          frame, self._parts)
			self._firstFrame.adjustBrightness(val)

		retval, thresh = cv2.threshold(img, 30, 100, cv2.THRESH_BINARY)
		thresh = cv2.GaussianBlur(thresh, (5,5), 0)
		contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
		for el in contours:
			cv2.drawContours(thresh,[el],-1,255,2)        
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
