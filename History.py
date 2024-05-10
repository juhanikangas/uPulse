from machine import Pin, ADC, I2C, PWM
from ssd1306 import SSD1306_I2C
import time
import network
import ujson
from umqtt.simple import MQTTClient
import Request
from functions import *



def history():
    response = []

    i2c = I2C(1, scl = Pin(15), sda = Pin(14))
    oled = SSD1306_I2C(128, 64, i2c)

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
    
    display_lines = 6
    
    showing = None
    
    def parse_utc_to_finnish(utc_timestamp):
        year = int(utc_timestamp[0:4])
        month = int(utc_timestamp[5:7])
        day = int(utc_timestamp[8:10])
        hour = int(utc_timestamp[11:13])
        minute = int(utc_timestamp[14:16])
        second = int(utc_timestamp[17:19])

        utc_hour = hour
        if (month > 3 and month < 10) or \
           (month == 3 and day - (day % 7) > 24) or \
           (month == 10 and day - (day % 7) <= 24):
            hour += 3
        else:
            hour += 2

        if hour >= 24:
            hour -= 24
            day += 1

        finnish_time = f"{year:04}.{month:02}.{day:02} {hour:02}:{minute:02}:00"
        return finnish_time



    def oled_menu(index):
        oled.fill(0)
        start_line = max(0, index - (display_lines // 2))
        end_line = min(len(response) + 1, start_line + display_lines)
        padding = 4

        item_height = 9
        total_item_height = item_height + padding

        for i in range(start_line, end_line):
            y_position = (i - start_line) * total_item_height

            if i == 0:
                menu_text = "< Back"
            else:
                item = response[i - 1]
                #menu_text = f"{parse_utc_to_finnish(item['analysis']['create_timestamp'])}"
                menu_text = f"{parse_utc_to_finnish(item)}"

            if i == index:
                oled.fill_rect(0, y_position, oled.width, item_height, 1)
                oled.text(menu_text, 0, y_position + 1 , 0)
            else:
                oled.text(menu_text, 0, y_position, 1)

        oled.show()




    def read_encoder():
        nonlocal last_clk_value, last_debounce_time, encoder_counter
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
        nonlocal last_sw_value, last_debounce_time
        sw_value = pin_sw.value()
        pressed = False
        
        if time.ticks_diff(time.ticks_ms(), last_debounce_time) > debounce_time:
            if sw_value != last_sw_value and sw_value == 0:
                last_debounce_time = time.ticks_ms()
                pressed = True
            last_sw_value = sw_value
        
        return pressed

    def update_selection(delta):
        nonlocal current_selection
        new_selection = current_selection + delta
        if 0 <= new_selection < len(response)+1:
            current_selection = new_selection
        oled_menu(current_selection)
        
    def display_analysis(history):
        nonlocal showing
        oled.fill(0)
        analysis = history['analysis']
        print(analysis['create_timestamp'])
        showing = current_selection
        
        
        TIMESTAMP = analysis['create_timestamp']
        mean_PPI = analysis['mean_rr_ms']
        mean_HR = analysis['mean_hr_bpm']
        SDNN = analysis['sdnn_ms']
        RMSSD = analysis['rmssd_ms']
#         SD1 = analysis['sd1_ms']
#         SD2 = analysis['sd2_ms']
        SNS = analysis['sns_index']
        PNS = analysis['pns_index']
        
        oled.fill_rect(0, 0, oled.width, 9, 1)
        oled.text(str(parse_utc_to_finnish(TIMESTAMP)) +'bpm', 0, 1, 0)
        oled.text('MeanHR:'+ str(int(mean_HR)) +'bpm', 0, 10, 1)
        oled.text('MeanPPI:'+ str(int(mean_PPI)) +'ms', 0, 19, 1)
        oled.text('SDNN:'+str(int(SDNN)) +'ms', 0, 28, 1)
        oled.text('RMSSD:'+str(int(RMSSD)) +'ms', 0, 37, 1)
#         oled.text('SD1:'+str(int(SD1))+' SD2:'+str(int(SD2)), 0, 36, 1)
        oled.text('SNS:%.3f' % SNS, 0, 46, 1)
        oled.text('PNS:%.3f' % PNS, 0, 55, 1)
        oled.show()
        
 
        
        
    display_multiline_text("Downloading...")
    
    body = {
        "type": "timestamps",
        "data": False
    }
        
    response_temp = Request.make_request(body)
    if response_temp == "timeout":
        display_multiline_text("Connection failed.")
        time.sleep(3)
        return
        
    response = ujson.loads(response_temp)
    oled_menu(current_selection)

    while True:
        delta = read_encoder()
        if delta:
            if showing is None:
                update_selection(delta)
        
        if encoder_button_pressed():
            if showing is not None:
                showing = None
                oled_menu(current_selection)
                time.sleep(0.3)
            else:
                if current_selection == 0:
                    return
                
                display_multiline_text("Downloading...")
                
                history_body = {
                    "type": "history",
                    "data": current_selection -1
                }
                    
                history_temp = Request.make_request(history_body)
                if history_temp == "timeout":
                    display_multiline_text("Connection Failed.")
                    time.sleep(3)
                    return
                
                history = ujson.loads(history_temp)
                display_analysis(history)

                time.sleep(0.3)
       



