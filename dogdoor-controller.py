import time
import board
from digitalio import DigitalInOut, Direction
import RPi.GPIO as GPIO

#door position switches
pad0_pin = board.D13
pad1_pin = board.D6
pad2_pin = board.D5
pad0 = DigitalInOut(pad0_pin)
pad1 = DigitalInOut(pad1_pin)
pad2 = DigitalInOut(pad2_pin)
pad0.direction = Direction.INPUT
pad1.direction = Direction.INPUT
pad2.direction = Direction.INPUT


#inside/outside switches
inside_sw = board.D12
outside_sw = board.D16
inside = DigitalInOut(inside_sw)
outside = DigitalInOut(outside_sw)
inside.direction = Direction.INPUT
outside.direction = Direction.INPUT
inside_already_pressed = True
outside_already_pressed = True

# set the motor output pins
MotorPin1   = 23    # pin36
MotorPin2   = 24    # pin35
MotorEnable = 25    # pin32
GPIO.setmode(GPIO.BCM)          # Numbers GPIOs by BCM
GPIO.setup(MotorPin1, GPIO.OUT)   # mode --- output
GPIO.setup(MotorPin2, GPIO.OUT)
GPIO.setup(MotorEnable, GPIO.OUT)
GPIO.output(MotorEnable, GPIO.LOW) # motor stop

pwm = GPIO.PWM(MotorEnable, 5)
pwm.ChangeDutyCycle(1)


def activateMotor():
    print('Raising the dog door...')      
    GPIO.output(MotorPin1, GPIO.HIGH)  # clockwise
    GPIO.output(MotorPin2, GPIO.LOW)
    GPIO.output(MotorEnable, GPIO.HIGH) # motor driver enable    
    motorActive = True
    pad0_already_pressed = True
    pad1_already_pressed = True
    pad2_already_pressed = True
    
    while motorActive:
        
        if pad0.value and not pad0_already_pressed:
            print("Pad 0 pressed stopping motor")
            pwm.ChangeDutyCycle(1)
            print("Go Outside Sal.mp3")
            time.sleep(3)
            print("You Snooze You Lose.jpg")
            pwm.ChangeDutyCycle(1)
            time.sleep(4)
            print("You Snooze You Lose 2.jpg")
            GPIO.output(MotorPin1, GPIO.LOW)   # counter-clockwise
            GPIO.output(MotorPin2, GPIO.LOW)
            GPIO.output(MotorEnable, GPIO.HIGH) # motor driver enable        
        pad0_already_pressed = pad0.value
     
        if pad1.value and not pad1_already_pressed:
            print("Pad 1 pressed - 50 pwm")
            pwm.ChangeDutyCycle(50)
        pad1_already_pressed = pad1.value
     
        if pad2.value and not pad2_already_pressed:
            print("Pad 2 pressed")
            print("stopping motor")
            GPIO.output(MotorEnable, GPIO.LOW) # motor stop
            motorActive = False
        pad2_already_pressed = pad2.value
            
        
        time.sleep(0.1)

    print("activateMotor() finished")
    
def emailImage():
    print("emailing image")
    time.sleep(1)
    print("image emailed")
    
def imageCapture():
    print("capturing image")
    time.sleep(0.5)
    print("image captured")
    emailImage()
    
    
while True:
 
    if inside.value and not inside_already_pressed:
        print("Pad 3 dog door triggered from inside")
        activateMotor()
    inside_already_pressed = inside.value
    
    if outside.value and not outside_already_pressed:
        print("Pad 4 dog door triggered from outside")
        activateMotor()
        imageCapture()
    outside_already_pressed = outside.value
    
    time.sleep(0.1)

print("exiting for some reason")
