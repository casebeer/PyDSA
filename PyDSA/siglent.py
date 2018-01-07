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

def acquire(scope, long_memory=False, desired_samples=2**23):
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
	# e.g. 1e9 Sa/s * 1e-3 s/div * 14 div = 14e6 Sa
	# Options include 1US,2US,5US,10US,20US,50US,100US,200US,500US,1MS
	# So set to 1 ms/div for 14 MSa (which is max TDIV that will use 1 GSA/s)
	# So set to 1 us/div for 14 kSa (below which we don't collect minimum 8192 samples)
	tdivs = {
		1e-6:  '1US',
		2e-6:  '2US',
		5e-6:  '5US',
		10e-6: '10US',
		20e-6: '20US',
		50e-6: '50US',
		100e-6:'100US',
		200e-6:'200US',
		500e-6:'500US',
		1e-3:  '1MS',
	}

	min_tdiv = desired_samples / (1e9 * 14)
	tdiv = min(t for t in tdivs if t > min_tdiv)
	tdiv_string = tdivs[tdiv]
	scope.write('TDIV {}'.format(tdiv_string))
	logger.debug("Set scope for {} per division for at least {} samples".format(tdiv_string, desired_samples))

	# n.b. Setting NP (number points) seems to corrupt the data; limit points with TDIV instead
	scope.write('WFSU SP,0,NP,0,FP,0')
	#scope.write('WFSU SP,0,NP,{},FP,0'.format(desired_samples))
	#scope.write('WFSU TYPE,1')

	sleep(0.1)               

    ## DATA RETRIEVAL

	trace_bytes = scope.ask_raw("C1:WF? DAT2")
	sample_rate_string = scope.ask('SARA?')

	logger.debug("{} samples available".format(scope.ask('SANU? C1')))
	logger.debug("{} samples retrieved".format(len(trace_bytes) - 21 - 2))

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

