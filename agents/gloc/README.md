# Gloc Agent System

ธีม agent ของโปรเจกต์ MT5 Planner ใช้ชื่อชุดเดียวกัน:

```text
Gloc Analyst   = วิเคราะห์กราฟ / ออก signal หรือ NO TRADE
Vloc Executor  = ส่ง order ในอนาคต ตอนนี้ OFF
Kloc Journal   = บันทึก signal, TP/SL, taken/skipped
Rloc Reporter  = Discord, dashboard, report, backup
Oloc Scheduler = ปลุกงานรายรอบ เช่น save-state/report
```

สถานะตอนนี้:

```text
Gloc Analyst   = ใช้งานอยู่
Vloc Executor  = OFF / manual only / ยังไม่ส่ง order จริง
Kloc Journal   = ใช้งานอยู่
Rloc Reporter  = ใช้งานอยู่ผ่าน dashboard, report, Discord webhook
Oloc Scheduler = ใช้งานแบบ task/manual ก่อน ยังไม่ใช่ server bot เต็มตัว
```

หลักการสำคัญ:

- ทุก signal เป็น forward-test/paper signal ก่อน
- Vloc Executor ห้ามเปิด auto execution จนกว่า forward test ผ่าน gate
- ความจำหลักของระบบอยู่ในไฟล์ `.md`, config, journal SQLite และ report
- ก่อนเริ่มแชทใหม่ ให้รัน `09 MAIN Save Project State`

อ่านต่อ:

```text
PROJECT_STATE.md
PROJECT_MEMORY.md
AI_RUNBOOK.md
AGENT_ARCHITECTURE.md
```

Automation added:

```text
11 MAIN Safe Automation + Discord Digest
12 MAIN Discord Bot Dry Reply
```

Rloc Reporter can now send a safe digest through the existing Discord webhook. The prepared Discord bot router is read-only and answers status/report/daily/latest/execution-status from local files and journals. Vloc Executor remains OFF.
