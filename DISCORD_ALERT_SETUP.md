# Discord Alert Setup

ระบบรองรับ Discord webhook แล้ว แต่ค่าเริ่มต้นยังปิดอยู่

## วิธีสร้าง Webhook ใน Discord

1. เปิด Discord server/channel ที่ต้องการรับ alert
2. Channel Settings
3. Integrations
4. Webhooks
5. New Webhook
6. Copy Webhook URL

## วิธีเปิดแบบไม่ใส่ secret ลง config

ใน PowerShell ก่อนรัน Live:

```powershell
$env:MT5_PLANNER_DISCORD_WEBHOOK="PASTE_WEBHOOK_URL_HERE"
```

แล้วแก้ใน `config_btc.json` หรือ `config.json`:

```json
"discord": {
  "enabled": true,
  "webhook_url": ""
}
```

ระบบจะอ่าน webhook จาก environment variable:

```text
MT5_PLANNER_DISCORD_WEBHOOK
```

## วิธีเปิดแบบใส่ใน config

ไม่แนะนำถ้า sync project ข้ามเครื่องหรือขึ้น cloud

```json
"discord": {
  "enabled": true,
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

## Alert จะส่งเมื่อไหร่

ส่งเฉพาะตอนมี signal ใหม่ที่ถูก save ลง journal

ไม่ส่งทุกครั้งที่ refresh หน้าจอ

## ข้อควรระวัง

- อย่าแชร์ webhook URL ให้คนอื่น
- ถ้า webhook หลุด ให้ลบ webhook เก่าและสร้างใหม่
- ตอนนี้ Discord ใช้สำหรับ alert เท่านั้น ยังไม่ใช้สั่งเทรด
