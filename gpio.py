#!/bin/python3

import RPi.GPIO as GPIO
import requests
from time import sleep
from pprint import PrettyPrinter

GPIO_PATH = "/sys/class/gpio"
REED_PIN = 4
URL = "https://sheltered-citadel-43963.herokuapp.com"
TIMEOUT = 5

seat = '6A'
announcement = False
cached = None
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
  global announcement
  if announcement:
    print("annoucement, so ignore transition")
    return

  params = {'seat': seat }
  res = None
  if GPIO.input(REED_PIN):  
    # high signal := open
    print("Rising edge = unbuckled")
    res = requests.get(url="{}/unbuckle".format(URL), params=params)
  else:
    # low signal := closed
    print("Falling edge = buckled")
    res = requests.get(url="{}/buckle".format(URL), params=params)

  if res.status_code == 503 and not announcement:
    announcement = True

    # busy poll for announcement to stop
    # then send updated state
    while True:
      state = GPIO.input(REED_PIN)
      buckled = 1 - state

      print("announcement, sending %d" % buckled)
      res = requests.get(url="{}/init".format(URL), params={ 'seat': seat, 'buckled':  buckled })

      cached = buckled
      if res.status_code == 200:
        print("announcement stopped")
        break
    
      sleep(0.5)

    if cached is not None:
      requests.get(url="{}/init".format(URL), params={ 'seat': seat, 'buckled':  cached })

    # reset cache and announcement flag
    cached = None
    announcement = False


def main():
  # onchange callback
  GPIO.add_event_detect(REED_PIN, GPIO.BOTH, callback=onchange, bouncetime=10)

  # send initial state to server
  state = GPIO.input(REED_PIN)
  buckled = 1 - state
  res = requests.get(url="{}/init".format(URL), params={ 'seat': seat, 'buckled':  buckled })

  # TODO deal with announcement status code
  print("Status code", res.status_code)

  print("Initial state of", REED_PIN, "is", GPIO.input(REED_PIN))
  
  # keep the thread running
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
  
