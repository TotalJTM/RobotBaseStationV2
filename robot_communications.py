#JTM 2021
#socket robot command class
#used to format basic commands into dictionary objects to be sent over network socket

import json

class commands:
    #create dictionary objects with specified left and right motor values
    #return formatted dictionary objects in an array
    def motor(left_motor_val=None, right_motor_val=None):
        arr = []
        if left_motor_val is not None:
            arr.append({"left_speed": left_motor_val})
        if right_motor_val is not None:
            arr.append({"right_speed": right_motor_val})
        return arr

    #create an belt_drive message dictionary object
    #should be used change the belt drive direction
    def arm_drive(value):
        return [{"arm_drive": value}]

    #create an belt_drive message dictionary object
    #should be used change the belt drive direction
    def gripper_drive(value):
        return [{"grip_drive": value}]

    #create an "OK" message dictionary object
    #should be used as an acknowledgement
    def ok():
        return [{"OK": "OK"}]

    #create a "STOP" command
    #should be used to signify the end of a socket connection
    def stop():
        return [{"STOP":"STOP"}]

    #function to format an array of commands into a json field "arr"
    #and convert it to a byte string object
    #byte string object is returned
    def format_arr(pay_arr):
        msg = json.dumps({"arr":pay_arr})
        return bytes(msg+',', 'utf-8')