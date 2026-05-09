# Rloc Reporter

หน้าที่: Discord, dashboard, report, backup

สิ่งที่ทำ:

- ส่ง Discord alert เมื่อมี signal ใหม่
- สร้าง live dashboard
- สร้าง forward report และ daily summary
- backup ไฟล์สำคัญ
- save project state เพื่อให้แชทใหม่อ่านต่อได้

ไฟล์หลัก:

```text
mt5_planner/alerts.py
mt5_planner/forward_report.py
mt5_planner/daily_report.py
mt5_planner/dashboard.py
mt5_planner/dashboard_server.py
mt5_planner/project_state.py
mt5_planner/backup.py
```

Discord ตอนนี้:

- ใช้ webhook สำหรับส่งออกอย่างเดียว
- ถ้าจะพิมพ์ถามแล้วให้ตอบ ต้องเพิ่ม Discord Bot จริงในอนาคต
