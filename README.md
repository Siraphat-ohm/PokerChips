# PokerChips

## 01204114 Introduction to Computer Hardware Development
มหาวิทยาลัยเกษตรศาสตร์ คณะวิศวกรรมศาสตร์ ภาควิชาคอมพิวเตอร์
- นายธิติ ทรงพลวารินทร์ 6710503992
- นายรชตะ วัฒนานนท์  6710504298
- นายสิรภัทร ทัพภะ    6710504409


# ที่มา
จุดเริ่มต้นของโปรเจกต์นี้เกิดมาจากการมองเห็นถึงปัญหาของผู้เล่น poker ที่ต้องใช้สมาธิส่วนหนึ่งในการดูแลและจัดสรร chips ของตัวเองในระหว่างการเล่น ซึ่งอาจทำให้เกิดความผิดพลาดในการเล่นได้

# แนวคิดการออกแบบ
อุปกรณ์นี้เป็นอุปกรณ์เพื่อช่วยอำนวยความสะดวกให้กับผู้เล่น poker ในการคำนวณและจัดสรร chips ของผู้เล่นแต่ละคน

# หลักการทำงาน

<img src="https://raw.githubusercontent.com/Siraphat-ohm/PokerChips/refs/heads/main/img/overall.png" width="45%">

## Board 1 ( Player ) 
มีหน้าที่รับ action ของแต่ละ player ( bet, call, fold, ... ) และ แสดง chips ของ player และ pod พร้อมทั้งส่ง action ของ player ไปยัง board ของ dealer  

## Board 2 ( Dealer )
มีหน้าที่รับข้อมูลของ player ( board 1 ) และทำหน้าที่ผลไปยัง Dashboard ( node red ) และยังมีหน้าที่ในการดูแล pot ของแต่ละรอบ

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
