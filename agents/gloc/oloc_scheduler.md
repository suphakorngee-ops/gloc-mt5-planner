# Oloc Scheduler

หน้าที่: ปลุกงานรายรอบ เช่น save-state/report

สิ่งที่ทำตอนนี้:

- ใช้ผ่าน VSCode tasks หรือ `MT5_PLANNER.ps1`
- สั่ง live, report, daily, backup, save-state

สิ่งที่ทำได้ในอนาคต:

- Windows Task Scheduler บน PC
- cron/systemd timer บน server
- Discord bot loop ที่ปลุก Rloc/Gloc ทุก 15 นาที

งานที่เหมาะ:

```text
save-state ทุก 30-60 นาที
daily summary วันละครั้ง
backup วันละครั้ง
dashboard server ตอนเปิดเครื่อง
```

ข้อห้าม:

- ไม่ปลุก Vloc Executor ให้ส่ง order จนกว่า auto execution gate ผ่าน
