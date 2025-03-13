# PokerChips

## 01204114 Introduction to Computer Hardware Development
มหาวิทยาลัยเกษตรศาสตร์ คณะวิศวกรรมศาสตร์ ภาควิชาคอมพิวเตอร์
- นายธิติ ทรงพลวารินทร์ 6710503992 [Github](https://github.com/ThitiSo)
- นายรชตะ วัฒนานนท์  6710504298 [Github](https://github.com/tottirct)
- นายสิรภัทร ทัพภะ    6710504409 [Github](https://github.com/Siraphat-ohm)

# ที่มา
จุดเริ่มต้นของโปรเจกต์นี้เกิดมาจากการมองเห็นถึงปัญหาของผู้เล่น poker ที่ต้องใช้สมาธิส่วนหนึ่งในการดูแลและจัดสรร chips ของตัวเองในระหว่างการเล่น ซึ่งอาจทำให้เกิดความผิดพลาดในการเล่นได้

# แนวคิดการออกแบบ
อุปกรณ์นี้เป็นอุปกรณ์เพื่อช่วยอำนวยความสะดวกให้กับผู้เล่น poker ในการคำนวณและจัดสรร chips ของผู้เล่นแต่ละคน

# หลักการทำงาน

<img src="https://raw.githubusercontent.com/Siraphat-ohm/PokerChips/refs/heads/main/img/overall.png" width="45%"><img src="https://raw.githubusercontent.com/Siraphat-ohm/PokerChips/refs/heads/main/img/Dashboard.png" width="45%">


## Board 1 ( Player ) 
มีหน้าที่รับ action ของแต่ละ player ( bet, call, fold, ... ) และ แสดง chips ของ player และ pot พร้อมทั้งส่ง action ของ player ไปยัง board ของ dealer  

### Files
- [utils](https://github.com/Siraphat-ohm/PokerChips/tree/main/utils) ใน Folder นี้จะเป็นพวก utility เช่น test_oled.py ไว้ทดสอบจอตาม channel
- [const.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/const.py) ค่าคงที่ต่างๆ และ config ของแต่ละ player
- [joystick.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/joystick.y) อ่านค่าจากจอย
- [player.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/player.py) ไฟล์นี้จัดการทุกอย่างเกี่ยวกับ player เช่น วาดหน้าจอ, ส่ง action
- [poker.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/poker.py) ไฟล์นี้จัดการเกี่ยวกับ logic ของเกม poker และ ส่งค่าไปยัง mqtt
- [main.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/main.py) ไฟล์นี้โปรแกรมหลัก

## Board 2 ( Dealer )
มีหน้าที่รับข้อมูลของ player ( board 1 ) และทำหน้าที่ผลไปยัง Dashboard ( node red ) และยังมีหน้าที่ในการดูแล pot ของแต่ละรอบ

### Files
- [dealer.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/dealer.py) ไฟล์ในบอร์ด dealer ใช้ในการ setting table และ กำหนดผู้ชนะของ player ในแต่ละรอบ
- [config.py](https://github.com/Siraphat-ohm/PokerChips/blob/main/config.py) ไฟล์ config เกี่ยวกับ mqtt

# รายการอุปกรณ์
- OLED x 4
- I2C Multiplexer x 1
- 74CH4051 Multiplexer x 1
- Joystick switch x 4
- ESP32s3 x 2
- Keypad x 1

# Library

- [ssd1306](https://github.com/adafruit/Adafruit_Python_SSD1306)

# Schematic

 <img src="https://raw.githubusercontent.com/Siraphat-ohm/PokerChips/refs/heads/main/img/Schematic%20Dealer%20Board.png" width="45%"> <img src="https://raw.githubusercontent.com/Siraphat-ohm/PokerChips/refs/heads/main/img/Schematic%20Player%20Board.png" width="45%">

# Source code
- [Github](https://github.com/Siraphat-ohm/PokerChips/tree/main)
