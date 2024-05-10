from machine import Pin, ADC, I2C, PWM
from ssd1306 import SSD1306_I2C
import utime
import array

# OLED
i2c = I2C(1, scl = Pin(15), sda = Pin(14))
oled = SSD1306_I2C(128, 64, i2c)
                                                #                     FUNCTIONS                    #

                       
        

    
#   Function to display "Start menu"   #

def press_to_start():
    oled.fill(0)
    oled.text("Press to start", 4, 7, 1)
    oled.text("the measurement", 4, 17, 1)
    oled.line(10, 53, 15, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(118, 48, 124, 53, 1)
    oled.line(118, 58, 124, 53, 1)
    oled.line(93, 53, 124, 53, 1)
    oled.line(48, 53, 60, 53, 1)
    horizontal = 0
    
    for i in range(2):
        oled.line(60-horizontal, 53, 63-horizontal, 50, 1)
        oled.line(63-horizontal, 50, 66-horizontal, 53, 1)
        oled.line(66-horizontal, 53, 68-horizontal, 53, 1)
        oled.line(68-horizontal, 53, 70-horizontal, 57, 1)
        oled.line(70-horizontal, 57, 73-horizontal, 31, 1)
        oled.line(73-horizontal, 31, 76-horizontal, 64, 1)
        oled.line(76-horizontal, 64, 78-horizontal, 53, 1)
        oled.line(78-horizontal, 53, 80-horizontal, 53, 1)
        oled.line(80-horizontal, 53, 84-horizontal, 47, 1)
        oled.line(84-horizontal, 47, 88-horizontal, 53, 1)
        oled.line(88-horizontal, 53, 89-horizontal, 53, 1)
        oled.line(89-horizontal, 53, 91-horizontal, 51, 1)
        oled.line(91-horizontal, 51, 93-horizontal, 53, 1)
        
        horizontal += 45
        
    oled.show()
    

#   Functions for connecting to WLAN   #

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return

def display_multiline_text(text):
    y_padding=2
    screen_width = oled.width
    char_width = 8
    max_chars_per_line = screen_width // char_width
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > max_chars_per_line:
            lines.append(current_line)
            current_line = word
        else:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
    if current_line:
        lines.append(current_line)

    char_height = 10 
    line_height = char_height + y_padding
    total_height = len(lines) * line_height - y_padding
    start_y = max(0, (oled.height - total_height) // 2)

    oled.fill(0)
    y_position = start_y
    for line in lines:
        line_width = len(line) * char_width
        x_position = (screen_width - line_width) // 2
        oled.text(line, x_position, y_position, 1)
        y_position += line_height

    oled.show() 

