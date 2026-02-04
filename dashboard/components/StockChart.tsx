
import React from 'react';
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area } from 'recharts';
import { StockData } from '../types';

const data = [
  { name: 'Day 1', market: 70, leaders: 72, volume: 1200 },
  { name: 'Day 2', market: 71, leaders: 75, volume: 900 },
  { name: 'Day 3', market: 69, leaders: 78, volume: 1500 },
  { name: 'Day 4', market: 72, leaders: 82, volume: 2200 },
  { name: 'Day 5', market: 73, leaders: 88, volume: 3100 },
  { name: 'Day 6', market: 74, leaders: 92, volume: 2800 },
  { name: 'Day 7', market: 75, leaders: 95, volume: 4200 },
];

const StockChart: React.FC<{ stocks: StockData[] }> = () => {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="colorLeaders" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis 
          dataKey="name" 
          stroke="#475569" 
          fontSize={10} 
          tickLine={false}
          axisLine={false}
          dy={10}
        />
        <YAxis 
          yAxisId="left"
          stroke="#475569" 
          fontSize={10} 
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <YAxis 
          yAxisId="right"
          orientation="right"
          stroke="#1e293b" 
          fontSize={10} 
          tickLine={false}
          axisLine={false}
          hide={true}
        />
        <Tooltip 
          contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}
          itemStyle={{ fontSize: '12px' }}
        />
        <Area 
          yAxisId="left"
          type="monotone" 
          dataKey="leaders" 
          stroke="#3b82f6" 
          fillOpacity={1} 
          fill="url(#colorLeaders)" 
          strokeWidth={4}
          animationDuration={2000}
        />
        <Line 
          yAxisId="left"
          type="monotone" 
          dataKey="market" 
          stroke="#475569" 
          strokeDasharray="5 5"
          dot={false}
        />
        <Bar 
          yAxisId="right"
          dataKey="volume" 
          barSize={20} 
          fill="#1e293b" 
          opacity={0.5}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
