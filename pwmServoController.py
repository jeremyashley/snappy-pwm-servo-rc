
from synapse.RF200 import *

TCCR1B_INIT = 18  # Phase & Frequency PWM, TOP=ICR1; FOSC/8
TCCR1B_TOFF = 16  # Phase & Frequency PWM, TOP=ICR1; FOSC OFF
TCCR1A_INIT = 0b11111100 # Enable Toggle on ABC; P&F PWM, TOP=ICR1
ICR1_TOP = 20000 / 4 # 20ms / 4 (16 MHz / 8 -> 2MHz .. /2 = 1MHz


def initTimer1():
    global TCCR1A_INIT, TCCR1B_INIT, ICR1_TOP
    poke(0x81,TCCR1B_INIT)
    poke(0x80,TCCR1A_INIT)
    poke16(0x86, 0x87, ICR1_TOP)

def poke16(low, high, value):
    poke(high, value >> 8)
    poke(low, value & 0xFF)
    
def initPins():
    # Set pin direction
    setPinDir(GPIO_2,True) # OC1A
    setPinDir(GPIO_1,True) # OC1B
    setPinDir(GPIO_0,True) # OC1C

def disableTimer1():
    poke(0x81,TCCR1B_TOFF)

def disablePins():
    # Set pin direction
    setPinDir(GPIO_2,False) # OC1A
    setPinDir(GPIO_1,False) # OC1B
    setPinDir(GPIO_0,False) # OC1C
    
# Read Timer values
def readCounterTCNT1():
    return peek(0x84)|peek(0x85)<<8

# NAME, PIN, ADDR_LO, ADDR_HI, TOP, MIN_VAL, MAX_VAL, START, OFFSET, DIR, STEPS, WIDTH
#             0        1      2     3       4       5     6     7    8     9  10      11
SERVO_A = ('LEFT',  GPIO_0, 0x88, 0x89, ICR1_TOP, 1110, 1990, 1500, 1100,  1, 20, (1990 - 1110) / 20)
SERVO_B = ('MOTOR', GPIO_1, 0x8A, 0x8B, ICR1_TOP, 1000, 2000, 1000, 1000,  1, 20, (2000 - 1000) / 20)
SERVO_C = ('RIGHT', GPIO_2, 0x8C, 0x8D, ICR1_TOP, 1110, 1990, 1500, 1990, -1, 20, (1990 - 1110) / 20)

CURRENTA = CURRENTB = CURRENTC = 0

def printServoSetup():
    global SERVO_A, CURRENTA, SERVO_B, CURRENTB, SERVO_C, CURRENTC
    print "NAME, PIN, ADDR_LO, ADDR_HI, TOP, MIN_VAL, MAX_VAL, START, DIR, STEPS, WIDTH, CURRENT"
    print SERVO_A, CURRENTA
    print SERVO_B, CURRENTB
    print SERVO_C, CURRENTC
    
def setServoPulseWidth(servo, width):
    global SERVO_A, SERVO_B, SERVO_C
    poke16(servo[2], servo[3], servo[4] - width)
    print "name: ", servo[0], " pulse width: ", width
    
def initServo(servo):
    setServoPulseWidth(servo, servo[7])
    setPinDir(servo[1], True)
        
def positionToPulseWidth(servo, position):
    position = limit(position, 0, servo[10])
    width = servo[8] + (position * servo[11] * servo[9])
    print "servo: ", servo[0], " position: ", position, " width: ", width
    return width

def setServoPosition(servo, position):
    width = positionToPulseWidth(servo, position)
    setServoPulseWidth(servo, width)
    return position
    
def limit(a, minv, maxv):
    return max(min(a, maxv), minv)

def min(a, b):
    if (a < b):
        return a
    return b

def max(a, b):
    if (a < b):
        return b
    return a

def initServos():
    global SERVO_A, SERVO_B, SERVO_C
    initServo(SERVO_A)
    initServo(SERVO_B)
    initServo(SERVO_C)

@setHook(HOOK_STARTUP)
def pwnServoStart():
    initTimer1()
    initServos()
    initPins()

def pwnServoStop():
    initServos()
    disablePins()

def pwmServoSetServoPositionByName(name, position):
    global SERVO_A, CURRENTA, SERVO_B, CURRENTB, SERVO_C, CURRENTC
    if (SERVO_A[0] == name):
        CURRENTA = setServoPosition(SERVO_A, position)
    if (SERVO_B[0] == name):
        CURRENTB = setServoPosition(SERVO_B, position)
    if (SERVO_C[0] == name):
        CURRENTC = setServoPosition(SERVO_C, position)

def pwmServoSetAllServoPositions(leftPosition, motorPosition, rightPosition):
    pwmServoSetServoPositionByName('LEFT', leftPosition)
    pwmServoSetServoPositionByName('MOTOR', motorPosition)
    pwmServoSetServoPositionByName('RIGHT', rightPosition)
    
def pwnResetServoPosition():
    pwmServoSetAllServoPositions(10, 0, 10)

