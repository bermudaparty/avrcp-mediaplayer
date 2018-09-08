from threading import Thread
import time
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

class Lcd(Adafruit_CharLCDPlate):
    BUTTON_SELECT = 1
    BUTTON_LEFT = 16
    BUTTON_RIGHT = 2
    BUTTON_UP = 8
    BUTTON_DOWN = 4

    worker = None
    polling = True
    handler = None

    def begin(self, cols, rows, handler=None):
        super(Lcd, self).begin(cols, rows)
        self.handler = handler
        if self.handler:
            self.worker = Thread(target=self.getButtons)
            self.worker.start()

    def end(self):
        self.polling = False;
        self.clear()
        self.backlight(Lcd.OFF)
        self.stop()

    def writeLn(self, str, row):
        self.setCursor(0, row)
        self.message(self.replaceAccents(str[:40].ljust(40)))

    def replaceAccents(self, str):
        return str.replace(u"\xe9", "e")

    def getButtons(self):
        button_cache = 0;
        while self.polling:
            test = self.buttons()
            buttons = test - button_cache;
            button_cache = test if test > 0 else 0
            if buttons > 0:
                self.handler(buttons)
            time.sleep(0.1)

    def wrap(self, str):
        lines = [];
        while len(str) > self.numcols:
            idx = str[:self.numcols+1].rfind(" ")
            if idx > 0:
                lines.append(str[:idx])
                str = str[idx+1:].lstrip()
            else:
                lines.append(str[:self.numcols])
                str = str[self.numcols:].lstrip()

        lines.append(str)

        return  lines



if __name__ == "__main__":
    def handleNav(buttons):
        print(buttons)

    try:
        lcd = Lcd()
        lcd.begin(16, 2, handler=handleNav)

        while True:
            time.sleep(1)
    except:
        lcd.end()