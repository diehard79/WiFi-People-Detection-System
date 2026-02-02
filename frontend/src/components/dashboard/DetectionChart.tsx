'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'
import { DetectionHistory } from '@/types/detection'

export function DetectionChart() {
  const [data, setData] = useState<DetectionHistory[]>([])

  useEffect(() => {
    // Simulate historical data
    const generateHistoricalData = () => {
      const historical: DetectionHistory[] = []
      const now = new Date()

      for (let i = 60; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60000) // Last 60 minutes
        // Simulate realistic detection patterns
        const hour = time.getHours()
        let count = 0

        // Simulate office hours pattern
        if (hour >= 8 && hour <= 18) {
          count = Math.floor(Math.random() * 8)
        } else {
          count = Math.floor(Math.random() * 2)
        }

        const presence = count > 0

        historical.push({
          time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          count: count,
          presence: presence
        })
      }

      return historical
    }

    const historical = generateHistoricalData()
    setData(historical)
  }, [])

  return (
    <div className="bg-white rounded-lg shadow p-6 transition-all duration-300 hover:shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Detection History</h3>
        <span className="text-sm text-gray-600">Last 60 minutes</span>
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            stroke="#9ca3af"
            interval="preserveStartEnd"
          />
          <YAxis
            label={{ value: 'People Count', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
            tick={{ fontSize: 12, fill: '#6b7280' }}
            stroke="#9ca3af"
            domain={[0, 'dataMax + 1']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e5e7eb',
              borderRadius: '0.5rem',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: '1rem' }}
            iconType="circle"
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#3b82f6"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorCount)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
