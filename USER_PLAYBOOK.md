# MT5 Planner User Playbook

## Current Simple Task List

Visible VSCode tasks are now simplified:

```text
01 Gloc BTC Live              = weekend/crypto forward test
02 Gloc XAU Live Weekdays     = XAU forward test when gold market is open
03 Gloc Dashboard Live        = local dashboard server
04 Gloc Safe Automation       = report + daily + save-state + backup + Discord digest
05 Gloc Report All            = forward progress report
06 Gloc Daily Summary All     = daily summary files
07 Gloc Execution Status      = confirm auto execution is OFF
08 Gloc Dashboard Open        = build/open static dashboard
```

XAUUSD/gold is normally closed on Saturday and Sunday. On weekends, use BTC live/report instead and leave XAU live off.

Old `.bat` launchers were moved to `scripts/legacy_launchers/` to keep the root folder clean. Use `START_HERE.bat`, `MT5_PLANNER.ps1`, or the visible VSCode tasks for normal work.

Forward reports show both raw `signals` and grouped `trade ideas`. The grouped number is better for judging edge because repeated refreshes of the same setup are counted as one idea.

If a Discord/terminal alert is missed, run `09 Gloc Resend Latest Signal`. Every saved alert is also kept in `reports/alerts.log`, and new alerts are appended to `reports/signal_inbox.txt`.

คู่มือนี้สำหรับคุณ ใช้ตอนเปิดเครื่องแล้วไม่อยากจำขั้นตอนเยอะ

## ตอนนี้ระบบคืออะไร

- ยังเป็น `FORWARD TEST / PAPER SIGNAL`
- ยังไม่ส่ง order จริง
- ถ้ามี signal คุณจะเข้า demo เองก็ได้ หรือไม่เข้าก็ได้
- ถ้าไม่ทัน ห้ามไล่ราคา ให้ปล่อยระบบ track paper result
- เป้าหมายตอนนี้คือเก็บ `50-100 signals` ต่อ symbol

## ใช้อะไรตอนตลาดไหน

### ทองปิด

ใช้ BTC ก่อน:

```text
MAIN BTC Live
MAIN BTC Report
MAIN BTC Daily Summary
```

### ทองเปิด

ใช้ XAU ได้:

```text
MAIN XAU Live
MAIN XAU Report
MAIN XAU Daily Summary
```

## ใช้งานใน VSCode

1. กด `Ctrl + Shift + P`
2. พิมพ์ `Tasks: Run Task`
3. เลือก task

ใช้บ่อย:

```text
MAIN BTC Live       = เปิดเก็บ BTC signal
MAIN BTC Report     = ดูครบ 50/100 signals หรือยัง
MAIN BTC Daily      = สรุปรายวัน

MAIN XAU Live       = เปิดเก็บ XAU signal ตอนตลาดทองเปิด
MAIN XAU Report     = ดูครบ 50/100 signals หรือยัง
MAIN XAU Daily      = สรุปรายวัน
```

## ถ้ามี Signal ขึ้น ต้องเข้าไหม

ไม่จำเป็น

ให้ดู 3 อย่างก่อน:

```text
$risk
entry / sl / tp
WAIT PLAN หรือ reason
```

ถ้าราคาเลย entry ไปมากแล้ว ให้ข้าม

กฎตอนนี้:

```text
ไม่ไล่ราคาเกิน 2 แท่ง M5
```

## Demo USD กับ Real Cent

ตอนนี้ VSCode task ใช้ demo USD เป็นหลัก

Demo config:

```text
config.json
config_btc.json
```

Real cent config:

```text
config_xau_cent.json
config_btc_cent.json
```

ตอนจะใช้ real cent ค่อยรันผ่าน terminal แบบนี้:

```powershell
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol btc -Account cent -Action live
powershell -ExecutionPolicy Bypass -File MT5_PLANNER.ps1 -Symbol xau -Account cent -Action live
```

## Clean Journal

ผลของ logic ปัจจุบันเก็บในไฟล์ใหม่:

```text
XAU demo = journal_xau_current.sqlite
BTC demo = journal_btc_current.sqlite
XAU cent = journal_xau_cent.sqlite
BTC cent = journal_btc_cent.sqlite
```

ไฟล์เก่าเป็น archive:

```text
journal.sqlite
journal_btc.sqlite
```

## เมื่อไหร่ค่อยคิดเรื่อง Auto Trade

ยังไม่ใช่ตอนนี้

ต้องผ่านก่อน:

