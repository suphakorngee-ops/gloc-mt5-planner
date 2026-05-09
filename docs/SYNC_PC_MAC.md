# PC / Mac Sync Guide

เป้าหมายคือให้ PC คอนโด และ Mac ออฟฟิศใช้ project เดียวกันโดยไม่ทำ journal หาย

## วิธีแนะนำ

ใช้ cloud folder เช่น OneDrive / Google Drive / iCloud Drive / Git repo ส่วนตัว

ให้ sync เฉพาะไฟล์ project หลัก:

```text
mt5_planner/
mt5_exporter/
config*.json
MT5_PLANNER.ps1
PROJECT_MEMORY.md
USER_PLAYBOOK.md
AI_RUNBOOK.md
reports/
backups/
```

## ระวัง

อย่าเปิด Live พร้อมกันหลายเครื่องบน journal เดียวกันถ้ายังไม่ได้แยก journal

ถ้าต้องเปิด PC และ Mac พร้อมกัน ให้ใช้ journal แยก:

```text
journal_btc_current_pc.sqlite
journal_btc_current_mac.sqlite
```

แล้วค่อยรวม report ภายหลัง

## MT5 Path ต่างเครื่อง

`MT5_PLANNER.ps1` ตอนนี้ path ผูกกับ PC เครื่องนี้:

```text
C:\Users\jiasny\AppData\Roaming\MetaQuotes\Terminal\...\MQL5\Files
```

บน Mac หรือ Windows อีกเครื่อง ต้องแก้ `$TerminalId` และ `$Mt5FilesDir`

## ขั้นตอนใช้งานจริง

1. ก่อนปิดเครื่อง กด `08 MAIN Backup`
2. ให้ cloud sync เสร็จ
3. เปิดอีกเครื่อง
4. เปิด project เดียวกัน
5. เช็ก path MT5/exporter
6. รัน `12 MAIN BTC Once` เพื่อทดสอบ
7. ค่อยรัน Live

