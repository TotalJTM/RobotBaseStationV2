from controller import joy_device
#from robot_communications import commands
from network import Network_Sock
from inputs import devices
from timer import Timer
import time, json

host_ip = '192.168.1.5'
server_port = 12345

class MBlock_UltiTank_GSO:	#Makeblock Ultimate 2.0 Ground Station Object

	class commands:
	    #create dictionary objects with specified left and right motor values
	    #return formatted dictionary objects in an array
	    def motor(left_motor_val=None, right_motor_val=None):
	        if left_motor_val is not None:
	            return {"left": left_motor_val}
	        if right_motor_val is not None:
	            return {"right": right_motor_val}

	    #create an belt_drive message dictionary object
	    #should be used change the belt drive direction
	    def arm_drive(value):
	        return {"arm": value}

	    #create an belt_drive message dictionary object
	    #should be used change the belt drive direction
	    def gripper_drive(value):
	        return {"grip": value}

	    #create an "OK" message dictionary object
	    #should be used as an acknowledgement
	    def ok():
	        return {"OK": "OK"}

	    #create a "STOP" command
	    #should be used to signify the end of a socket connection
	    def stop():
	        return {"STOP":"STOP"}

	    #function to format an array of commands into a json field "arr"
	    #and convert it to a byte string object
	    #byte string object is returned
	    def format_arr(pay_arr):
	        msg = json.dumps({"arr":pay_arr})
	        return bytes(msg, 'utf-8')


	def __init__(self):
		self.joystick_max_val = 32767
		self.speed_limit = 100
		self.deadzone = 8
		self.joy_type = 'MIX'
		#self.joy_type = 'TANK'

		#Button codes for a logitech gamepad
		#Trigger buttons: BTN_TL, BTN_TR, ABS_Z, ABS_RZ
		#Gamepad buttons: BTN_WEST, BTN_NORTH, BTN_SOUTH, BTN_EAST
		#Select/start 	: BTN_SELECT, BTN_START
		#Joy Pad 		: ABS_HAT0X, ABS_HAT0Y
		#Joysticks		: ABS_X, ABS_Y, ABS_RX, ABS_RY
		if self.joy_type == 'MIX':
			self.left_drive_stick = 'ABS_RX'
			self.right_drive_stick = 'ABS_RY'
		if self.joy_type == 'TANK':
			self.left_drive_stick = 'ABS_Y'
			self.right_drive_stick = 'ABS_RY'
		self.gripper_open_btn = 'BTN_TR'
		self.gripper_close_btn = 'BTN_TL'
		self.arm_up_down_btn = 'ABS_HAT0Y'

		self.left_drive_stick_val = 0
		self.right_drive_stick_val = 0
		self.gripper_open_btn_val = 0
		self.gripper_close_btn_val = 0
		self.arm_up_down_btn_val = 0
		
		self.left_drive_state = 0
		self.right_drive_state = 0
		self.gripper_state = 0
		self.arm_state = 0

		self.arm_state_tick_interval = 0.025
		self.arm_tick_timer = Timer(self.arm_state_tick_interval)
		self.arm_tick_timer.start()

	def normalize_joy(self, val):
	    #NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
	    newval = (((val+self.joystick_max_val)*(self.speed_limit*2))/(2*self.joystick_max_val))-self.speed_limit
	    #print(newval)
	    if -self.deadzone < newval < self.deadzone:
	        return 0
	    else:
	        return newval

	#function to generate JSON message from new controller input
	#takes an array of controller values, returns an empty arr (if no new string necessary) or a formatted string
	#that can be sent to the robot
	def update_raw_vals_from_controller_input(self, new_button_vals):

		#move through the new button values
		for event in new_button_vals:

			if event["event"] == self.left_drive_stick:
				self.left_drive_stick_val = int(event["value"])

			if event["event"] == self.right_drive_stick:
				self.right_drive_stick_val = int(event["value"])

			if event["event"] == self.gripper_open_btn:
				self.gripper_open_btn_val = event["value"]

			if event["event"] == self.gripper_close_btn:
				self.gripper_close_btn_val = event["value"]

			if event["event"] == self.arm_up_down_btn:
				if event["value"] == 0:
					self.arm_up_down_btn_val = 0
				if event["value"] == 1:
					self.arm_up_down_btn_val = 1
				if event["value"] == -1:
					self.arm_up_down_btn_val = -1


	def generate_states_from_raws(self):
		if self.joy_type == 'TANK':
			self.left_drive_state = self.normalize_joy(self.left_drive_stick_val)
			self.right_drive_state = self.normalize_joy(self.right_drive_stick_val)

		if self.joy_type == 'MIX':
		    newx = (((self.left_drive_stick_val+self.joystick_max_val)*(100*2))/(2*self.joystick_max_val))-100
		    newy = (((self.right_drive_stick_val+self.joystick_max_val)*(100*2))/(2*self.joystick_max_val))-100

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
		    self.left_drive_state = self.speed_limit * left
		    self.right_drive_state = self.speed_limit * right #((newy*limit)/100)

		#invert button states, up is negative and down is pos normally
		if self.arm_up_down_btn_val == 1:
			if self.arm_tick_timer.expired():
				if self.arm_state > 0:
					self.arm_state -= 1
					self.arm_tick_timer.start()
		elif self.arm_up_down_btn_val == -1:
			if self.arm_tick_timer.expired():
				if self.arm_state < 90:
					self.arm_state += 1
					self.arm_tick_timer.start()
		else:
			pass

		grip_mask = self.gripper_close_btn_val<<1|self.gripper_open_btn_val
		if grip_mask == 1:
			self.gripper_state = 75
		elif grip_mask == 2:
			self.gripper_state = -75
		else:
			self.gripper_state = 0


	def generate_json_from_states(self):
		pay_pack = []

		pay_pack.append(self.commands.motor(left_motor_val=self.left_drive_state))
		pay_pack.append(self.commands.motor(right_motor_val=self.right_drive_state))
		pay_pack.append(self.commands.arm_drive(self.arm_state))
		pay_pack.append(self.commands.gripper_drive(self.gripper_state))

		return pay_pack


