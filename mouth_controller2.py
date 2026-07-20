import serial
import pyaudio
import numpy as np
import time

# --- CONFIGURATION (FINALIZED VALUES) ---
# 1. Arduino Serial Settings
COM_PORT = 'COM9'  # <<< Set to your specific COM Port
BAUD_RATE = 9600

# 2. Audio Processing Settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
INPUT_DEVICE_INDEX = 13 # <<< Set to your specific Audio Device Index

# 3. Servo and Volume Mapping (Minimal Motion Settings)
MIN_ANGLE = 90  # Closed mouth angle (Initial/Rest Position)
MAX_ANGLE = 105 # Limits the servo to a small 15-degree swing
RMS_THRESHOLD = 0.06 # Only moves the servo for reasonably loud sounds
MAX_RMS_LEVEL = 0.50 # Requires high volume to reach the 105-degree limit

# --- INITIALIZATION ---
try:
    # Initialize Serial communication
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Wait for Arduino to reset after connecting
    print(f"Connected to Arduino on {COM_PORT}")
except serial.SerialException as e:
    print(f"Error connecting to serial port: {e}")
    exit()

# Initialize PyAudio
p = pyaudio.PyAudio()
try:
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=INPUT_DEVICE_INDEX)
    print(f"Listening on audio device index: {INPUT_DEVICE_INDEX}")
except Exception as e:
    print(f"Error opening audio stream. Check your INPUT_DEVICE_INDEX: {e}")
    ser.close()
    p.terminate()
    exit()

print("\n--- Listening for Perplexity Pro Audio. ---")
print(f"Servo range set to {MIN_ANGLE} to {MAX_ANGLE} degrees for minimal motion.")

# --- MAIN LOOP ---
try:
    while True:
        # Read audio data from the loopback device
        data = stream.read(CHUNK, exception_on_overflow=False)
        # Convert data to NumPy array for RMS calculation
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Calculate Root Mean Square (RMS) to get volume
        rms = np.sqrt(np.mean(audio_data**2)) / 32768.0 
        
        # Map the volume (RMS) to the servo angle
        if rms > RMS_THRESHOLD:
            # np.interp scales the volume (input range) to the angle range (output range)
            angle = np.interp(rms, 
                              [RMS_THRESHOLD, MAX_RMS_LEVEL], 
                              [MIN_ANGLE, MAX_ANGLE])
        else:
            # When sound is below threshold, send the minimum angle (closed/initial position)
            angle = MIN_ANGLE

        # Ensure the angle is within the safe limits
        angle = int(np.clip(angle, MIN_ANGLE, MAX_ANGLE))
        
        # Send the calculated angle to the Arduino
        command = f"{angle}\n" 
        ser.write(command.encode('utf-8'))
        
        # Optional: Uncomment the line below for real-time debugging!
        # print(f"RMS: {rms:.4f} -> Angle: {angle}")

except KeyboardInterrupt:
    print("\nStopping controller...")
except Exception as e:
    print(f"\nAn error occurred: {e}")
    
finally:
    # Cleanup and close connections
    stream.stop_stream()
    stream.close()
    p.terminate()
    ser.close()
    print("Program finished and connections closed.")