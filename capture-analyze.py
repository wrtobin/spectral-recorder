import sys
import os
import time

from datetime import datetime as dt
import sounddevice as sd
from scipy.io.wavfile import write

import math
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


fs = 44100

class RepeatingAsyncRecorder:
    def __init__( self, seconds ):
        self._seconds = seconds
        self._last_start = None
        self._last_end = None 
        self._sound_data = None
        self._active = False

    def start( self ):
        self._last_start = dt.now()
        self._active = True
        self._sound_data = sd.rec( int( self._seconds * fs ), 
                                   samplerate = fs, 
                                   channels=2 )

    def checkDone( self, window = 0.25 ):
        # if we're outside the window, just return False, else wait for the recording to end
        if (dt.now() - self._last_start).seconds < (self._seconds - window):
            return False
        sd.wait( )
        return True

    def finalize( self ):
        self._last_end = dt.now()
        filename = ( self._last_end.strftime("%Y%m%d_%H%M%S") + "__" + 
                     self._last_start.strftime("%Y%m%d_%H%M%S") )
        write(filename + ".wav", fs, self._sound_data)
        self._active = False
        return ( filename, self._sound_data )

    def isActive( self ):
        return self._active

def makeSpectralPlot( filename_root, sound_data ):
        f, t, Sxx = signal.spectrogram( sound_data[:,0], fs, nperseg = 64 )
        dBS = 10 * np.log10( Sxx )
        plt.pcolormesh(t, f, dBS, cmap='inferno')
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.savefig(f'{filename_root}.png', bbox_inches='tight')

def run( args ):
    # parse args to get
    #  reccuring recording length
    #  total run time (S)

    start = dt.now( )
    period = 3
    runtime = 6

    if( not os.path.isdir("data") ):
        os.mkdir("data")
    os.chdir("data")

    rec = RepeatingAsyncRecorder( period )

    unprocessed = { }

    while( (dt.now() - start).seconds < runtime ):
        rec.start( )
        while ( not rec.checkDone( ) ):
            doPop = False
            for ( k, v ) in unprocessed.items( ):
                makeSpectralPlot( k, v )
                doPop = True
                break
            if doPop:
                unprocessed.pop( k )
            if len(unprocessed) == 0:
                time.sleep(0.1)
        ( filename, sound_data ) = rec.finalize( )
        unprocessed[ filename ] = sound_data

    for ( k, v ) in unprocessed.items( ):
        makeSpectralPlot( k, v )

    os.chdir('..')

if __name__ == "__main__":
    run( sys.argv )
