from flask import Flask, render_template, Response, send_from_directory
import os
import time
import gpiozero as g0
from threading import Thread

# Define the pins in use for Motor1 and add to a list
in1_m1 = g0.OutputDevice(17)
in2_m1 = g0.OutputDevice(18)
in3_m1 = g0.OutputDevice(21)
in4_m1 = g0.OutputDevice(22)
steppins_m1 = [in1_m1, in2_m1, in3_m1, in4_m1]

# Define the pins in use for Motor2 and add to a list
in4_m2 = g0.OutputDevice(19)
in3_m2 = g0.OutputDevice(13)
in2_m2 = g0.OutputDevice(5)
in1_m2 = g0.OutputDevice(6)
steppins_m2 = [in1_m2, in2_m2, in3_m2, in4_m2]

# Define step sequence
# as shown in manufacturers datasheet
seq = [[1, 0, 0, 1],
       [1, 0, 0, 0],
       [1, 1, 0, 0],
       [0, 1, 0, 0],
       [0, 1, 1, 0],
       [0, 0, 1, 0],
       [0, 0, 1, 1],
       [0, 0, 0, 1]]

# Define wait times to correlate with speeds and gear
speeds = {"L": (10, 8, 5, 3, 2.5, 2, 1.5, 1, .8, .5, .3),
          "H": (11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1.5)}


# Set Variable for state tracking
running = True
stepcount = len(seq)
curdirection = 'S'     # Variable for direction. F Forward, B Backwards, R Right, L Left, SR SpinRight SL SpinLeft
curspeed = 0           # Speed values for 0 - 10. 0 is stationary
curgear = 'L'          # Set for H High or L Low gear. Low is slower but more torque
app = Flask(__name__)


# Function for continuous movements using variables from the global scope for speed and direction
def move():
    rstepcounter = 0
    lstepcounter = 0
    while running:
        if curgear == 'L':
            seqsize = -1
        elif curgear == 'H':
            seqsize = -2
        else:
            print('Error in Gear selection')
        rstepdir = seqsize  # Set to 1 or 2 for fwd, -1 or -2 for back
        lstepdir = seqsize  # Set to 1 or 2 for fwd, -1 or -2 for back
        if curdirection == 'B':
            rstepdir *= -1
            lstepdir *= -1
        elif curdirection == 'BR' or curdirection == 'R':
            lstepdir *= -1
        elif curdirection == 'BL' or curdirection == 'L':
            rstepdir *= -1
        waittime = speeds[curgear][int(curspeed)]/float(1000)  # adjust this to change speed
        for pin in range(0, 4):
            lpin = steppins_m1[pin]
            rpin = steppins_m2[pin]
            if seq[rstepcounter][pin] != 0:
                if curdirection == 'FR' or curdirection == 'B' or curdirection == 'F' or curdirection == 'BL' or curdirection == 'R' or curdirection == 'L':
                    rpin.on()
            else:
                rpin.off()
            if seq[lstepcounter][pin] != 0:
                if curdirection == 'FL' or curdirection == 'B' or curdirection == 'F' or curdirection == 'BR' or curdirection == 'R' or curdirection == 'L':
                    lpin.on()
            else:
                lpin.off()
        rstepcounter += rstepdir
        lstepcounter += lstepdir
        if rstepcounter >= stepcount:  # Repeat sequence
            rstepcounter = 0
        if rstepcounter < 0:
            rstepcounter = stepcount + rstepdir
        if lstepcounter >= stepcount:  # Repeat sequence
            lstepcounter = 0
        if lstepcounter < 0:
            lstepcounter = stepcount + lstepdir
        time.sleep(waittime)  # pause

# Route for Favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Default/Index Route to a page that redirects the user
@app.route('/')
def index():
    return render_template('index.html')

# Route for Henry control page
@app.route('/henry/<direction>/<gear>/<speed>')
def henry(direction, gear, speed):
    global curdirection
    global curgear
    global curspeed
    curdirection = direction
    curgear = gear
    curspeed = speed
    return render_template('henry.html', direction=direction, gear=gear, speed=speed)

# Main
if __name__ == '__main__':
    try:
        # Run the move function as a separate thread
        t1 = Thread( target=move )
        t1.start()
        # Run the Flask Web App
        app.run(host='0.0.0.0', port=5000)
    finally:
        running = False