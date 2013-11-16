import cv2, cv
import numpy as np
import time

class FingersCounter:
	def __init__(self, cap):
		cv2.namedWindow("Fingers Counter", cv2.CV_WINDOW_AUTOSIZE)
		cv.SetMouseCallback("Fingers Counter", mouseCallback)
		self._cap = cap

	def run(self):
		while self.display() < 0 and notClicked:
			continue

	def display(self):
		retval, frame = cap.read()
		try:
			cv2.imshow("Fingers Counter", frame)
		except Exception, e:
			print("Known library error happened - continue")
			time.sleep(3)

		return cv2.waitKey(30)

def mouseCallback(event, x, y, a, b):
	global notClicked
	print('ok')
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