export function calculateKairi(data: any[], period: number = 14): any[] {
  if (data.length < period) return [];
  
  const results = [];
  let sum = 0;
  
  // Calculate initial SMA
  for (let i = 0; i < period; i++) {
    sum += data[i].close;
  }
  
  // Need same index handling as typical charting libraries
  for (let i = period - 1; i < data.length; i++) {
    if (i > period - 1) {
      sum = sum - data[i - period].close + data[i].close;
    }
    const sma = sum / period;
    const currentPrice = data[i].close;
    
    // Kairi = ((Close - SMA) / SMA) * 100
    const kairiValue = ((currentPrice - sma) / sma) * 100;
    
    results.push({
      time: data[i].time,
      value: kairiValue
    });
  }
  
  return results;
}
