from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C, PWM
from fifo import Fifo
import utime
import array
import time
import network
import socket
import urequests as requests
import ujson
from functions import *
from calculate import *
import Request

def hrv(variant, duration):

    
                                                    #                    GPIO Pins                     #

    # ADC-converter
    adc = ADC(26)


    # OLED
    i2c = I2C(1, scl = Pin(15), sda = Pin(14))
    oled = SSD1306_I2C(128, 64, i2c)

    # LEDs
    led_onboard = Pin("LED", Pin.OUT)
    led21 = PWM(Pin(21))
    led21.freq(1000)

    # Rotary Encoder
    rot_push = Pin(12, mode = Pin.IN, pull = Pin.PULL_UP)
    

                                                    #                     Variables                    #


    # Sample Rate, Buffer
    samplerate = 250
    samples = Fifo(32)

    # Menu selection variables and switch filtering
    mode = 0
    count = 0
    switch_state = 0
    running = True
    
    beat = False
    beat_start_time = None


                                                    #                  Maim Program                  #
                                                    
                                                    
    avg_size = 128	# originally: int(samplerate * 0.5)
    buffer = array.array('H',[0]*avg_size)
    
    def read_adc(tid):
        x = adc.read_u16()
        samples.put(x)
        
    def draw_heart():
        if beat == True:
            size = 2
        else:
            size = 1
    
        heart_pattern = [
            (1, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
            (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3),
            (2, 4)
        ]


        s_x, s_y = 4, 2
        b_x, b_y = 2, 0


        x_offset, y_offset = (s_x, s_y) if size == 1 else (b_x, b_y)


        for dx, dy in heart_pattern:
            oled.pixel(b_x + dx * 2, b_y + dy * 2, 0)
            oled.pixel(s_x + dx * 1, s_y + dy * 1, 0)


        for dx, dy in heart_pattern:
            oled.pixel(x_offset + dx * size, y_offset + dy * size, 1)
            
    def dynamic_erase_bounds(current_x, erase_width, display_width):
        erase_start = max(current_x - erase_width, 0)
        erase_end = min(current_x + erase_width, display_width - 1) 


        if current_x > display_width - erase_width:

            additional_erase_start = display_width - erase_width
            additional_erase_end = display_width - 1
            return erase_start, erase_end, additional_erase_start, additional_erase_end
        else:
            return erase_start, erase_end, None, None 


    while running:
        press_to_start()
        new_state = rot_push.value()

        if new_state != switch_state:
            count += 1
            if count > 3:
                if new_state == 0:
                    if mode == 0:
                        mode = 1
                    else:
                        mode = 0
                switch_state = new_state
                count = 0
        else:
            count = 0
        utime.sleep(0.01)
        
        if mode == 1:
            count = 0
            switch_state = 0

            oled.fill(0)
            oled.show()
            
            x1 = -1
            y1 = 32
            m0 = 65535 / 2
            a = 1 / 10

            disp_div = samplerate / 25
            disp_count = 0
            capture_length = samplerate * (int(duration) if duration is not None else 9999)


            index = 0
            capture_count = 0
            subtract_old_sample = 0
            sample_sum = 0

            min_bpm = 30
            max_bpm = 200
            sample_peak = 0
            sample_index = 0
            previous_peak = 0
            previous_index = 0
            interval_ms = 0
            PPI_array = []
            
            brightness = 0
            tmr = Timer(freq = samplerate, callback = read_adc)
            

            #   Plotting the signal, Sampling   #
            
            while capture_count < capture_length and running is not False:
                
                new_state = rot_push.value()

                if new_state != switch_state:
                    count += 1
                    if count > 3:
                        if new_state == 0:
                            running = False
                            led_onboard.value(0)
                            return
                        switch_state = new_state
                        count = 0
                else:
                    count = 0
                if not samples.empty():
                    x = samples.get()
                   
                    disp_count += 1
                    
                    
            
                    if disp_count >= disp_div:
                        disp_count = 0
                        m0 = (1 - a) * m0 + a * x
                        y2 = int(32 * (m0 - x) / 14000 + 35)
                        y2 = max(10, min(53, y2))
                        x2 = x1 + 1
                        
                        oled.fill_rect(0, 0, 128, 9, 0)
                   
                        if len(PPI_array) > 3:
                            actual_PPI = meanPPI_calculator(PPI_array)
                            actual_HR = meanHR_calculator(actual_PPI)
                            oled.text(f'{actual_HR}', 15, 1, 1)
#                             oled.text(f'PPI:{interval_ms}', 60, 1, 1)
                        #oled.text(f'{int((capture_length - capture_count)/samplerate)}s', 90, 1, 1)
                        
                        text = f'{int((capture_length - capture_count)/samplerate)}s'
                        char_width = 8 
                        display_width = oled.width 
                        text_width = len(text) * char_width
                        x_position = display_width - text_width
                        
                        if duration is not None:
                            oled.text(text, x_position, 1, 1)

                        erase_width = 64 
                        erase_start, erase_end, additional_erase_start, additional_erase_end = dynamic_erase_bounds(x2, erase_width, 128)

                        oled.line(erase_start, 15, erase_start, 73, 0)
                        oled.line(erase_end, 15, erase_end, 73, 0)

                        if additional_erase_start is not None and additional_erase_end is not None:
                            oled.line(additional_erase_start, 0, additional_erase_end, 73, 0)
                        oled.line(x1, y1+10, x2, y2+10, 1)
                        draw_heart()
                        oled.show()
                       
                        x1 = x2
                        if x1 > 127:
                            x1 = -1
                        y1 = y2

                    if subtract_old_sample:
                        old_sample = buffer[index]
                    else:
                        old_sample = 0
                    sample_sum = sample_sum + x - old_sample

                    #   Peak Detection   #

                    if subtract_old_sample:
                        sample_avg = sample_sum / avg_size
                        sample_val = x
                        if sample_val > (sample_avg * 1.03):
                            if sample_val > sample_peak:
                                sample_peak = sample_val
                                sample_index = capture_count

                        else:
                            if sample_peak > 0:
                                if (sample_index - previous_index) > (60 * samplerate / min_bpm):
                                    previous_peak = 0
                                    previous_index = sample_index
                                else:
                                    if sample_peak >= (previous_peak*0.7):
                                        if (sample_index - previous_index) > (60 * samplerate / max_bpm):
                                            if previous_peak > 0:
                                                interval = sample_index - previous_index
                                                interval_ms = int(interval * 1000 / samplerate)
                                                PPI_array.append(interval_ms)
                                                beat = True
                                                beat_start_time = time.ticks_ms()
  
                                            previous_peak = sample_peak
                                            previous_index = sample_index
                            sample_peak = 0
                            
                        if beat and beat_start_time is not None and PPI_array:
                            last_ppi_duration = int(PPI_array[-1])  # Get the last PPI value as the duration
                            if time.ticks_diff(time.ticks_ms(), beat_start_time) > 200:
                                beat = False
                            

                        if brightness > 0:
                            brightness -= 1
                        else:
                            led21.duty_u16(0)

                    buffer[index] = x
                    capture_count += 1
                    index += 1
                    if index >= avg_size:
                        index = 0
                        subtract_old_sample = 1
            

            tmr.deinit()
           
            
            while not samples.empty():
                x = samples.get()


            #   HRV calculation   #
            

            oled.fill(0)

       
            text = "Processing..."
            text_width = len(text) * 8  
            x_position = (oled.width - text_width) // 2 
            y_position = oled.height // 2 - 4
            
            oled.text(text, x_position, y_position, 1) 
            
            oled.show()
            oled.fill(0)
            
            if len(PPI_array) >= 3:
                
                
                if variant == "kubios":
                    
                    body = {
                        "type": "kubios",
                        "data": PPI_array
                    }
                    
                    response = Request.make_request(body)
                    print(response)
                    response_dict = ujson.loads(response)
                    analysis = response_dict['analysis']
                    
                    mean_PPI = analysis['mean_rr_ms']
                    mean_HR = analysis['mean_hr_bpm']
                    SDNN = analysis['sdnn_ms']
                    RMSSD = analysis['rmssd_ms']
                    SD1 = analysis['sd1_ms']
                    SD2 = analysis['sd2_ms']
                    SNS = analysis['sns_index']
                    PNS = analysis['pns_index']
                 
                    oled.text('MeanHR:'+ str(int(mean_HR)) +'bpm', 0, 0, 1)
                    oled.text('MeanPPI:'+ str(int(mean_PPI)) +'ms', 0, 9, 1)
                    oled.text('SDNN:'+str(int(SDNN)) +'ms', 0, 18, 1)
                    oled.text('RMSSD:'+str(int(RMSSD)) +'ms', 0, 27, 1)
                    oled.text('SD1:'+str(int(SD1))+' SD2:'+str(int(SD2)), 0, 36, 1)
                    oled.text('SNS:%.3f' % SNS, 0, 45, 1)
                    oled.text('PNS:%.3f' % PNS, 0, 54, 1)
                
                else:
        
                    mean_PPI = meanPPI_calculator(PPI_array)
                    mean_HR = meanHR_calculator(mean_PPI)
                    SDNN = SDNN_calculator(PPI_array, mean_PPI)
                    RMSSD = RMSSD_calculator(PPI_array)
                    SDSD = SDSD_calculator(PPI_array)
                    SD1 = SD1_calculator(SDSD)
                    SD2 = SD2_calculator(SDNN, SDSD)
                 
                    oled.text('MeanPPI:'+ str(int(mean_PPI)) +'ms', 0, 0, 1)
                    oled.text('MeanHR:'+ str(int(mean_HR)) +'bpm', 0, 9, 1)
                    oled.text('SDNN:'+str(int(SDNN)) +'ms', 0, 18, 1)
                    oled.text('RMSSD:'+str(int(RMSSD)) +'ms', 0, 27, 1)
                    oled.text('SD1:'+str(int(SD1))+' SD2:'+str(int(SD2)), 0, 36, 1)
                    
            else:
                
                oled.text('Error', 45, 10, 1)
                oled.text('Please restart', 8, 30, 1)
                oled.text('measurement', 20, 40, 1)
                
            oled.show()
            
            while mode == 1:
                new_state = rot_push.value()
                if new_state != switch_state:
                    count += 1
                    if count > 3:
                        if new_state == 0:
                            if mode == 0:
                                mode = 1
                            else:
                                mode = 0
                                running = False
                            led_onboard.value(1)
                            time.sleep(0.15)
                            led_onboard.value(0)
                        switch_state = new_state
                        count = 0
                else:
                    count = 0
                utime.sleep(0.01)






