# MT5 Planner Agent Architecture

เป้าหมายคือแยกหน้าที่เป็นหลาย agent เพื่อให้ระบบไม่ปนกัน ลด token ในแชทยาว และต่อยอดไป Discord/server ได้ง่ายขึ้น

## Agent Map

```text
Gloc Analyst   = วิเคราะห์กราฟ / ออก signal หรือ NO TRADE
Vloc Executor  = ส่ง order ในอนาคต ตอนนี้ OFF
Kloc Journal   = บันทึก signal, TP/SL, taken/skipped
Rloc Reporter  = Discord, dashboard, report, backup
Oloc Scheduler = ปลุกงานรายรอบ เช่น save-state/report
```

## Gloc Analyst

หน้าที่:

- อ่าน CSV จาก MT5 exporter
- วิเคราะห์ market structure / SMC / Fibo / risk
- สร้างผลลัพธ์ `NO TRADE` หรือ signal
- ไม่ส่ง order

ไฟล์:

```text
mt5_planner/strategy.py
mt5_planner/market_features.py
mt5_planner/quality.py
mt5_planner/terminal.py
agents/gloc/gloc_analyst.md
```

## Vloc Executor

หน้าที่ในอนาคต:

- รับเฉพาะ signal ที่ผ่านจาก Gloc Analyst
- ตรวจ guard ก่อนส่ง order
- เช็ก daily lock, duplicate signal, max open trades, max daily loss
- ส่ง order เฉพาะ demo/cent เมื่อ forward test ผ่าน

สถานะตอนนี้:

```text
OFF
manual_only
ยังไม่มี live order sender
```

ไฟล์:

```text
mt5_planner/execution.py
guards/
agents/gloc/vloc_executor.md
```

## Kloc Journal

หน้าที่:

- บันทึก signal ทุกอัน แม้ผู้ใช้ไม่ได้เทรดตาม
- track ว่า TP/SL/timeout/open
- จด manual status: taken/skipped/missed/watch
- แยก clean journal ของ logic ปัจจุบัน

ไฟล์:

```text
mt5_planner/journal.py
mt5_planner/tracker.py
journal_btc_current.sqlite
journal_xau_current.sqlite
agents/gloc/kloc_journal.md
```

## Rloc Reporter

หน้าที่:

- ส่ง Discord alert
- สร้าง dashboard
- สร้าง daily summary / forward report
- backup ไฟล์สำคัญ
- save project state

ไฟล์:

```text
mt5_planner/alerts.py
mt5_planner/forward_report.py
mt5_planner/daily_report.py
mt5_planner/dashboard.py
mt5_planner/dashboard_server.py
mt5_planner/project_state.py
mt5_planner/backup.py
agents/gloc/rloc_reporter.md
```

## Oloc Scheduler

หน้าที่:

- ปลุกงานเป็นรอบ เช่น report, backup, save-state
- ตอนนี้ใช้ผ่าน VSCode task/manual ก่อน
- อนาคตใช้ Windows Task Scheduler, server cron, หรือ Discord bot loop ได้

ไฟล์:

```text
MT5_PLANNER.ps1
.vscode/tasks.json
agents/gloc/oloc_scheduler.md
```

## Data Flow

```text
MT5 Exporter
  -> CSV
  -> Gloc Analyst
  -> Kloc Journal
  -> Rloc Reporter / Discord / Dashboard
  -> Vloc Executor remains OFF until forward test passes
  -> Oloc Scheduler triggers repeated jobs
```

## Discord Server Future

Webhook ที่ใช้อยู่ตอนนี้ส่งข้อความออกได้อย่างเดียว

ถ้าอยากพิมพ์ถามใน Discord แล้วให้ตอบกลับ ต้องเพิ่ม Discord Bot ตัวจริง:

```text
Discord message/slash command
  -> Rloc Discord Bot
  -> read journals/reports/project state
  -> optionally ask Gloc Analyst for latest status
  -> reply in Discord
```

คำสั่งที่ควรทำได้ในอนาคต:

```text
/status
/signals btc
/signals xau
/report
/daily
/mark <id> <taken|skipped|missed|watch>
/lock
/unlock
/save-state
```

คำสั่ง order เช่น `/buy` หรือ `/sell` ยังไม่ควรเปิดจนกว่า Vloc Executor ผ่าน gate

## Multi-Model Future

ทำได้โดยเพิ่ม model router:

```text
Gemma/Gemini = สรุป, จัดข้อมูล, clean journal notes
GPT          = วิเคราะห์ภาพรวม, ตัดสินใจเชิงระบบ, coding, review
Local files  = memory กลางที่ทุก model อ่าน/เขียน
```

ข้อสำคัญ:

- ห้ามให้หลาย model ส่ง order เองโดยตรง
- ให้ทุก model เขียนผลลงไฟล์/report ก่อน
- Vloc Executor เป็นจุดเดียวที่มีสิทธิ์ส่ง order และตอนนี้ OFF

## Why This Is Different From A Normal EA Bot

EA bot ปกติ:

```text
signal -> order immediately
```

ระบบนี้:

```text
signal -> journal -> alert/report/dashboard -> user marks taken/skipped -> evaluate edge -> only later consider execution
```

## Auto Execution Gate

เปิด Vloc Executor ได้ก็ต่อเมื่อ:

```text
50-100 current forward signals
positive expectancy
profit factor > 1.3
daily max loss implemented
max open trades implemented
duplicate order guard implemented
demo/cent only flag implemented
```
