# Champion Trading Strategy Prompt

คำสั่ง:

วิเคราะห์และสรุปกลยุทธ์การเทรดจากข้อมูลหลักการของแชมป์โลกการเทรด (Trading Champions) ต่อไปนี้ เพื่อสร้างเป็นโมเดลแนวทางเทรดที่มีความน่าจะเป็นสูง (High Probability Setup)

## Entry Strategy

### VCP - Volatility Contraction Pattern

แนว Mark Minervini:

- ราคาแกว่งแคบลงเป็นรอบ ๆ
- volatility ลดลง
- volume แห้งก่อน breakout
- เข้าเมื่อ breakout พร้อม confirmation

ใช้กับ XAUUSD/FX:

- ใช้ ATR contraction แทน volume contraction
- ใช้ range compression เช่น high-low ของ 3-5 ชุดหลังเล็กลง
- ใช้ breakout จาก swing high/low หรือ consolidation box
- ถ้า spread สูง ไม่เข้า

### SEPA - Specific Entry Point Analysis

แนว Mark Minervini:

- เทรดเฉพาะสินทรัพย์ที่ trend ชัด
- รอจุดเข้าเฉพาะ ไม่ไล่ราคา
- cut loss เร็ว

ใช้กับ XAUUSD/FX:

- ใช้ EMA stack และ EMA slope เป็น trend template
- รอ pullback/retest หรือ breakout confirmation
- quality ต่ำกว่า B ไม่ save signal

### Chart Patterns

แนว Dan Zanger:

- Cup and Handle
- Flat Base
- Breakout ต้องมี volume ยืนยัน

ใช้กับ XAUUSD/FX:

- ใช้ flat base/consolidation ก่อน breakout
- ใช้ tick volume เฉพาะเป็น confirmation รอง
- ใช้ candle close เหนือ/ใต้โซนสำคัญ

## Risk Management

- มี hard stop ทุกครั้ง
- RR ขั้นต่ำควร 2:1 สำหรับ default plan
- 3:1 ใช้กับ aggressive เท่านั้น
- เป้าหมายหลักคือ capital preservation
- `NO TRADE` ดีกว่า forced trade

## Market Context

### Auction Market Theory

- ดู value area / fair price zone
- ถ้าราคาอยู่กลาง value area ให้ระวัง
- setup ดีขึ้นเมื่อราคาออกจาก balance แล้ว retest ผ่าน

ใช้กับ MVP:

- เริ่มจาก swing high/low และ consolidation range
- เพิ่ม VWAP/value area ภายหลัง

### Seasonal & Cycles

แนว Larry Williams:

- ใช้ช่วงเวลา/session ที่ตลาดมี edge
- ใช้สถิติย้อนหลังช่วยเลือกเวลาที่เทรด

ใช้กับ MVP:

- เก็บ session ทุก signal
- วิเคราะห์ win/loss by session

## Position Sizing

- เริ่ม risk ต่ำ
- เพิ่ม exposure เฉพาะเมื่อไม้แรกกำไร
- ไม่เพิ่ม lot หลังขาดทุน
- demo/cent account ต้องเคารพ min lot เพราะอาจทำให้ risk จริงสูงกว่าเป้า

## Model Rules

High Probability Setup ต้องผ่าน:

1. Trend confirmed
2. Volatility acceptable
3. Spread acceptable
4. Quality score >= 65
5. RR >= 2 สำหรับ mid
6. มี SL ชัดเจน
7. บันทึกผลทุกครั้ง

Next engine upgrades:

1. VCP detector
2. Breakout/retest detector
3. Flat base detector
4. Session stats
5. MFE/MAE tracker

## SMC / Wyckoff Gold Logic Added

New preferred flow for XAUUSD:

1. Price taps important zone.
2. Liquidity sweep / Wyckoff spring or upthrust.
3. CHoCH / micro structure shift.
4. Entry around FVG or last order-block proxy.
5. If no FVG/OB zone, wait.

This is preferred over pure support/resistance breakout because gold often sweeps stops first.

User supplied references:

- http://www.youtube.com/watch?v=AY7fWmE1CBk
- http://www.youtube.com/watch?v=VZh4Y96FYxY

Current backtest note:

- SMC flow detector is implemented.
- In current 400-bar CSV sample, strict SMC flow rarely triggers.
- Existing signals are still mostly fibo pullback / BOS context.
- Need more historical data before judging SMC flow properly.
