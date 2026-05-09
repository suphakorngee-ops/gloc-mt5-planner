// Exports BTCUSDm M5 candles to CSV for the Python planner.
#property strict

input string ExportSymbol = "BTCUSDm";
input ENUM_TIMEFRAMES ExportTimeframe = PERIOD_M5;
input int BarsToExport = 10000;
input int TimerSeconds = 5;
input string FileName = "btcusdm_m5.csv";

int OnInit()
{
   EventSetTimer(TimerSeconds);
   ExportRates();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTimer()
{
   ExportRates();
}

void ExportRates()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(ExportSymbol, ExportTimeframe, 0, BarsToExport, rates);
   if(copied <= 0)
   {
      Print("CopyRates failed: ", GetLastError());
      return;
   }

   int handle = FileOpen(FileName, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("FileOpen failed: ", GetLastError());
      return;
   }

   MqlTick tick;
   double bid = 0.0;
   double ask = 0.0;
   double spreadPrice = 0.0;
   long spreadPoints = 0;
   if(SymbolInfoTick(ExportSymbol, tick))
   {
      bid = tick.bid;
      ask = tick.ask;
      spreadPrice = ask - bid;
      spreadPoints = (long)MathRound(spreadPrice / _Point);
   }

   FileWrite(handle, "time", "open", "high", "low", "close", "tick_volume", "bid", "ask", "spread_price", "spread_points");
   for(int i = copied - 1; i >= 0; i--)
   {
      FileWrite(
         handle,
         TimeToString(rates[i].time, TIME_DATE | TIME_SECONDS),
         DoubleToString(rates[i].open, _Digits),
         DoubleToString(rates[i].high, _Digits),
         DoubleToString(rates[i].low, _Digits),
         DoubleToString(rates[i].close, _Digits),
         IntegerToString(rates[i].tick_volume),
         DoubleToString(bid, _Digits),
         DoubleToString(ask, _Digits),
         DoubleToString(spreadPrice, _Digits),
         IntegerToString(spreadPoints)
      );
   }

   FileClose(handle);
}
