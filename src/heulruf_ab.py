"""
Howl-Call-Automated recorder
"""

import time
import wave
import math
import traceback
import array
import struct
import os
import threading
import alsaaudio
import signal,sys

WIDTH = 2
CHANNELS = 1
RATE = 16000
# Please set upload destination path here
SEND_CMD = "rsync -vcr /tmp/outqueue/ USER@HOST:path"

# Base frequency for inband answerback tones and sequencees
FREQ = 425


def render_beep(freq, duration):
    '''
    Creates a sinewave buffer of signed integers for playback.
    This takes the frequency and duration of the tone as parameters
    NOTE: To avoid having unfinished sine waves in the buffer, this routine
        duplicates a single full wave until it appoximately reaches the length of
        the requested tone. So the sample returned is likely to be a few
        milliseconds shorter than requested.
    '''
    # Render exactly one cycle, first
    wave = [ math.sin(2*freq*math.pi*x/(RATE)) for x in xrange(int(RATE/freq)+1) ]
    raw_wave = ''.join([ struct.pack("<h", x*32000) for x in wave])
    # Now duplicate the raw wave as required
    return raw_wave * int(freq*duration)

# This defines the two beep sequences for user feedback.
# beep_on signified the start of a recording to the user
beep_on = render_beep(425,.25) +  render_beep(425*2,.25) + render_beep(425,.25) + render_beep(425*2,.25)
# beeo_of tells the user the recording has ended.
beep_off = render_beep(2*425,.1) +  render_beep(425,.1)


# For optimzation reasons, both receive and transmit run as two different
# threads. Otherwise the alsa API might begin to stumble when interleaving reads
# and writes.

# All audio data are supposed to be PCM_FORMAT_S16_LE, so 16bit signed int,
# little endian. This seems to give the best performance/resolution balance on
# the PRi hardware

class sender(threading.Thread):
    '''
    Handles audio sending to the line.
    Output data is passed via the global/shared buffer output_buffer.
    '''
    def __init__(self):
        threading.Thread.__init__(self)
        self.device = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NORMAL)
        self.device.setchannels(1)
        self.device.setrate(RATE)
        self.device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.sample_len = 1024
        self.device.setperiodsize(self.sample_len)
        
    
    def run(self):
            global running
            global record_holdoff
            global output_buffer

            while running:
                try:
                        # Play out the remaining buffer
                        out = output_buffer[:self.sample_len]
                        if (len(output_buffer) > self.sample_len):
                            output_buffer = output_buffer[self.sample_len:]
                        else:
                            # When buffer ran empty, holdoff until retriggering
                            # so echoes of our beep_off will not cause disruptions
                            if len(output_buffer)>0:
                                record_holdoff = 50
                            output_buffer = ""

                        # Pad with silence
                        silence = array.array("h",[0] * (self.sample_len-len(out)))
                        out += silence.tostring()
                        self.device.write(out)
                except Exception as e:
                    print e
                    traceback.print_exc()
                    running=False

class receiver(threading.Thread):
    '''
    Implements listening into the line and a part of the control logic.
    The control logic watches the input signal and finds excursions above
    silence threshold level. This level in turn is updated by the average
    peak-peak value within the silence time.

    When recording starts, the beep_on sound is enqueued for playback.

    During recording recording_timeout is > 0 and reset to its maximum whenever
    audio above the threshold value is detected during recording. So the
    recording continues until no signal is detected anymore.

    While record_holdoff is > 0 the input signal does not influece the
    threshold detection. This is done because when the the beep_off sound is
    played after the message is recorded, its echo in the line should not
    reenable recording.
    '''
    def __init__(self):
            threading.Thread.__init__(self)
            self.device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL)
            self.device.setchannels(1)
            self.device.setrate(RATE)
            self.device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            self.sample_len = 1024
            self.device.setperiodsize(self.sample_len)

    def run(self):
            global recording_timeout
            global record_holdoff
            global beep_on, beep_off
            global output_buffer
            global record_buffer
            global running
            
            
            threshold = 500
            while running:
                try:
                    (sample_len, raw_data) = self.device.read()
                    in_array = array.array("h")
                    in_array.fromstring(raw_data)

                    peak_peak = max(in_array) - min(in_array)
                    if (len(output_buffer)==0) and (record_holdoff==0):
                        if peak_peak > 1.5*threshold:
                            if (recording_timeout==0):
                                output_buffer = beep_on
                                record_buffer = array.array("h")

                            recording_timeout = 50
                        else:
                            # Only adjust threshold in silence
                            if (recording_timeout==0):
                                    threshold = (threshold*5 + peak_peak) / 6

                    if record_holdoff>0:
                        record_holdoff-=1

                    # Record if necessary
                    record_buffer += in_array


                    print self.sample_len, len(output_buffer), recording_timeout, threshold, peak_peak
                except Exception as e:
                    print e
                    traceback.print_exc()
                    running=False


# This is done to exit all threads at the same time
def exit_handler(signal, frame):
	global running
	running=False

signal.signal(signal.SIGINT, exit_handler)



recording_timeout = False
record_buffer = array.array("h")
output_buffer = beep_on
record_holdoff = 0

running=True

send_thread = sender()
recv_thread = receiver()

send_thread.start()
recv_thread.start()

# Main control loop, this thaes case of recording the audiostream when the
# message has finished. Also this will run the upload command.
while running:

    time.sleep(.1)
    if recording_timeout > 0:
        recording_timeout -= 1
        if recording_timeout == 0:
            output_buffer = beep_off
            recording_name = '/tmp/output_'+str(int(time.time()))
            print "Begin write"
		
            with open(recording_name+".s16","w+") as f:
                data = array.array("h", record_buffer)
                data.tofile(f)
                f.close()
            print "End write"
            command = "mkdir -p /tmp/outqueue; (nice -n 10 sox -r{1} -c1 {0}.s16 {0}.mp3 compand 0.3,.8 6:-70,-60,-20 norm -3 && rm {0}.s16 ; mv {0}.mp3 /tmp/outqueue ; {2} ) &".format(recording_name,RATE, SEND_CMD)
            os.system(command)


running=False