```text
50 signals  = เริ่มประเมิน
100 signals = ค่อยพิจารณา auto demo/cent
forward expectancy เป็นบวก
profit factor มากกว่า 1.3
มี daily max loss
มี max open trades
```

## Reports, Alerts, Dashboard

Files created by the system:

```text
reports/daily_btc.txt
reports/daily_xau.txt
reports/dashboard.html
reports/alerts.log
reports/latest_signal.txt
```

Use:

```text
MAIN BTC Daily Summary
MAIN XAU Daily Summary
05 MAIN Dashboard Open
```

When a new signal is saved, the planner can beep, print `NEW SIGNAL`, and write the alert into `reports/alerts.log`.

## BTC Demo Auto Execution

BTC demo auto execution is now available through Vloc Executor.

Current BTC setting:

```text
enabled: true
mode: demo_auto
dry_run: false
demo_only: true
fixed_lot: 0.01
max_open_trades: 1
daily_max_loss_usd: 5
```

XAU remains OFF.

Check:

```text
MAIN BTC Execution Status
MAIN XAU Execution Status
```

Correct current status:

```text
enabled: False
mode: manual_only
```

## Manual Trade Journal

ดู signal ล่าสุดเพื่อจดว่าเข้าเองหรือข้าม:

```text
08 MAIN BTC Manual List
09 MAIN XAU Manual List
```

ถ้าต้อง mark มือเองผ่าน terminal:

```powershell
python -m mt5_planner manual-mark --config config_btc.json --id 1 --status taken --entry 80300 --note "demo entry"
python -m mt5_planner manual-mark --config config_btc.json --id 1 --status skipped --note "missed entry"
```

สถานะที่ใช้ได้:

```text
taken
skipped
missed
watch
```

## Backup

กด:

```text
07 MAIN Backup
```

ระบบจะเก็บ config, memory, playbook, journal ลง:

```text
backups/YYYYMMDD_HHMMSS/
```

## Live Dashboard Server

ใช้ task:

```text
07 MAIN Dashboard Live Server
```

แล้วเปิด:

```text
http://127.0.0.1:8765
```

หน้านี้ดึงข้อมูลจาก journal สดทุก 5 วินาที และมีปุ่ม:

```text
taken
skipped
missed
watch
```

## Guard Lock

ใช้สำหรับล็อกไม่ให้ future auto execution ทำงานในวันนั้น แม้ตอนนี้ auto ยังปิดอยู่

```text
11 MAIN Guard Lock All
12 MAIN Guard Unlock All
06 MAIN Execution Status All
```

สถานะปกติตอนนี้:

```text
enabled: False
daily_locked: False
```

## Project State สำหรับลดการกิน token

ใช้:

```text
09 MAIN Save Project State
```

ระบบจะสร้าง/อัปเดต:

```text
PROJECT_STATE.md
```

ไฟล์นี้เป็นสรุปล่าสุดของโปรเจกต์ ให้ AI/แชทใหม่อ่านต่อได้เร็วขึ้น ไม่ต้องไล่ทั้งแชทยาว ๆ

## Discord Alert

อ่าน:

```text
DISCORD_ALERT_SETUP.md
```

ค่าเริ่มต้นยังปิดอยู่ ต้องใส่ Discord webhook และเปิด:

```json
"discord": {
  "enabled": true,
  "webhook_url": ""
}
```

แนะนำให้ใส่ webhook ผ่าน environment variable:

```powershell
$env:MT5_PLANNER_DISCORD_WEBHOOK="..."
```

## Agent Architecture

อ่าน:

```text
AGENT_ARCHITECTURE.md
```

ระบบแบ่งได้เป็น 4 agent:

```text
Analyst Agent
Execution Agent
Journal Agent
Report Agent
```

## Dashboard ดูยังไง

ใน VSCode:

```text
Tasks: Run Task
05 MAIN Dashboard Open
```

ระบบจะสร้าง/เปิด:

```text
reports/dashboard.html
```

ถ้าไม่เปิดอัตโนมัติ ให้เปิดไฟล์นี้เองจากโฟลเดอร์ `reports`

## Alert ขึ้นยังไง

เมื่อมี signal ใหม่:

- terminal จะ beep
- terminal จะพิมพ์ `NEW SIGNAL`
- บันทึกลง `reports/alerts.log`
- signal ล่าสุดอยู่ที่ `reports/latest_signal.txt`

Alert จะขึ้นเฉพาะตอนมี signal ที่ถูก save ใหม่ ไม่ขึ้นทุกครั้งที่หน้าจอ refresh
