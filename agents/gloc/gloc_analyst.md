# Gloc Analyst

หน้าที่: วิเคราะห์กราฟและออกผลลัพธ์ `SIGNAL` หรือ `NO TRADE`

สิ่งที่ทำ:

- อ่านข้อมูล CSV จาก MT5 exporter
- วิเคราะห์ structure, SMC, Fibo, spread, risk, session
- สร้าง entry / SL / TP / RR เมื่อมี setup
- อธิบายเหตุผลใน terminal และ dashboard

ข้อห้าม:

- ไม่ส่ง order
- ไม่แก้ manual journal
- ไม่เปิด auto execution

ไฟล์หลัก:

```text
mt5_planner/strategy.py
mt5_planner/market_features.py
mt5_planner/quality.py
mt5_planner/terminal.py
```
