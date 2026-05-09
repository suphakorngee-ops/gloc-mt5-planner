# MT5 AI Trading Planner MVP

MVP สำหรับเริ่มทำ dashboard/agent วิเคราะห์กราฟจาก MT5:

- ดึง candles จาก MT5
- คำนวณ indicators พื้นฐาน
- สร้างแผน `safe`, `mid`, `aggressive`
- คำนวณ `R:R`
- บันทึก signal ลง SQLite journal
- เริ่มจาก demo/log เท่านั้น ยังไม่ส่ง order จริง

## ติดตั้ง

ต้องมี Python และ MT5 terminal เปิด login ไว้

```powershell
pip install -r requirements.txt
```

ถ้าใช้ Python launcher:

```powershell
py -m pip install -r requirements.txt
```

## ตั้งค่า

แก้ไฟล์ `config.example.json` แล้ว save เป็น `config.json`

สำคัญ:

- `symbol`: ชื่อ symbol ใน broker เช่น `XAUUSD`, `XAUUSDm`, `USOIL`, `XTIUSD`
- `timeframe`: `M1`, `M5`, `M15`, `H1`
- `risk_per_trade`: เริ่ม `0.0025` ถึง `0.005`

## รัน

```powershell
python -m mt5_planner run --config config.json
```

โหมดนี้จะ:

1. ดึง candle ล่าสุด
2. วิเคราะห์ signal
3. พิมพ์แผน 3 แบบ
4. บันทึกลง `journal.sqlite`

## ถ้าติดตั้ง Python package `MetaTrader5` ไม่ได้

ใช้ EA exporter แทน:

1. เปิด MetaEditor
2. สร้าง Expert Advisor ชื่อ `ChartDataExporter`
3. วางโค้ดจาก `mt5_exporter/ChartDataExporter.mq5`
4. Compile
5. Attach EA กับกราฟ `XAUUSDm`
6. ตั้ง `FileName = xauusdm_m5.csv`
7. เปิด `File > Open Data Folder > MQL5 > Files`
8. copy path ของไฟล์ CSV มาใส่ `csv_path` ใน `config.json`

แล้วรัน:

```powershell
python -m mt5_planner csv --config config.json
```

หรือใช้ script live สำหรับเครื่องนี้:

```powershell
.\run_xauusdm_live.ps1
```

ดู signal ล่าสุด:

```powershell
python -m mt5_planner history --config config.json --limit 20
```

## ทดสอบ logic แบบไม่ใช้ MT5

```powershell
python -m mt5_planner demo
```

## Roadmap

1. ทำ data collector ให้เก็บ M1/M5/M15/H1 ต่อเนื่อง
2. เพิ่ม dashboard
3. เพิ่ม paper/demo execution
4. เก็บผล `MFE/MAE`
5. ทำ ML confidence scoring
