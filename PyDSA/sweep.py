import logging
logger = logging.getLogger(__name__)

#import PyDSA as pydsa
import siglent
#import rigol

def sweep(connection_string, pydsa):   # Read samples and store the data into the arrays
	# Main loop
	while True:
		# RUNstatus = 1 : Open Stream
		if pydsa.RUNstatus == 1:
			try:

				#scope = rigol.connect()
				scope = siglent.connect(connection_string)

				pydsa.RUNstatus = 2
			except: # If error in opening audio stream, show error
				pydsa.RUNstatus = 0
				pydsa.showerror("VISA Error", "Cannot open scope")
			pydsa.UpdateScreen() # UpdateScreen() call		

		# RUNstatus = 2: Reading audio data from soundcard
		if pydsa.RUNstatus == 2:
			pydsa.update_status("->Acquire", 275, 32)

			#signals, sample_rate = rigol.acquire(scope, long_memory=(pydsa.SAMPLEdepth == 1))
			signals, sample_rate = siglent.acquire(scope, desired_samples=2**17)
		
			pydsa.SIGNAL1 = signals
			pydsa.SAMPLErate = sample_rate

			pydsa.UpdateAll() # Update Data, trace and screen

			if pydsa.SWEEPsingle == True:  # single sweep mode, sweep once then stop
				pydsa.SWEEPsingle = False
				pydsa.RUNstatus = 3
				
		# RUNstatus = 3: Stop
		# RUNstatus = 4: Stop and restart
		if pydsa.RUNstatus in (3, 4):
			#scope.write(":KEY:FORCE")
			#scope.close()
			if pydsa.RUNstatus == 3:
				pydsa.RUNstatus = 0							   # Status is stopped
			if pydsa.RUNstatus == 4:		
				pydsa.RUNstatus = 1							   # Status is (re)start
			pydsa.UpdateScreen()								  # UpdateScreen() call


		# Update tasks and screens by TKinter
		pydsa.root.update_idletasks()
		pydsa.root.update()									   # update screens
