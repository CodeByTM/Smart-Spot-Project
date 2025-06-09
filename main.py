#!/home/pi/software/bin/python3.11

import os
import time
import cv2
import RPi.GPIO as GPIO
from flask import Flask, render_template, Response, request, jsonify
from threading import Thread
from mfrc522 import SimpleMFRC522
from gpiozero import AngularServo, LED, Button
from gpiozero.pins.pigpio import PiGPIOFactory
from rpi_lcd import LCD
import subprocess
import atexit


# Start pigpiod if not running
def start_pigpiod():
   try:
       subprocess.check_output(["pgrep", "pigpiod"])
   except subprocess.CalledProcessError:
       print("Starting pigpiod...")
       subprocess.run(["sudo", "pigpiod"])


GPIO.setmode(GPIO.BCM)
start_pigpiod()

app = Flask(__name__)
GPIO.setwarnings(False)

# Define GPIO pins
LED_GREEN_PIN = 27
LED_RED_PIN = 17
SERVO1_PIN = 13
SERVO2_PIN = 18
IR_SENSOR1_PIN = 20
IR_SENSOR2_PIN = 25  # 23
RFID_RST_PIN = 24
KEYPAD_ROW_PINS = [5, 6, 12, 19]
KEYPAD_COL_PINS = [26, 4, 22, 21]

# Initialize hardware components

GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
GPIO.setup(LED_RED_PIN, GPIO.OUT)
GPIO.setup(IR_SENSOR1_PIN, GPIO.IN)
GPIO.setup(IR_SENSOR2_PIN, GPIO.IN)

for row_pin in KEYPAD_ROW_PINS:
   GPIO.setup(row_pin, GPIO.OUT, initial=GPIO.LOW)
for col_pin in KEYPAD_COL_PINS:
   GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Use PiGPIOFactory for more accurate PWM control
factory = PiGPIOFactory()
servo1 = AngularServo(SERVO1_PIN, min_pulse_width=0.0006, max_pulse_width=0.0023, pin_factory=factory)
servo2 = AngularServo(SERVO2_PIN, min_pulse_width=0.0006, max_pulse_width=0.0023, pin_factory=factory)
reader = SimpleMFRC522()
lcd = LCD()
# Directory to save screenshots
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
   os.makedirs(SCREENSHOT_DIR)

# Initial state
available_spots = 8
PASSWORD = '1234'
passcode_status = ""
current_option = ""
keypad_input = False  # Flag to indicate if keypad input is detected


def lcd_init():
   lcd.text("Enter A, B, or C", 1)
   lcd.text("", 2)


def check_ir_state(num):
   global proxState1
   global proxState2
   if (num == 1):
       proxState1 = GPIO.input(IR_SENSOR1_PIN)
       print(proxState1)
       return int(proxState1)
   if (num == 2):
       proxState2 = GPIO.input(IR_SENSOR2_PIN)
       return int(proxState2)


def check_fob(text):
   members = [1111, 2222, 3333, 4444, 5555, 7777, 8888]
   if text in members:
       return True
   else:
       return False


def open_gate():
   global available_spots
   proxState = check_ir_state(1)  # checking the status of ir sensor 1
   if available_spots > 0 and proxState == 0:
       lcd.clear()
       servo1.angle = 0
       GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
       GPIO.output(LED_RED_PIN, GPIO.LOW)
       lcd.text("    Welcome!", 1)
       lcd.text(f"    Spots: {available_spots}", 2)
       servo1.angle = 90
       time.sleep(5)
       servo1.angle = 0
       available_spots -= 1
       GPIO.output(LED_GREEN_PIN, GPIO.LOW)
       GPIO.output(LED_RED_PIN, GPIO.HIGH)
       lcd.clear()
       reset_lcd()

   if proxState == 1:
       lcd.text("Drive Closer", 1)
       lcd.text("To Gate", 2)
       time.sleep(3)
       lcd.clear()
       open_gate()

   if available_spots <= 0:
       lcd.clear()
       lcd.text("    No Spots", 1)
       lcd.text("   Available", 2)
       GPIO.output(LED_GREEN_PIN, GPIO.LOW)
       GPIO.output(LED_RED_PIN, GPIO.HIGH)
       if available_spots > 0:
           lcd.clear()
           reset_lcd()


def reset_lcd():
   lcd.clear()
   global current_option
   current_option = ""
   lcd.text("Enter A, B, or C", 1)
   lcd.text("", 2)


def close_gate():  # this is the exit gate
   global available_spots
   while True:
       proxState = check_ir_state(2)
       if available_spots < 8 and proxState == 0:
           servo2.angle = 20
           time.sleep(0.5)
           servo2.angle = 90
           time.sleep(5)
           servo2.angle = 20
           available_spots += 1
           lcd.clear()
           reset_lcd()
       time.sleep(0.1)


def read_rfid():
   lcd.text("Hold a tag near the reader", 1)
   id, text = reader.read()
   print(text)
   lcd.clear()
   return int(text)


def save_screenshot():
   camera = cv2.VideoCapture(0)
   success, frame = camera.read()
   if success:
       filename = os.path.join(SCREENSHOT_DIR, f"screenshot_{int(time.time())}.jpg")
       cv2.imwrite(filename, frame)
       return f"Screenshot saved: {filename}"
   return "Failed to take screenshot"


