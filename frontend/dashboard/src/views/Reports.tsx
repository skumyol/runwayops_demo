import React, { useState } from 'react';
import { TopNav } from '../components/TopNav';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Download, Calendar } from 'lucide-react';

const autoReaccommodatedData = [
  { date: 'Oct 8', percentage: 78 },
  { date: 'Oct 9', percentage: 82 },
  { date: 'Oct 10', percentage: 85 },
  { date: 'Oct 11', percentage: 84 },
  { date: 'Oct 12', percentage: 88 },
  { date: 'Oct 13', percentage: 90 },
  { date: 'Oct 14', percentage: 87 },
];

const timeToPlanData = [
  { time: '<2m', count: 45 },
  { time: '2-4m', count: 78 },
  { time: '4-6m', count: 32 },
  { time: '6-8m', count: 18 },
  { time: '>8m', count: 12 },
];

const voucherCostData = [
  { date: 'Oct 8', cost: 156 },
  { date: 'Oct 9', cost: 148 },
  { date: 'Oct 10', cost: 152 },
  { date: 'Oct 11', cost: 145 },
  { date: 'Oct 12', cost: 138 },
  { date: 'Oct 13', cost: 140 },
  { date: 'Oct 14', cost: 142 },
];

const compensationData = [
  { bundle: 'Miles only', uptake: '34%', avgCost: '$85', count: 142 },
  { bundle: 'Miles + Meal voucher', uptake: '28%', avgCost: '$125', count: 118 },
  { bundle: 'Miles + Hotel', uptake: '22%', avgCost: '$245', count: 92 },
  { bundle: 'Miles + Upgrade voucher', uptake: '16%', avgCost: '$185', count: 68 },
];

export function Reports() {
  const [timeRange, setTimeRange] = useState('7d');

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <TopNav
        title="IROP Recovery Reports"
        subtitle="Performance Analytics & Insights"
        actions={
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[180px] h-10">
                <Calendar className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24h">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </Button>
          </div>
        }
      />

      <div className="p-8 space-y-6">
        {/* Auto-reaccommodated Trend */}
        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-4">
            Auto-reaccommodation Rate
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={autoReaccommodatedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
                domain={[0, 100]}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="percentage"
                stroke="#006564"
                strokeWidth={3}
                dot={{ fill: '#006564', r: 4 }}
                name="Success Rate (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Time to Plan Distribution */}
        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-4">
            Time-to-Plan Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timeToPlanData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="time" 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
              />
              <Bar
                dataKey="count"
                fill="#367D79"
                radius={[8, 8, 0, 0]}
                name="Number of Cases"
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Voucher Cost Trend */}
        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-4">
            Average Voucher Cost per Passenger
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={voucherCostData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                stroke="#94a3b8"
                domain={[0, 200]}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(value) => `$${value}`}
              />
              <Legend 
                wrapperStyle={{ fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#C2262E"
                strokeWidth={3}
                dot={{ fill: '#C2262E', r: 4 }}
                name="Cost ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Compensation Bundle Uptake */}
        <Card className="p-6 rounded-[12px]">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-4">
            Compensation Bundle Uptake
          </h3>
          <Table>
            <TableHeader>
              <TableRow className="h-[44px]">
                <TableHead>Bundle Type</TableHead>
                <TableHead>Uptake Rate</TableHead>
                <TableHead>Avg Cost</TableHead>
                <TableHead>Total Cases</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {compensationData.map((row) => (
                <TableRow key={row.bundle} className="h-[44px]">
                  <TableCell className="text-[14px]">{row.bundle}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary"
                          style={{ width: row.uptake }}
                        />
                      </div>
                      <span className="text-[14px] font-semibold">{row.uptake}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-[14px] font-semibold">{row.avgCost}</TableCell>
                  <TableCell className="text-[14px] text-muted-foreground">{row.count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-6">
          <Card className="p-6 rounded-[12px]">
            <h4 className="text-[14px] text-muted-foreground mb-2">Total Disruptions</h4>
            <p className="text-[32px] leading-[40px] font-semibold">1,847</p>
            <p className="text-[12px] text-success mt-2">-12% vs last week</p>
          </Card>
          <Card className="p-6 rounded-[12px]">
            <h4 className="text-[14px] text-muted-foreground mb-2">Avg Resolution Time</h4>
            <p className="text-[32px] leading-[40px] font-semibold">4.2m</p>
            <p className="text-[12px] text-success mt-2">-1.3m improvement</p>
          </Card>
          <Card className="p-6 rounded-[12px]">
            <h4 className="text-[14px] text-muted-foreground mb-2">Customer Satisfaction</h4>
            <p className="text-[32px] leading-[40px] font-semibold">4.6/5</p>
            <p className="text-[12px] text-success mt-2">+0.3 vs baseline</p>
          </Card>
        </div>
      </div>
    </div>
  );
}
