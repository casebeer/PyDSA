import logging
logger = logging.getLogger(__name__)

from time import sleep

import visa
import numpy

def connect():
	# Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
	instruments = visa.get_instruments_list()
	usb = filter(lambda x: 'USB' in x, instruments)
	if len(usb) != 1:
		logger.warn('Bad instrument list', instruments)
		raise Exception("Bad instrument list", instruments)

	scope = visa.instrument(usb[0], timeout=20, chunk_size=1024000) # bigger timeout for long mem
	return scope

def acquire(scope, long_memory=False):
	# Grab the raw data from channel 1
	# Set the scope the way we want it
	if long_memory:
		scope.write(':ACQ:MEMD NORM') # Long memory type
	else:
		scope.write(':ACQ:MEMD LONG') # normal memory type

	scope.write(":RUN")
	while scope.ask(':TRIG:STAT?') != 'STOP':
		sleep(0.1)

    # Grab the raw data from channel 1, which will take a few seconds for long buffer mode
	scope.write(":STOP")
	scope.write(":WAV:POIN:MODE RAW")

	signals_buffer = scope.ask(":WAV:DATA? CHAN1")  #do this first
	sample_rate = scope.ask_for_values(':ACQ:SAMP?')[0] #do this second

	sleep(0.1)               

	# convert data from (inverted) bytes to an array of scaled floats
	# this magic from Matthew Mets
	signals = numpy.frombuffer(signals_buffer, 'B')
	signals = (signals * -1 + 255) - 130 # invert
	signals = signals / 127.0 # scale 10 +-1, has a slight DC offset

	return signals, sample_rate

