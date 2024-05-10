from machine import Pin, ADC, I2C, PWM

from ssd1306 import SSD1306_I2C
import time
from History import history
from Monitor import monitor

# i2c = SoftI2C(scl=Pin(15), sda=Pin(14))
# oled = ssd1306.SSD1306_I2C(128, 64, i2c)

i2c = I2C(1, scl = Pin(15), sda = Pin(14))
oled = SSD1306_I2C(128, 64, i2c)
menu_items = ['MEASURE HR', 'HRV ANALYSIS', 'KUBIOS', 'HISTORY']

pin_clk = Pin(10, Pin.IN, Pin.PULL_UP)
pin_dt = Pin(11, Pin.IN, Pin.PULL_UP)
pin_sw = Pin(12, Pin.IN, Pin.PULL_UP)

pin_btn_up = Pin(7, Pin.IN, Pin.PULL_UP)
pin_btn_down = Pin(9, Pin.IN, Pin.PULL_UP)
pin_btn_enter = Pin(8, Pin.IN, Pin.PULL_UP)

current_selection = 0
last_clk_value = pin_clk.value()
last_sw_value = pin_sw.value()
debounce_time = 0  
last_debounce_time = 0

encoder_threshold = 3 

encoder_counter = 0

    
    
def oled_menu(selection):
    oled.fill(0) 
    line_height = 10
    padding_between_items = 5

    menu_height = len(menu_items) * (line_height + padding_between_items)

    start_y = (oled.height - menu_height) // 2 
    padding_top = (line_height - 8) // 2

    for i, item in enumerate(menu_items):
        menu_text = item
        y_position = start_y + i * (line_height + padding_between_items) + padding_top
        if i == selection:
            oled.fill_rect(0, y_position - padding_top, oled.width, line_height, 1)
            oled.text(menu_text, 0, y_position, 0)
        else:
            oled.text(menu_text, 0, y_position, 1)

    oled.show()



def read_encoder():
    global last_clk_value, last_debounce_time, encoder_counter
    clk_value = pin_clk.value()
    dt_value = pin_dt.value()
    rotation = 0

    if time.ticks_diff(time.ticks_ms(), last_debounce_time) > debounce_time:
        if clk_value != last_clk_value:
            last_debounce_time = time.ticks_ms()
            if clk_value != dt_value:
                encoder_counter += 1
            else:
                encoder_counter -= 1
            
            last_clk_value = clk_value
            
            if abs(encoder_counter) >= encoder_threshold:
                rotation = 1 if encoder_counter > 0 else -1
                encoder_counter = 0  # Reset the counter after processing

    return rotation


def encoder_button_pressed():
    global last_sw_value, last_debounce_time
    sw_value = pin_sw.value()
    pressed = False
    
    if time.ticks_diff(time.ticks_ms(), last_debounce_time) > debounce_time:
        if sw_value != last_sw_value and sw_value == 0:
            last_debounce_time = time.ticks_ms()
            pressed = True
        last_sw_value = sw_value
    
    return pressed

def update_selection(delta):
    global current_selection
    new_selection = current_selection + delta
    if 0 <= new_selection < len(menu_items):
        current_selection = new_selection
    oled_menu(current_selection)

    
oled_menu(current_selection)

while True:
    delta = read_encoder()
    if delta:
        update_selection(delta)
    
    if encoder_button_pressed():
        if current_selection == 0:
            monitor("hr", None)
        elif current_selection == 1:
            monitor("hrv", 30)
        elif current_selection == 2:
            monitor("kubios", 30)
        elif current_selection == 3:
            history()

        else:
            print(current_selection)  

        oled_menu(current_selection)
        time.sleep(0.30)
   


