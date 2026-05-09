# Vloc Executor

หน้าที่: ส่ง order ในอนาคต ตอนนี้ `OFF`

สถานะปัจจุบัน:

```text
execution.enabled = false
mode = manual_only
no live order sender
```

งานที่ทำได้ตอนนี้:

- แสดง execution status
- ตรวจ daily lock file
- ตรวจ duplicate guard path
- เตือนว่า auto execution ยังปิดอยู่

งานในอนาคต:

- รับเฉพาะ signal จาก Gloc Analyst
- ตรวจ risk guard, duplicate, daily lock, max open trades
- ส่ง order ไป MT5 เฉพาะ demo/cent
- บันทึกผลกลับให้ Kloc Journal

ข้อห้าม:

- ห้ามเปิดเองก่อน forward test ผ่าน
- ห้ามส่ง order จาก Discord โดยตรง
- ห้ามให้ model หลายตัวมีสิทธิ์ส่ง order พร้อมกัน

ไฟล์หลัก:

```text
mt5_planner/execution.py
guards/
```
