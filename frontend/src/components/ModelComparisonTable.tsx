'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { EvaluationResult, ModelComparison } from '@/lib/evaluation';
import { JAILBREAK_CATEGORIES } from '@/lib/categorizer';

interface ModelComparisonTableProps {
  evaluationResults: EvaluationResult[];
  selectedModel?: string;
}

export default function ModelComparisonTable({ evaluationResults, selectedModel = 'GPT-4' }: ModelComparisonTableProps) {
  const getPerformanceBadge = (performance: 'better' | 'worse' | 'similar', difference: number) => {
    if (performance === 'similar') {
      return <Badge variant="secondary">Similar ({difference >= 0 ? '+' : ''}{(difference * 100).toFixed(1)}%)</Badge>;
    } else if (performance === 'better') {
      return <Badge variant="destructive">More Vulnerable (+{(difference * 100).toFixed(1)}%)</Badge>;
    } else {
      return <Badge variant="default">More Resistant ({(difference * 100).toFixed(1)}%)</Badge>;
    }
  };

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1) + '%';
  };

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-white mb-2">Model Comparison: Our Results vs {selectedModel}</h3>
        <p className="text-white/70 text-sm">
          Attack Success Rate (ASR) comparison across violation categories. Lower scores indicate better safety.
        </p>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-white/20">
              <TableHead className="w-[200px] text-white font-semibold">Category</TableHead>
              <TableHead className="text-right text-white font-semibold">Our ASR</TableHead>
              <TableHead className="text-right text-white font-semibold">{selectedModel} ASR</TableHead>
              <TableHead className="text-right text-white font-semibold">Benchmark Avg</TableHead>
              <TableHead className="text-right text-white font-semibold">Baseline</TableHead>
              <TableHead className="text-white font-semibold">Performance</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {evaluationResults.map((result) => {
              const benchmarkScore = result.benchmarkComparison.modelScores[selectedModel] || 0;
              const difference = result.asr - benchmarkScore;
              const performance = Math.abs(difference) < 0.05 ? 'similar' : 
                                difference > 0 ? 'better' : 'worse';
              
              return (
                <TableRow key={result.category} className="border-white/10 hover:bg-white/5 transition-colors">
                  <TableCell className="font-medium text-white/90">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: JAILBREAK_CATEGORIES[result.category].color }}
                      />
                      <span className="text-sm">{result.category}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-white/90">
                    {formatScore(result.asr)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-white/90">
                    {formatScore(benchmarkScore)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-white/60">
                    {formatScore(result.benchmarkComparison.benchmarkAverage)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-white/60">
                    {formatScore(result.benchmarkComparison.benchmarkBaseline)}
                  </TableCell>
                  <TableCell>
                    {getPerformanceBadge(performance, difference)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
