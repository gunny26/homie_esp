import machine
import dht
import settings
from homie.device import HomieDevice
from homie.node import HomieNode
from homie.property import HomieNodeProperty
from homie.constants import FALSE, TRUE, BOOLEAN, FLOAT
from machine import Pin, ADC
from uasyncio import get_event_loop, sleep_ms


class DHT22(HomieNode):
    def __init__(self, name="Temp & Humid", pin=4, interval=60, pull=-1):
        super().__init__(id="dht22", name=name, type="dht22")
        self.dht22 = dht.DHT22(Pin(pin, Pin.IN, pull))
        self.interval = interval

        self.temp_property = HomieNodeProperty(
            id="temperature",
            name="Temperature",
            datatype=FLOAT,
            format="-40:80",
            unit="°C",
        )
        self.add_property(self.temp_property)

        self.hum_property = HomieNodeProperty(
            id="humidity",
            name="Humidity",
            datatype=FLOAT,
            format="0:100",
            unit="%",
        )
        self.add_property(self.hum_property)

        loop = get_event_loop()
        loop.create_task(self.update_data())

    async def update_data(self):
        dht22 = self.dht22
        delay = self.interval * 1000

        while True:
            dht22.measure()
            self.temp_property.data = dht22.temperature()
            self.hum_property.data = dht22.humidity()

            await sleep_ms(delay)


class KY018(HomieNode):
    """
    Light Sensor on ADC port
    read adc volatge level, only possible on AD port
    connecting fir extention an plus and minus, and S port to AD

    KY-018 Foto LDR Widerstand Diode Photo Resistor Sensor
    https://www.az-delivery.de/products/licht-sensor-modul?_pos=5&_sid=2af9b43b3&_ss=r
    """

    def __init__(self, name="Light Sensor", pin=0, interval=60):
        super().__init__(id="ky018", name=name, type="ky018")
        self.interval = interval
        self.adc = ADC(pin)
        self.light_property = HomieNodeProperty(
            id="light",
            name="Light",
            datatype=FLOAT,
            format="0:1023",
            unit="lum",
        )
        self.add_property(self.light_property)
        loop = get_event_loop()
        loop.create_task(self.update_data())

    def measure(self):
        """
        read adc volatge level, only possible on AD port
        connecting fir extention an plus and minus, and S port to AD

        KY-018 Foto LDR Widerstand Diode Photo Resistor Sensor
        https://www.az-delivery.de/products/licht-sensor-modul?_pos=5&_sid=2af9b43b3&_ss=r
        """
        value = self.adc.read() # analog read value
        resistence = (1023 - value) * 10 / value
        return resistence

    async def update_data(self):
        delay = self.interval * 1000
        while True:
            light = self.measure()
            self.light_property.data = light
            await sleep_ms(delay)


def main():
    # Homie device setup
    homie = HomieDevice(settings)

    # Add dht22 node
    homie.add_node(DHT22(pin=5))

    # Add ky018 node
    homie.add_node(KY018(pin=0))

    # run forever
    homie.run_forever()


if __name__ == "__main__":
    main()
