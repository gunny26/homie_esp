"""
basic homie usage example with 3 functions and sensos
- On-board LED to swithc something on and off
- DHT22 to read TEMP + Humidity
- KY018 Light Sensor to read from ADC
- KY026 Flame detector
"""
import dht
import settings
import uasyncio as asyncio

# homie modules
from machine import Pin, ADC
from primitives.pushbutton import Pushbutton
from homie.device import HomieDevice, await_ready_state
from homie.node import HomieNode
from homie.property import HomieProperty
from homie.constants import FALSE, TRUE, BOOLEAN, FLOAT


class LED(HomieNode):
    """
    ESP8266 LED - testing
    """

    # Reversed values for the esp8266 boards onboard led
    ONOFF = {FALSE: 1, TRUE: 0}

    def __init__(self, name="Onboard LED", pin=0):
        super().__init__(id="led", name=name, type="LED")
        self.led = Pin(pin, Pin.OUT, value=1)

        # Boot button on some dev boards
        self.btn = Pushbutton(Pin(pin, Pin.IN, Pin.PULL_UP))
        self.btn.press_func(self.toggle_led)

        self.p_power = HomieProperty(
            id="power",
            name="LED Power",
            settable=True,
            datatype=BOOLEAN,
            default=FALSE,
            on_message=self.on_power_msg,
        )
        self.add_property(self.p_power)

    def on_power_msg(self, topic, payload, retained):
        """
        called on_message
        """
        self.led(self.ONOFF[payload])

    def toggle_led(self):
        """
        toggle led value
        """
        if self.p_power.value == TRUE:
            self.led(1)
            self.p_power.value = False
        else:
            self.led(0)
            self.p_power.value = True


class DHT22(HomieNode):
    """
    standard DHT22 device, not much customized

    wiring for ESP8266
    DHT22 - +   -> ESP8266 V3.3
    DHT22 - OUT -> ESP8266 D1
    DHT22 - GND -> ESP8266 GND
    """

    def __init__(self, name="Temp & Humid", pin=4, interval=60, pull=-1):
        super().__init__(id="dht22", name=name, type="dht22")
        self.dht22 = dht.DHT22(Pin(pin, Pin.IN, pull))
        self.interval = interval

        self.temp_property = HomieProperty(
            id="temperature",
            name="Temperature",
            datatype=FLOAT,
            format="-40:80",
            unit="°C",
            default=0
        )
        self.add_property(self.temp_property)

        self.hum_property = HomieProperty(
            id="humidity",
            name="Humidity",
            datatype=FLOAT,
            format="0:100",
            unit="%",
        )
        self.add_property(self.hum_property)

        asyncio.create_task(self.update_data())

    @await_ready_state
    async def update_data(self):
        """
        periodically called to update property data
        """
        dht22 = self.dht22
        delay = self.interval * 1000

        while True:
            dht22.measure()
            self.temp_property.data = str(dht22.temperature()) # must be str
            self.hum_property.data = str(dht22.humidity()) # must be str
            await asyncio.sleep_ms(delay)


class KY018(HomieNode):
    """
    Light Sensor on ADC port
    read adc volatge level, only possible on AD port
    connecting fir extention an plus and minus, and S port to AD

    KY-018 Foto LDR Widerstand Diode Photo Resistor Sensor
    https://www.az-delivery.de/products/licht-sensor-modul?_pos=5&_sid=2af9b43b3&_ss=r

    wiring for ESP8266
    KY018 - S   -> ESP8266 AD0
    KY018 - +   -> ESP8266 V3.3
    KY018 - GND -> ESP8266 GND
    """

    def __init__(self, name="Light Sensor", pin=0, interval=60):
        super().__init__(id="ky018", name=name, type="ky018")
        self.interval = interval
        self.adc = ADC(pin)
        self.light_property = HomieProperty(
            id="light",
            name="Light",
            datatype=FLOAT,
            format="0:1023",
            unit="lum",
            default=0
        )
        self.add_property(self.light_property)
        asyncio.create_task(self.update_data())

    @await_ready_state
    async def update_data(self):
        """
        periodically called to update property data
        """
        delay = self.interval * 1000
        while True:
            light = self.measure()
            self.light_property.data = str(light) # must be str, otherwise mqtt error
            await asyncio.sleep_ms(delay)

    def measure(self):
        """
        read adc voltage level, only possible on AD port
        connecting fir extention an plus and minus, and S port to AD

        KY-018 Foto LDR Widerstand Diode Photo Resistor Sensor
        https://www.az-delivery.de/products/licht-sensor-modul?_pos=5&_sid=2af9b43b3&_ss=r
        """
        value = self.adc.read() # analog read value
        resistence = (1023 - value) * 10 / value
        return resistence

class KY026(HomieNode):
    """
    flame detection sensor KY-026
    read KY-026 from D2 aka GPIO5 (so use pin=5)

    wiring for ESP8266
    KY026 - D0  -> ESP8266 D2
    KY026 - +   -> ESP8266 V3.3
    KY026 - GND -> ESP8266 GND
    KY026 - A0  -> Analog not used

    KY-026 Flammensensor Modul
    https://www.az-delivery.de/collections/sensoren/products/flammensensor-modul
    """

    def __init__(self, name="Flame detector", pin=5, interval=1):
        super().__init__(id="ky026", name=name, type="KY026")
        self.interval = interval
        self.ky026 = Pin(pin, Pin.IN, pull=Pin.PULL_UP)
        self.active = True
        self.active_property = HomieProperty(
            id="active",
            name="KY026 Status",
            settable=True,
            datatype=BOOLEAN,
            restore=True,
            default=TRUE,
        )
        self.add_property(self.active_property)
        asyncio.create_task(self.update_data())

    async def update_data(self):
        """
        update measuring values
        """
        ky026 = self.ky026
        delay = self.interval * 1000
        latest = 0
        while True:
            state = ky026() # TODO: should this be .value()??
            if state != latest: # state change
                if state == 1:
                    print("flame detected")
                    # self.device.broadcast("flame detected")
                latest = state
                self.active_property.data = str(state)
            await asyncio.sleep_ms(delay)


def main():
    # Homie device setup
    homie = HomieDevice(settings)
    #print("homie DEVIDE_ID   :" + homie.DEVICE_ID)
    #print("homie DEVIDE_NAME :" + homie.DEVICE_NAME)
    #print("homie MQTT_BROKER :" + homie.MQTT_BROKER)
    #print("homie WIFI_SSID   :" + homie.WIFI_SSID)

    # Add On-board LED
    homie.add_node(LED())

    # Add dht22 node
    homie.add_node(DHT22(pin=5))

    # Add ky018 node
    homie.add_node(KY018(pin=0))

    # Add KY026 flame detection
    homie.add_node(KY026(pin=4))

    # run forever
    homie.run_forever()


if __name__ == "__main__":
    main()
