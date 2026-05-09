# Kloc Journal

หน้าที่: บันทึก signal, TP/SL, taken/skipped

สิ่งที่ทำ:

- บันทึก signal ทุกอัน แม้ผู้ใช้ไม่ได้เทรดตาม
- track ผลลัพธ์: open, tp, tp1, sl, timeout, be
- เก็บ manual status: taken, skipped, missed, watch
- แยก journal ของ logic ปัจจุบัน ไม่ปน logic เก่า

ไฟล์หลัก:

```text
mt5_planner/journal.py
mt5_planner/tracker.py
journal_btc_current.sqlite
journal_xau_current.sqlite
```

หมายเหตุ:

- ถ้ากด mark ผิดใน dashboard ให้ใช้ปุ่ม clear หรือ mark ใหม่
- ข้อมูล manual ไม่ใช่ผล backtest แต่เป็นประวัติพฤติกรรมการเทรดจริงของผู้ใช้
