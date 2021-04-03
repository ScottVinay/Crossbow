import machine as M
from machine import Pin
import utime

class Button():
    def __init__(self, gpio, pulldownup='down'):
        if pulldownup.lower()=='down': mode = Pin.PULL_DOWN
        elif pulldownup.lower()=='up': mode = Pin.PULL_UP
        else: raise NotImplementedError
        self.button = Pin(gpio, Pin.IN, mode)
        
    def pressed(self):
        return self.button.value()
    
class Light():
    def __init__(self, gpio=25):
        self.led = Pin(gpio, Pin.OUT)
        self.off()
        
    def on(self):
        self.led.value(1)
        
    def off(self):
        self.led.value(0)

class Gun():
    def __init__(self, gpio, min_delay_s=1):
        self.pwm = M.PWM(Pin(0, Pin.OUT))
        self.pwm.freq(50)
        self.MINPULSE = 500_000
        self.MAXPULSE = 2500_000
        self.shot_time = utime.ticks_ms()
        self.min_delay_s = min_delay_s
        
    def a2p(self, angle):
        # Angle-to-pulse
        pulse_diff = self.MAXPULSE - self.MINPULSE
        pulse_per_degree = pulse_diff/180
        pulse = pulse_per_degree * angle
        pulse = pulse + self.MINPULSE
        return int(pulse)

    def turn_to(self, angle):
        self.pwm.duty_ns(self.a2p(angle))
        
    def fire(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.shot_time) >= self.min_delay_s*1000:
            self.turn_to(200)
            utime.sleep_ms(650)
            self.turn_to(160)
            self.shot_time = now
        
    def reset(self):
        self.turn_to(160)
        
class USS():
    def __init__(self, gpio_trig, gpio_echo, prep=None, active=None):
        self.SOS = 0.344
        self.trig = Pin(gpio_trig, Pin.OUT)
        self.echo = Pin(gpio_echo, Pin.IN)
        if prep is not None:
            self.prep = prep
        if active is not None:
            self.active = active
    
    def dist(self, verbose=False):
        self.trig.low()
        utime.sleep_us(20)
        self.trig.high()
        utime.sleep_us(10)
        self.trig.low()
        
        delaytime = utime.ticks_us()
        receivetime = utime.ticks_us()
        
        loopcount = 0
        exitloop = 0
        
        while self.echo.value()==0 and exitloop==0:
            loopcount += 1
            delaytime = utime.ticks_us()
            if loopcount > 3000: exitloop=1
            
        while self.echo.value()==1 and exitloop==0:
            loopcount += 1
            receivetime = utime.ticks_us()
            if loopcount > 3000: exitloop=1
        
        if exitloop: return 0
        
        distance = utime.ticks_diff(receivetime, delaytime)*self.SOS/2
            
        return distance
        
    def get_rest_dist(self, wait=5, verbose=False):
        if hasattr(self, 'prep'): self.prep.on()
        
        distances = []
        for i in range(wait*4):
            distances.append(self.dist(verbose=verbose))
            utime.sleep_ms(250)
        distances = distances[:2*(len(distances)//2)]
        distances = sorted(distances)
        rest_dist = distances[int((len(distances)+1)/2)]

        if hasattr(self, 'prep'): self.prep.off()
        
        return rest_dist
            

def main():
    but = Button(1)
    led = Light(25)
    gun = Gun(0, min_delay_s = 1)
    red = Light(16)
    grn = Light(17)
    uss = USS(14, 15, prep=grn)
    
    gun.reset()
    rest_dist = uss.get_rest_dist(2, verbose=True)
    
    consecutive = 0
    
    while True:
        if but.pressed():
            print('.')
        if uss.dist()<rest_dist * 0.2:
            consecutive +=1
        else:
            consecutive = 0
            gun.ready = 1
        
        if consecutive>=3 or but.pressed():
            red.on()
            gun.fire()
            gun.ready = 0
        else:
            red.off()
            
main()
    
    
    
    
    
    
    
    
    
    