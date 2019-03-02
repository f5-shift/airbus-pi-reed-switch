#!/bin/python3

import RPi.GPIO as GPIO
import requests
from time import sleep
from pprint import PrettyPrinter

GPIO_PATH = "/sys/class/gpio"
REED_PIN = 4
URL = "https://sheltered-citadel-43963.herokuapp.com"
TIMEOUT = 2

seat = '6A'
pp = PrettyPrinter(indent=4)

def export(pin):
  try:
    path = GPIO_PATH + "/export"
    with open(path, 'w') as f:
      f.write(str(pin))
  except IOError:
    print("GPIO {} already exists, no need to export".format(pin))

def unexport(pin):
  try:
    path = GPIO_PATH + "/unexport"
    with open(path, 'w') as f:
      f.write(str(pin))
  except IOError:
    print("GPIO {} already exists, no need to unexport".format(pin))


def setup():
  GPIO.setmode(GPIO.BCM)          # set pin numbering scheme
  export(REED_PIN)
  GPIO.setup(REED_PIN, GPIO.IN)   # setup input pin


def onchange(gpio):
  params = {'seat': seat }
  if GPIO.input(REED_PIN):
    print("Rising edge = unbuckled")
    requests.get(url="{}/unbuckle".format(URL), params=params)
  else:
    print("Falling edge = buckled")
    requests.get(url="{}/buckle".format(URL), params=params)


def main():
  # busy polling
  '''
  while True:
    state = GPIO.input(REED_PIN)
    print("State of", REED_PIN, "is", state) 
    sleep(TIMEOUT)
  '''

  GPIO.add_event_detect(REED_PIN, GPIO.BOTH, callback=onchange, bouncetime=10)

  print("State of", REED_PIN, "is", GPIO.input(REED_PIN))
  
  while True:
    sleep(TIMEOUT)


def cleanup():
  unexport(REED_PIN)


if __name__ == "__main__":
  print("Setup...", end="")
  setup()
  print("done!")

  try:
    main()
  except (KeyboardInterrupt, SystemExit):
    print("Cleanup...", end="")
    cleanup()
    print("done!")
  except RuntimeError:
    pp.pprint(locals())
  
