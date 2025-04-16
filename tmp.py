import pyautogui
import time

print('start')
time.sleep(5)   

for i in range(20):
    print(i)    
    pyautogui.press('pagedown')
    time.sleep(2)