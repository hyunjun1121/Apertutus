'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EvaluationResult } from '@/lib/evaluation';
import { JAILBREAK_CATEGORIES } from '@/lib/categorizer';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from 'recharts';

interface CategoryPerformanceChartProps {
  evaluationResults: EvaluationResult[];
  selectedModels?: string[];
}

export default function CategoryPerformanceChart({ 
  evaluationResults, 
  selectedModels = ['GPT-4', 'GPT-3.5', 'Llama3.1'] 
}: CategoryPerformanceChartProps) {
  const chartData = evaluationResults.map(result => {
    const dataPoint: any = {
      category: result.category.length > 20 ? 
        result.category.substring(0, 17) + '...' : 
        result.category,
      fullCategory: result.category,
      ourScore: result.asr * 100,
      benchmarkAvg: result.benchmarkComparison.benchmarkAverage * 100,
      baseline: result.benchmarkComparison.benchmarkBaseline * 100,
      color: JAILBREAK_CATEGORIES[result.category].color
    };
    
    selectedModels.forEach(model => {
      dataPoint[model] = (result.benchmarkComparison.modelScores[model] || 0) * 100;
    });
    
    return dataPoint;
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800/90 backdrop-blur-sm p-3 border border-white/20 rounded-lg shadow-lg">
          <p className="font-medium text-white">{data.fullCategory}</p>
          <div className="space-y-1 mt-2">
            <p className="text-blue-400">Our Score: {data.ourScore.toFixed(1)}%</p>
            <p className="text-gray-300">Benchmark Avg: {data.benchmarkAvg.toFixed(1)}%</p>
            <p className="text-gray-400">Baseline: {data.baseline.toFixed(1)}%</p>
            {selectedModels.map(model => (
              <p key={model} className="text-purple-400">
                {model}: {data[model].toFixed(1)}%
              </p>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Bar Chart */}
      <div>
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-white mb-2">Attack Success Rate by Category</h3>
          <p className="text-white/70 text-sm">
            Comparison of our model performance vs benchmark models (lower is better for safety)
          </p>
        </div>
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4">
          <ResponsiveContainer width="100%" height={500}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="category" 
                angle={-45}
                textAnchor="end"
                height={120}
                fontSize={12}
                stroke="rgba(255,255,255,0.7)"
              />
              <YAxis 
                label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'rgba(255,255,255,0.7)' } }}
                stroke="rgba(255,255,255,0.7)"
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="ourScore" fill="#3b82f6" name="Our Model" />
              <Bar dataKey="benchmarkAvg" fill="#6b7280" name="Benchmark Average" />
              {selectedModels.map((model, index) => (
                <Bar 
                  key={model}
                  dataKey={model} 
                  fill={['#8b5cf6', '#10b981', '#f59e0b'][index % 3]} 
                  name={model} 
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Line Chart for trends */}
      <div>
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-white mb-2">Performance Trend Across Categories</h3>
          <p className="text-white/70 text-sm">
            Line chart showing how different models perform across violation categories
          </p>
        </div>
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4">
          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="category"
                angle={-45}
                textAnchor="end"
                height={120}
                fontSize={12}
                stroke="rgba(255,255,255,0.7)"
              />
              <YAxis 
                label={{ value: 'Attack Success Rate (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: 'rgba(255,255,255,0.7)' } }}
                stroke="rgba(255,255,255,0.7)"
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="ourScore" 
                stroke="#3b82f6" 
                strokeWidth={3}
                name="Our Model"
                dot={{ r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="benchmarkAvg" 
                stroke="#6b7280" 
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Benchmark Average"
                dot={{ r: 3 }}
              />
              {selectedModels.map((model, index) => (
                <Line
                  key={model}
                  type="monotone"
                  dataKey={model}
                  stroke={['#8b5cf6', '#10b981', '#f59e0b'][index % 3]}
                  strokeWidth={2}
                  name={model}
                  dot={{ r: 3 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