@app.route('/')
def index():
   return render_template('index.html')


@app.route('/video_feed')
def video_feed():
   return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


def gen_frames():
   camera = cv2.VideoCapture(0)
   while True:
       success, frame = camera.read()
       if not success:
           break
       else:
           ret, buffer = cv2.imencode('.jpg', frame)
           frame = buffer.tobytes()
           yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/open_gate', methods=['POST'])
def open_gate_route():
   open_gate()
   return "Gate opened"


@app.route('/status')
def status():
   global passcode_status
   global current_option
   return jsonify({
       "available_spots": available_spots,
       "passcode_status": passcode_status,
       "current_option": current_option
   })


@app.route('/operator_open_gate', methods=['POST'])
def operator_open_gate():
   global available_spots
   if available_spots > 0:
       lcd.clear()
       GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
       GPIO.output(LED_RED_PIN, GPIO.LOW)
       lcd.text("    Welcome!", 1)
       lcd.text(f"    Spots: {available_spots}", 2)
       servo1.angle = 90
       available_spots -= 1
       time.sleep(5)
       lcd.clear()
       reset_lcd()
   else:
       lcd.clear()
       lcd.text("    No Spots", 1)
       lcd.text("   Available", 2)
       GPIO.output(LED_GREEN_PIN, GPIO.LOW)
       GPIO.output(LED_RED_PIN, GPIO.HIGH)
       time.sleep(5)
       lcd.clear()
       reset_lcd()
   return "Operator opened the gate"


@app.route('/operator_close_gate', methods=['POST'])
def operator_close_gate():
   lcd.clear()
   servo1.angle = 0  # Close the gate (servo back to 0 degrees)
   GPIO.output(LED_GREEN_PIN, GPIO.LOW)
   GPIO.output(LED_RED_PIN, GPIO.HIGH)
   lcd.clear()
   reset_lcd()
   return "Operator closed the gate"


@app.route('/save_screenshot', methods=['POST'])
def save_screenshot_route():
   message = save_screenshot()
   return message


@app.route('/end_program', methods=['POST'])
def end_program():
   shutdown = request.environ.get('werkzeug.server.shutdown')
   if shutdown:
       shutdown()
   return "Program ended"


def handle_keypad():
   global passcode_status
   global current_option
   global keypad_input

   keys = [
       ['1', '2', '3', 'A'],
       ['4', '5', '6', 'B'],
       ['7', '8', '9', 'C'],
       ['*', '0', '#', 'D']
   ]
   entered_passcode = ""

   def read_keypad():
       for i, row_pin in enumerate(KEYPAD_ROW_PINS):
           GPIO.output(row_pin, GPIO.HIGH)
           for j, col_pin in enumerate(KEYPAD_COL_PINS):
               if GPIO.input(col_pin) == GPIO.HIGH:
                   GPIO.output(row_pin, GPIO.LOW)
                   return keys[i][j]
           GPIO.output(row_pin, GPIO.LOW)
       return None

   while True:
       key = read_keypad()
       if key:
           keypad_input = True  # Set keypad_input to True to indicate key press

           if current_option == "":
               if key == 'A':
                   current_option = "fob"
               elif key == 'B':
                   current_option = "forgot_fob"
               elif key == 'C':
                   current_option = "not_member"

               if current_option == "fob":
                   text = read_rfid()
                   print(text)
                   time.sleep(5)
                   check = check_fob(text)
                   if (check == True):
                       open_gate()
                   if (check == False):
                       lcd.text("  Not in,", 1)
                       lcd.text("   system", 2)
                       time.sleep(2)
                       lcd.clear()
                       reset_lcd()
               elif current_option == "forgot_fob":
                   lcd.text("Enter Passcode", 1)
                   lcd.text("", 2)
               elif current_option == "not_member":
                   lcd.text("Contact Office", 1)
                   lcd.text("", 2)
                   time.sleep(2)
                   reset_lcd()
           elif current_option == "forgot_fob":
               if key == '#':
                   if entered_passcode == PASSWORD:
                       lcd.clear()
                       lcd.text("   Passcode", 1)
                       lcd.text("   Correct", 2)
                       time.sleep(3)
                       lcd.clear()
                       passcode_status = "Passcode Correct"
                       open_gate()
                   else:
                       lcd.clear()
                       lcd.text("   Passcode", 1)
                       lcd.text("   Incorrect", 2)
                       time.sleep(3)
                       lcd.clear()
                       passcode_status = "Passcode Incorrect"
                   entered_passcode = ""
                   reset_lcd()
               else:
                   entered_passcode += key
                   lcd.text(len(entered_passcode) * "*", 2)

       time.sleep(0.1)  # Adjust this delay as needed to control the loop frequency


def cleanup():
   GPIO.cleanup()
   servo1.detach()
   servo2.detach()


if __name__ == '__main__':
   lcd_init()
   servo2.angle = 20

   t1 = Thread(target=close_gate)
   t2 = Thread(target=handle_keypad)


   t1.start()
   t2.start()

   atexit.register(cleanup)

   app.run(host='0.0.0.0', port=5000)




