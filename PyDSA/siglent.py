#coding=utf8

import logging
logger = logging.getLogger(__name__)

from time import sleep
import re

import vxi11
import numpy

def parse_sample_rate(sample_rate_string):
	'''
	u'SARA 1GSa/s'
	u'SARA 500MSa/s'
	u'SARA 50MSa/s'
	u'SARA 50MSa/s'
	u'SARA 1kSa/s'
	'''

	match = re.search(r'SARA (\d+)([kMG])Sa\/s', sample_rate_string)

	if match is None:
		raise Exception("Unable to parse sample rate string from Siglent scope: {}".format(sample_rate_string))

	multipliers = {
		'k': 1e3,
		'M': 1e6,
		'G': 1e9,
	}
	sample_rate = int(match.group(1)) * multipliers[match.group(2)]
	return sample_rate

def connect(ip_address):
	logger.debug("Connecting to Siglent scope via IP at {}".format(ip_address))
	scope = vxi11.Instrument(ip_address)
	return scope

def acquire(scope, long_memory=False, max_samples=2**23):
	'''Grab the raw data from channel 1'''

	## SCOPE SETUP

	# auto setup
	#scope.write('ASET')

	# enable C1, disable C2
	scope.write('C1:TRA ON')
	scope.write('C2:TRA OFF')

	## DATA ACQUISITION
	#scope.write('TRMD SINGLE')
	#scope.write('TRMD AUTO')
	#scope.write("WAIT")
	#scope.write("STOP")
	#scope.ask("SAST?")

	# TODO: Ensure scope set up to generate enough sample points
	# From user manual p 55:
	# Memory depth = sample rate (Sa/s) × waveform length (s/div × div)
	# 1e9 Sa/s * 1e-3 s/div * 14 div = 14e6 Sa
	# So set to 1 ms/dev
	scope.write('TDIV 1ms')
	scope.write('WFSU TYPE,1')
	scope.write('WFSU NP,{}'.format(max_samples))

	sleep(0.1)               

    ## DATA RETRIEVAL

	# TODO: Set desired number of sample points using WFSU to avoid collecting more than we'll use
	trace_bytes = scope.ask_raw("C1:WF? DAT2")
	sample_rate_string = scope.ask('SARA?')

	## DATA CONVERSION AND FORMATTING

	# First 21 bytes seems to be status message, last 2 are \n\n
	trace_bytes = trace_bytes[21:][:-2]

	# convert data from (inverted) bytes to an array of scaled floats
	# this magic from Matthew Mets
	signals = numpy.frombuffer(trace_bytes, 'B')
	signals = (signals * -1 + 255) - 130 # invert
	signals = signals / 127.0 # scale 10 +-1, has a slight DC offset

	sample_rate = parse_sample_rate(sample_rate_string)

	print len(trace_bytes)

	print sample_rate
	print signals

	return signals, sample_rate

