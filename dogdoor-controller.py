import time
import board
from digitalio import DigitalInOut, Direction
import RPi.GPIO as GPIO
from multiprocessing import Pool
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import logging

webcam_devname = '/dev/video0'

logger = logging.getLogger('dog_door')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/home/pi/Python/logs/dog_door.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


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

pad0_already_pressed = True
pad1_already_pressed = True
pad2_already_pressed = True

#in case door is open upon startup
if not pad2.value and not pad2_already_pressed:
    print("Pad 2 pressed on application startup")
    logger.info("Pad 2 pressed on application startup")
    print("lowering door")
    logger.info("lowering door")
    GPIO.output(MotorPin1, GPIO.LOW)   # counter-clockwise
    GPIO.output(MotorPin2, GPIO.LOW)
    GPIO.output(MotorEnable, GPIO.HIGH) # motor driver enable
    motorActive = True
    while motorActive:
        if pad2.value:
            print("Pad 2 pressed")
            logger.info("Pad 2 pressed - Stopping motor")
            GPIO.output(MotorEnable, GPIO.LOW) # motor stop
            motorActive = False
        pad2_already_pressed = pad2.value
        time.sleep(0.1)
    print("door has been lowered on startup")
    logger.info("door has been lowered on startup")
pad2_already_pressed = pad2.value


def activateMotor():
    print('Raising the dog door...')
    logger.info("Raising the dog door")
    GPIO.output(MotorPin1, GPIO.HIGH)  # clockwise
    GPIO.output(MotorPin2, GPIO.LOW)
    GPIO.output(MotorEnable, GPIO.HIGH) # motor driver enable
    motorActive = True

    print("activateMotor() finished")
    logger.info("activateMotor() finished")
    pad0_already_pressed = True
    pad1_already_pressed = True
    pad2_already_pressed = True

    while motorActive:

        if pad0.value and not pad0_already_pressed:
            print("Pad 0 pressed stopping motor")
            logger.info("Pad 0 pressed stopping motor - sleeping 10 seconds")
            pwm.ChangeDutyCycle(1)
            time.sleep(10)
            GPIO.output(MotorPin1, GPIO.LOW)   # counter-clockwise
            GPIO.output(MotorPin2, GPIO.LOW)
            GPIO.output(MotorEnable, GPIO.HIGH) # motor driver enable
        pad0_already_pressed = pad0.value

        if pad1.value and not pad1_already_pressed:
            print("Pad 1 pressed - 50 pwm")
            logger.info("Pad 1 pressed - set duty cycle to 50")
            pwm.ChangeDutyCycle(50)
        pad1_already_pressed = pad1.value

        if pad2.value and not pad2_already_pressed:
            print("Pad 2 pressed")
            logger.info("Pad 2 pressed - stopping motor")
            GPIO.output(MotorEnable, GPIO.LOW) # motor stop
            motorActive = False
        pad2_already_pressed = pad2.value


        time.sleep(0.1)

    print("activateMotor() finished")
    logger.info("activateMotor() finished")


def emailImage(abs_file_path, currentdate, rel_path):

    print("emailing image")
    logger.info("emailing image")
    # Define these once; use them twice!
    strFrom = 'fdsa@gmail.com'
    strTo = 'asdf@gmail.com'

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = 'Dog door triggered from outside at: '+currentdate
    msgRoot['From'] = strFrom
    msgRoot['To'] = strTo
    msgRoot.preamble = 'This is a multi-part message in MIME format.'
    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)
    msgText = MIMEText('Salvador is a good boy! Hopefully, this is an image of a dog and not a person')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText('<b>DOG NAME HERE <i>is</i> a good boy!</b> Hopefully, this is an image of a dog and not a person else<br><img src="cid:image1"><br>', 'html')
    msgAlternative.attach(msgText)
    # This example assumes the image is in the current directory
    fp = open(abs_file_path, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgImage.add_header('Content-Disposition', 'attachment', filename=rel_path)
    msgRoot.attach(msgImage)
    # Send the email (this example assumes SMTP authentication is required)
    # define smtp server domain and port number.
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465
    smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
    smtp.ehlo()
    smtp.login('fdsa@gmail.com', 'asdffdsa')
    smtp.sendmail(strFrom, strTo, msgRoot.as_string())
    smtp.quit()
    print("IMAGE HAS BEEN EMAILED")
    logger.info("IMAGE HAS BEEN EMAILED")

def imageCapture():
    print("capturing image")
    logger.info("capturing image")
    image = "/tmp/%H%M%S.jpg"
    # read the absolute path
    script_dir = os.path.dirname(__file__)
    #get the date and time, set the date and time as a filename.
    currentdate = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    # create the real path
    rel_path = currentdate +".jpg"
    #  join the absolute path and created file name
    abs_file_path = os.path.join(script_dir, rel_path)
    os.system('fswebcam -r 800x600 --fps 60 -F 30 --device '+webcam_devname+' --no-banner --jpeg 95 --save '+abs_file_path+' > /dev/null 2>&1')
    print("image captured")
    logger.info("image captured:" + abs_file_path + " - sending image via email asynchronously")
    print(abs_file_path)
    print("sending image async")
    #pool2 = Pool(processes=1)
    #pool2.apply_async(emailImage, [abs_file_path], [currentdate], [rel_path])
    emailImage(abs_file_path, currentdate, rel_path)



while True:

    if inside.value and not inside_already_pressed:
        print("dog door triggered from inside")
        logger.info("Dog door triggered from the inside")
        activateMotor()
    inside_already_pressed = inside.value

    if outside.value and not outside_already_pressed:
        print("dog door triggered from outside")
        logger.info("Dog door triggered from the outside")
        pool = Pool(processes=4)
        pool.apply_async(imageCapture)
        activateMotor()
    outside_already_pressed = outside.value

    time.sleep(0.1)

print("exiting for some reason")
logger.info("Exited")
