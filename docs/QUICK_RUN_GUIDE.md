# MT5 Planner Quick Run Guide

## Simplified VSCode Tasks

```text
LIVE 01 / BTC Demo Auto
LIVE 02 / XAU Weekdays
DASH 01 / Live View
OPS 01 / Safe Automation
REPORT 01 / Forward All
REPORT 02 / Daily All
EXEC 01 / Status All
EXEC 04 / Order Ledger All
DASH 02 / Open Static
```

XAUUSD/gold is normally closed on Saturday and Sunday. On weekends, run BTC tasks only.

Old `.bat` launchers are archived in `scripts/legacy_launchers/`. The current main entrypoints are `START_HERE.bat`, `MT5_PLANNER.ps1`, and the visible VSCode tasks.

## ตอนนี้ควรเปิดอะไร

### ตลาดทองปิด

ใช้ BTC ก่อน:

```text
MAIN BTC Live
MAIN BTC Report
MAIN BTC Daily Summary
```

### ตลาดทองเปิด

ใช้ XAU ได้:

```text
MAIN XAU Live
MAIN XAU Report
MAIN XAU Daily Summary
```

## ความหมายของ task

```text
Live     = เปิดดูกราฟต่อเนื่อง + เก็บ paper forward signals
Once     = เช็กครั้งเดียว
Report   = ดูครบ 50/100 signals หรือยัง
Daily    = สรุปรายวัน 7 วันล่าสุด
Backtest = ทดสอบย้อนหลัง + วิเคราะห์ผล
```

## Demo USD กับ Real Cent

ค่าเริ่มต้นใน VSCode tasks คือ demo USD:

```text
config.json
config_btc.json
```

ไฟล์ real cent แยกไว้แล้ว:

```text
config_xau_cent.json
config_btc_cent.json
```

ถ้าจะรัน cent ผ่าน terminal:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Account cent -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Account cent -Action live
```

## กฎตอนนี้

- ยังเป็น forward test / paper signal
- ไม่ต้องเข้าเองทุกไม้
- ถ้าไม่ทัน อย่าไล่ราคา
- ดู `$risk` ทุกครั้งก่อนเข้า manual demo
- ระบบจะเตือนถ้า `$risk` เกิน limit

## Clean Journal คืออะไร

Journal คือสมุดบันทึก signal/result

Clean journal คือแยกสมุดใหม่สำหรับ logic ปัจจุบัน เพื่อไม่ให้สัญญาณเก่าจากเวอร์ชันก่อนปนกับผลใหม่

ตอนนี้แยก journal ใหม่แล้ว:

```text
XAU demo current = journal_xau_current.sqlite
BTC demo current = journal_btc_current.sqlite
XAU cent         = journal_xau_cent.sqlite
BTC cent         = journal_btc_cent.sqlite
```

ไฟล์เก่า:

```text
journal.sqlite
journal_btc.sqlite
```

ยังเก็บไว้เป็น archive แต่ task หลักไม่ใช้แล้ว
