# วิธีดูและรัน

ดับเบิลคลิกไฟล์:

- `RUN_ONCE.bat` ดูผลวิเคราะห์ 1 ครั้ง
- `RUN_LIVE.bat` รัน live ทุก 10 วิ
- `VIEW_HISTORY.bat` ดู signal ที่บันทึกไว้
- `RUN_TRACK.bat` เช็กว่า signal เก่าแตะ TP/SL หรือยัง
- `RUN_STATS.bat` ดู win/loss แยกตาม mode/session
- `RUN_EXPORT_DATASET.bat` export ข้อมูลสำหรับ ML
- `RUN_BACKTEST.bat` backtest จาก CSV ปัจจุบัน
- `RUN_ANALYZE_BACKTEST.bat` วิเคราะห์ผล backtest ว่าแพ้ตรงไหน
- `RUN_CHECK_CSV.bat` เช็กจำนวนแท่ง CSV

ใน VSCode:

1. กด `Ctrl+Shift+P`
2. พิมพ์ `Tasks: Run Task`
3. เลือก:
   - `MT5 Planner: Live`
   - `MT5 Planner: Run Once`
   - `MT5 Planner: History`
   - `MT5 Planner: Track Results`
   - `MT5 Planner: Stats`
   - `MT5 Planner: Export Dataset`
   - `MT5 Planner: Backtest`
   - `MT5 Planner: Analyze Backtest`

BTCUSDm:

- `101 BTC Planner Live`
- `102 BTC Planner Run Once`
- `103 BTC Planner Check CSV`
- `104 BTC Planner Backtest`
- `105 BTC Planner Analyze Backtest`

ต้องเปิด MT5 + EA `ChartDataExporter` ไว้ก่อน

อ่านผล:

- `bias LONG` = ระบบมองฝั่ง buy
- `bias SHORT` = ระบบมองฝั่ง sell
- `safe` = เสี่ยงต่ำกว่า
- `mid` = ค่า default
- `aggressive` = TP ไกลกว่า เสี่ยงโดนหลอกสูงกว่า
- `entry` = จุดเข้า
- `sl` = จุด cut loss
- `tp` = เป้า
- `rr` = Risk:Reward
- `risk` = % เสี่ยงต่อไม้
- `$risk` = เงินที่เสี่ยงจริงโดยประมาณ
- `lot` = lot ที่คำนวณจาก USD demo account
- `spread` = ask - bid
- `SPREAD BLOCK` = spread เกิน `spread_filter.max_spread_price` ใน `config.json`
- `quality A/B/C/D` = คะแนน setup จาก trend, RSI, volatility, spread
- `QUALITY BLOCK` = quality ต่ำกว่า `quality_filter.min_score`
- `session` = ช่วงตลาดจากเวลา candle
- `setup` = pattern ที่ยืนยัน เช่น `vcp`, `flat_base`, `breakout`, `retest`
- `features` = มุมมองเสริม: scalping momentum, trend strength, SMC event, fibo zone
