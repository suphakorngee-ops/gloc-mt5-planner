# Multi-Model Agent Plan

ทำได้: ใช้ AI หลายตัวช่วยคนละหน้าที่ เช่น Gemini, Gemma, GPT

หลักการคือทุก model ต้องอ่าน/เขียนผ่านไฟล์กลาง ไม่ให้คุยกันแบบลอย ๆ

## Role Split

```text
Gloc Analyst   = GPT หรือ model ที่ reasoning ดี ใช้วิเคราะห์/ตัดสินใจระบบ
Kloc Journal   = Gemma/Gemini ใช้จัดข้อมูล สรุป journal ทำความสะอาด notes
Rloc Reporter  = model ราคาถูก ใช้สรุป report/Discord message
Oloc Scheduler = ไม่ต้องใช้ LLM มาก เป็นตัวปลุกงาน
Vloc Executor  = ไม่ควรใช้ LLM ส่ง order โดยตรงจนกว่า guard พร้อม
```

## Shared Memory

```text
PROJECT_STATE.md
PROJECT_MEMORY.md
AI_RUNBOOK.md
AGENT_ARCHITECTURE.md
journal_btc_current.sqlite
journal_xau_current.sqlite
reports/
```

## Why File Memory Is Useful

ข้อดี:

- อยู่ข้ามแชทได้
- ราคาถูกกว่าใส่ทุกอย่างใน token
- อ่านทวน/backup ได้
- ทำให้หลาย model ใช้ข้อมูลชุดเดียวกัน

ข้อจำกัด:

- ยังไม่ใช่ ML learning จริง
- คุณภาพขึ้นกับการบันทึกให้เป็นระเบียบ
- ต้องมี evaluator/backtest/forward report เพื่อวัดว่าดีขึ้นจริงไหม

## Future Model Router

เพิ่มไฟล์ประมาณนี้ในอนาคต:

```text
mt5_planner/model_router.py
agents/prompts/
reports/model_outputs/
```

Flow:

```text
task -> model_router -> selected model -> write report/file -> human/Rloc reviews
```

Rule:

```text
Only Vloc Executor can ever send orders, and it is OFF now.
```
