#https://inputs.readthedocs.io/en/latest/user/quickstart.html
from inputs import devices, get_gamepad
from math import pi, cos

from _thread import *
import threading

#Button codes for a logitech gamepad
#Trigger buttons: BTN_TL, BTN_TR, ABS_Z, ABS_RZ
#Gamepad buttons: BTN_WEST, BTN_NORTH, BTN_SOUTH, BTN_EAST
#Select/start 	: BTN_SELECT, BTN_START
#Joy Pad 		: ABS_HAT0X, ABS_HAT0Y
#Joysticks		: ABS_X, ABS_Y, ABS_RX, ABS_RY

class joy_device():
	def __init__(self, device):
		self.joystick_max_val = 32767
		self.speed_limit = 10
		self.deadzone = 10
		self.gamepad_queue = []
		self.device_id = device.manager
		self.gamepad_thread = None
		self.gamepad_thread_active = False

	def queue_gamepad_input(self):
		while self.gamepad_thread_active:
			new_input = self.get_gamepad_input()
			for item in new_input:
				self.gamepad_queue.append(item)
		else:
			print("gamepad thread stopped")

	def get_gamepad_input(self):
		list_events = []
		events = get_gamepad()
		for event in events:
			if event.device.manager == self.device_id:
				list_events.append({"event":event.code,"value":event.state})
		return list_events

	def start_gamepad_thread(self):
		self.gamepad_thread_active = True
		self.gamepad_thread = threading.Thread(target=self.queue_gamepad_input)
		self.gamepad_thread.daemon = True
		self.gamepad_thread.start()

	def stop_gamepad_thread(self):
		self.gamepad_thread_active = False
		self.gamepad_thread = None

	def pop_gamepad_queue(self):
		local_queue = self.gamepad_queue
		self.gamepad_queue = []
		return local_queue

	def normalize_joy(self, val):
	    #NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
	    newval = (((val+self.joystick_max_val)*(self.speed_limit*2))/(2*self.joystick_max_val))-self.speed_limit
	    #print(newval)
	    if -2 < newval < 2:
	        return 0
	    else:
	        return newval

	#https://home.kendra.com/mauser/joystick.html

	def mix_joy(self, xval, yval):
	    newx = (((xval+self.joystick_max_val)*(100*2))/(2*self.joystick_max_val))-100
	    newy = (((yval+self.joystick_max_val)*(100*2))/(2*self.joystick_max_val))-100

	    if -self.deadzone < newx < self.deadzone:
	        newx = 0
	    if -self.deadzone < newy < self.deadzone:
	        newy = 0

	    newx = -1 * newx
	    V = (100-abs(newx))*(newy/100)+newy
	    W = (100-abs(newy))*(newx/100)+newx
	    left = ((V-W)/2)/100
	    right = ((V+W)/2)/100
	    #print(f'l: {left} ||| r: {right}')
	    left = self.speed_limit * left
	    right = self.speed_limit * right #((newy*limit)/100)

	    return left, right

	def stop_thread(self):
		self.gamepad_thread_active = False