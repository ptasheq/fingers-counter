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
			#self._frame = x



class FingersCounter:
	def __init__(self, cap):
		cv2.namedWindow("Fingers Counter", cv2.CV_WINDOW_AUTOSIZE)
		cv.SetMouseCallback("Fingers Counter", mouseCallback)
		self._cap = cap
		self._clock = 0
		self._parts = 16

	def initCamera(self):
		self._fingers = [0, 0]
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
		frame = cv2.GaussianBlur(frame, (5,5), 0)
		self._firstFrame = FirstFrame(frame, 640, 480, self._parts) 
		self._lastAvgs = self._firstFrame.getAvgs()

	def run(self):
		self.initCamera()
		while self.display() < 0 and notClicked:
			continue

	def getCosAlpha(self, contours, step, i):
		vec1 = (contours[i-step][0][0]	- contours[i][0][0], contours[i-step][0][1] - contours[i][0][1])
		vec2 = (contours[i+step][0][0]	- contours[i][0][0], contours[i+step][0][1] - contours[i][0][1])
		return (vec1[0] * vec2[0] + vec1[1] * vec2[1]) / ((vec1[0] ** 2 + vec1[1] ** 2) * (vec2[0] ** 2 + vec2[1] ** 2)) ** 0.5

	def findStep(self, contours):
		length = len(contours)
		dists = []
		prevPoint = [0, 0]
		for step in (65, 85, 120):
			i = step - step + (length - 1) % step 
			while i < length-step:
				if contours[i-step][0][0] <= 3  or contours[i][0][0] <= 3 or contours[i+step][0][0] <= 3 or contours[i-step][0][1] <= 3 or contours [i][0][1] <= 3 or contours[i+step][0][1] <= 3 :
					i += 5
					continue
				if contours[i-step][0][0] >= 637  or contours[i][0][0] >= 637 or contours[i+step][0][0] >= 637 or contours[i-step][0][1] >= 477 or contours [i][0][1] >= 477 or contours[i+step][0][1] >= 477 :
					i += 5
					continue

				cosAlpha = self.getCosAlpha(contours, step, i)

				if (cosAlpha >= 0.4):
					if prevPoint != [0, 0]:
						prevPoint = [contours[i][0][0], contours[i][0][1]]
					else:
						dists.append((prevPoint[0] - contours[i][0][0]) ** 2 + (prevPoint[1] - contours[i][0][1]) ** 2)
						break
				i += 5	

		if dists != []:
			return int(min(dists) ** 0.5 / 2)
		return 65

	def doCounting(self, contours, img, step, thresh, b):
		length = len(contours)
		fingers = 0
		i = step - step + (length - 1) % step 

		while i < length-step:

			if contours[i-step][0][0] <= 3  or contours[i][0][0] <= 3 or contours[i+step][0][0] <= 3 or contours[i-step][0][1] <= 3 or contours [i][0][1] <= 3 or contours[i+step][0][1] <= 3 :
				i += 5
				continue
			if contours[i-step][0][0] >= 637  or contours[i][0][0] >= 637 or contours[i+step][0][0] >= 637 or contours[i-step][0][1] >= 477 or contours [i][0][1] >= 477 or contours[i+step][0][1] >= 477 :
				i += 5
				continue

			cosAlpha = self.getCosAlpha(contours, step, i)

			if (cosAlpha >= 0.4):			
				# we have to check if we have finger of valley beetwen them
				insideX = (contours[i-step][0][0] + contours[i+step][0][0]) / 2
				insideY = (contours[i-step][0][1] + contours[i+step][0][1]) / 2
				if img[insideY][insideX] == thresh:
					cv2.circle(b, (contours[i][0][0], contours[i][0][1]), 5, 255)
					fingers += 1
					i += int(2 * step)
				else:
					i += 5
			i += 1

		self._fingers[0] += fingers;
		#print('fingers' + str(fingers))

	def display(self):
		
		retval, frame = cap.read()
		frame = cv2.cvtColor(frame, cv.CV_RGB2GRAY)	
		frame = cv2.GaussianBlur(frame, (5,5), 0)

		img = cv2.absdiff(frame, self._firstFrame.getImg())

		if time.clock() - self._clock > 0.2:
			self._clock = time.clock()
			self._lastAvgs, val = getBrightnessChange(self._lastAvgs,
			                                          frame, self._parts)
			self._firstFrame.adjustBrightness(val)

		retval, thresh = cv2.threshold(img, 30, 205, cv2.THRESH_BINARY)

		#deep copy of thresh
		tmp = np.empty_like(thresh)
		np.copyto(tmp, thresh)

		b = np.zeros_like(thresh)
		contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
		# looking for max 2 largest shapes 
		largestArea, largestContours = [0, 0], [0, 0]
		if hierarchy != None:
			for el in contours:
				area = abs(cv2.contourArea(el))
				if (area > largestArea[0]):
					largestArea[1] = largestArea[0]
					largestArea[0] = area	
					largestContours[1] = largestContours[0]
					largestContours[0] = el
				elif (area > largestArea[1]):
					largestArea[1] = area
					largestContours[1] = el	
			for area, contour in zip(largestArea, largestContours):
				if area > 5000:
					cv2.drawContours(b, contour,-1,255,3)

					self.doCounting(contour, tmp, self.findStep(contour), 205, b)
			self._fingers[1] += 1
		if self._fingers[1] >= 10:
			print('You showed up ' + str(int(self._fingers[0] / self._fingers[1])) + ' fingers')
			self._fingers = [0, 0]
		cv2.imshow("Fingers Counter", b)
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