if __name__ == "__main__":
	try:
		s = Network_Sock()
		s.bind(host=host_ip, port=server_port)

		print(f'Connected to {host_ip}')
	except:
		print(f'Could not connect to {host_ip}')

	cmd_line_timer = Timer(0.25)
	cmd_line_timer.start()
	try:
		joy = joy_device(devices.gamepads[0])
		joy.start_gamepad_thread()
	except:
		print("No gamepads connected")

	mb_tank = MBlock_UltiTank_GSO()

	try:

		while s.sock != None:

			events = joy.pop_gamepad_queue()
			#print(len(events))
			#print(events)

			mb_tank.update_raw_vals_from_controller_input(events)
			mb_tank.generate_states_from_raws()
			pay_pack = mb_tank.generate_json_from_states()
			#print(pay_pack)
			#if len(pay_pack) > 0:
				#print(commands.format_arr(pay_pack))
			s.send(mb_tank.commands.format_arr(pay_pack))

			time.sleep(.001)

			if cmd_line_timer.expired():
				print(f'Speed L:{mb_tank.left_drive_state} R:{mb_tank.right_drive_state}, Gripper: {mb_tank.gripper_state}, Arm: {mb_tank.arm_state}')
				cmd_line_timer.start()


	except:  # this never happens KeyboardInterrupt
		print("Script aborted")
		joy.stop_thread()
		print("joy stopped")
		abcd_1234()
		s.send(mb_tank.commands.format_arr(commands.stop()))
		print("socket sent")
		s.close()
		print("socket close")
		
		#sys.exit(0)
		terminate()
		print("reached end")
		abcd_1234()