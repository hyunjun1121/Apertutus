"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { JAILBREAK_CATEGORIES, JailbreakCategory, getCategoryStats } from "@/lib/categorizer";
import { evaluateDataset, getPerformanceSummary } from "@/lib/evaluation";
import ModelComparisonTable from "@/components/ModelComparisonTable";
import CategoryPerformanceChart from "@/components/CategoryPerformanceChart";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

type Row = {
  custom_id: string;
  question: string;
  llm_response: string;
  response_content: string;
  final_score: number;
  average_score: number;
  score_0_25: number;
  asr_0_25: number;
  score_1: number;
  asr_1: number;
  category?: JailbreakCategory;
};

function AnimatedProgress({ value, className, delay = 0 }: { value: number; className?: string; delay?: number }) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return (
    <Progress
      value={animatedValue}
      className={`transition-all duration-1000 ease-out ${className}`}
    />
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<Row[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [categorizing, setCategorizing] = useState(false);
  const [categoryStats, setCategoryStats] = useState<ReturnType<typeof getCategoryStats>>([]);
  const [evaluationResults, setEvaluationResults] = useState<any[]>([]);
  const [performanceSummary, setPerformanceSummary] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState('GPT-4');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [sortField, setSortField] = useState<'custom_id' | 'question' | 'category' | 'final_score'>('final_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  
  // Landing page steps
  const [currentStep, setCurrentStep] = useState(0);
  const [apiEndpoint, setApiEndpoint] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isApiConfigured, setIsApiConfigured] = useState(false);

  // Step navigation functions
  const nextStep = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleApiSubmit = () => {
    if ((apiEndpoint === 'test' && apiKey === 'test') || (apiEndpoint && apiKey)) {
      setIsApiConfigured(true);
      // Add API validation
    }
  };

  // 정렬 함수
  const handleSort = (field: 'custom_id' | 'question' | 'category' | 'final_score') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // 정렬 및 필터링된 데이터
  const filteredAndSortedData = data
    .filter(row => 
      searchKeyword === '' || 
      row.question.toLowerCase().includes(searchKeyword.toLowerCase())
    )
    .sort((a, b) => {
      let aVal: any, bVal: any;
      
      switch (sortField) {
        case 'custom_id':
          aVal = a.custom_id;
          bVal = b.custom_id;
          break;
        case 'question':
          aVal = a.question.toLowerCase();
          bVal = b.question.toLowerCase();
          break;
        case 'category':
          aVal = a.category || '';
          bVal = b.category || '';
          break;
        case 'final_score':
        default:
          aVal = a.final_score;
          bVal = b.final_score;
          break;
      }
      
      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

  useEffect(() => {
    async function loadAndCategorizeData() {
      try {
        const res = await fetch("/data/converted_dataset.json");
        const rows: Row[] = await res.json();
        
        setCategorizing(true);
        
        const prompts = rows.map(row => row.question);
        const categorizeRes = await fetch("/api/categorize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompts })
        });
        
        if (categorizeRes.ok) {
          const { categorizedPrompts } = await categorizeRes.json();
          const categorizedRows = rows.map((row, index) => ({
            ...row,
            category: categorizedPrompts[index]?.category
          }));
          
          setData(categorizedRows);
          setCategoryStats(getCategoryStats(categorizedRows));
          
          // Evaluate dataset and generate comparison data
          const evalResults = evaluateDataset(categorizedRows);
          const perfSummary = getPerformanceSummary(evalResults);
          setEvaluationResults(evalResults);
          setPerformanceSummary(perfSummary);
        } else {
          setData(rows);
        }
        
        setCategorizing(false);
        
        setTimeout(() => {
          setIsLoaded(true);
        }, 100);
      } catch (error) {
        console.error('Error loading data:', error);
        setCategorizing(false);
      }
    }

    loadAndCategorizeData();
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image */}
      <div 
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/asset/bg.png')"
        }}
      ></div>
      
      {/* Dark overlay for better text readability */}
      <div className="absolute inset-0 bg-black/30"></div>
      
      <div className="relative z-10 p-6">
        {!isApiConfigured ? (
          <>
            {/* Step indicator */}
            <div className="flex justify-center mb-12">
              <div className="flex items-center space-x-8">
                {['Welcome', 'Pipeline', 'API Configuration'].map((label, index) => (
                  <div key={index} className={`text-center transition-all duration-500 ${
                    index === currentStep ? 'text-red-500 font-bold text-lg' : 'text-white/60 text-base'
                  }`} style={{ color: index === currentStep ? '#FF0000' : undefined }}>
                    {label}
                  </div>
                ))}
              </div>
            </div>

            {/* Step content */}
            <div className="min-h-[700px] flex items-center justify-center">
              {/* Step 0: Welcome with Logo */}
              {currentStep === 0 && (
                <div className="w-full h-full relative">
                  {/* Background Image */}
                  <div 
                    className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-60"
                    style={{
                      backgroundImage: "url('/asset/bg.png')"
                    }}
                  ></div>
                  
                  {/* Content */}
                  <div className="relative z-10 flex flex-col items-center justify-center text-center space-y-8 py-20">
                    {/* Logo */}
                    <div>
                      <img 
                        src="/asset/logo.png" 
                        alt="Logo" 
                        className="max-w-4xl max-h-48 object-contain"
                      />
                    </div>
                    
                    {/* Welcome Message */}
                    <div className="space-y-4 mb-10">
                      <h1 className="text-4xl font-black text-white">
                        Welcome to AI Security Testing
                      </h1>
                      <p className="text-white/80 text-xl max-w-2xl">
                        Advanced jailbreak detection and vulnerability assessment platform
                      </p>
                    </div>
                  </div>
                  
                  {/* Navigation */}
                  <div className="absolute bottom-6 left-0 right-0 z-10 flex justify-center">
                    <button
                      onClick={nextStep}
                      className="text-white px-10 py-6 rounded-xl font-bold shadow-lg transition-all duration-300 flex items-center gap-3 text-lg group"
                    >
                      <span className="group-hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.8)] transition-all duration-300">
                        Get Started
                      </span>

                    </button>
                  </div>
                </div>
              )}
              
              {/* Step 1: Pipeline Images */}
              {currentStep === 1 && (
                <div className="w-full h-full relative">
                  {/* Content */}
                  <div className="relative z-10 flex flex-col items-center justify-center space-y-8 py-8">
                    {/* Images */}
                    <div className="space-y-5">
                      <div className="flex justify-center">
                        <img 
                          src="/asset/pip1.png" 
                          alt="Pipeline 1" 
                          className="max-w-4xl w-full object-contain"
                        />
                      </div>
                      <div className="flex justify-center">
                        <img 
                          src="/asset/pip2.png" 
                          alt="Pipeline 2" 
                          className="max-w-4xl w-full object-contain"
                        />
                      </div>
                    </div>
                  </div>
                  
                  {/* Navigation */}
                  <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-between px-8 z-10 pointer-events-none">
                    <button
                      onClick={prevStep}
                      className="text-white text-3xl font-bold hover:text-gray-300 transition-all duration-300 pointer-events-auto"
                    >
                      &lt;
                    </button>
                    <button
                      onClick={nextStep}
                      className="text-white text-3xl font-bold hover:text-gray-300 transition-all duration-300 pointer-events-auto"
                    >
                      &gt;
                    </button>
                  </div>
                </div>
              )}
              
              {/* Step 2: API Configuration */}
              {currentStep === 2 && (
                <div className="w-full h-full relative">
                  {/* Content */}
                  <div className="relative z-10 p-8 max-w-4xl mx-auto">
                    <div className="space-y-8 max-w-2xl mx-auto">
                      <div className="space-y-6">
                        <div>
                          <label className="block text-white font-semibold mb-3 text-xl">API Endpoint</label>
                          <input
                            type="url"
                            placeholder="Enter your model's API endpoint URL"
                            value={apiEndpoint}
                            onChange={(e) => setApiEndpoint(e.target.value)}
                            className="w-full px-6 py-4 bg-white/20 backdrop-blur-sm border border-white/30 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all duration-300 text-lg"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-white font-semibold mb-3 text-xl">API Key</label>
                          <input
                            type="password"
                            placeholder="Your API key will be used to test the model"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            className="w-full px-6 py-4 bg-white/20 backdrop-blur-sm border border-white/30 rounded-2xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all duration-300 text-lg"
                          />
                        </div>
                      </div>
                      
                      <div className="bg-red-500/20 border border-red-400/30 rounded-2xl p-6">
                        <h3 className="text-white font-bold mb-3 flex items-center gap-2 text-lg">
                          <span>🛡️</span>
                          Security Notice
                        </h3>
                        <p className="text-white/80 text-base leading-relaxed">
                          Your API credentials are processed securely and used only for testing purposes. 
                          We recommend using a dedicated API key with limited permissions for testing.
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Navigation */}
                  <div className="absolute inset-y-0 left-0 right-0 flex items-center justify-between px-8 z-10 pointer-events-none">
                    <button
                      onClick={prevStep}
                      className="text-white text-3xl font-bold hover:text-gray-300 transition-all duration-300 pointer-events-auto"
                    >
                      &lt;
                    </button>
                    <button
                      onClick={handleApiSubmit}
                      disabled={!((apiEndpoint === 'test' && apiKey === 'test') || (apiEndpoint && apiKey))}
                      className={`text-3xl font-bold transition-all duration-300 pointer-events-auto ${
                        (apiEndpoint === 'test' && apiKey === 'test') || (apiEndpoint && apiKey)
                          ? 'text-white hover:text-gray-300'
                          : 'text-gray-600 cursor-not-allowed'
                      }`}
                    >
                      &gt;
                    </button>
                  </div>
                </div>
              )}
                    </div>
          </>
        ) : (
          // Main dashboard after API configuration
          <div className="w-full space-y-8 relative z-10 p-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-3">API Endpoint</h3>
                <p className="text-gray-300 font-mono text-sm bg-black/30 p-3 rounded">{apiEndpoint}</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-3">Status</h3>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-green-300 font-semibold">Connected & Ready</span>
                </div>
              </div>
            </div>
            
            {/* Dashboard Tabs */}
            <div className="max-w-7xl mx-auto">
              <Tabs defaultValue="results" className="w-full">
                <div className="flex justify-center mb-8">
                  <TabsList className="bg-white/10 backdrop-blur-sm border border-white/20 p-2 rounded-2xl">
                    <TabsTrigger 
                      value="results" 
                      className="px-6 py-3 rounded-xl font-semibold transition-all duration-300 data-[state=active]:bg-white/20 data-[state=active]:text-white text-white/70"
                    >
                      🎯 Test Results
                    </TabsTrigger>
                    <TabsTrigger 
                      value="dataset" 
                      className="px-6 py-3 rounded-xl font-semibold transition-all duration-300 data-[state=active]:bg-white/20 data-[state=active]:text-white text-white/70"
                    >
                      📊 Dataset Analysis
                    </TabsTrigger>
                  </TabsList>
                </div>

                <TabsContent value="dataset" className="space-y-8">
                  {/* Category Distribution Chart */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                    <h2 className="text-2xl font-bold text-white mb-6 text-center">Category Distribution</h2>
                    {categoryStats.length > 0 && (
                      <div className="h-96 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={categoryStats.map(stat => ({
                                name: stat.category,
                                value: stat.count,
                                color: stat.color,
                                percentage: stat.percentage,
                                description: stat.description
                              }))}
                              cx="50%"
                              cy="50%"
                              outerRadius={140}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {categoryStats.map((stat, index) => (
                                <Cell key={`cell-${index}`} fill={stat.color} />
                              ))}
                            </Pie>
                            <Tooltip 
                              content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                  const data = payload[0].payload;
                                  return (
                                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                                      <div className="flex items-center gap-2">
                                        <div 
                                          className="w-4 h-4 rounded-full"
                                          style={{ backgroundColor: data.color }}
                                        />
                                        <span className="font-semibold text-sm">{data.name}</span>
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              }}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    <div className="text-center mt-6">
                      <div className="text-xl font-bold text-white">
                        {data.length} Total Jailbreak Prompts
                      </div>
                      <div className="text-white/70 mt-2">
                        Categorized into {categoryStats.length} attack patterns
                      </div>
                    </div>
                  </div>

                  {/* Jailbreak Prompts Table */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-white">Jailbreak Prompts</h2>
                      <div className="relative">
                        <input
                          type="text"
                          placeholder="🔎 Search questions..."
                          value={searchKeyword}
                          onChange={(e) => setSearchKeyword(e.target.value)}
                          className="px-4 py-2 pl-10 bg-white/20 backdrop-blur-sm border border-white/30 rounded-xl text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all duration-300"
                        />
                        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/70">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    
                    <div className="max-h-96 overflow-y-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-white/20">
                            <TableHead 
                              className="text-white font-semibold cursor-pointer hover:text-blue-300 transition-colors"
                              onClick={() => handleSort('custom_id')}
                            >
                              ID {sortField === 'custom_id' && (sortDirection === 'asc' ? '▲' : '▼')}
                            </TableHead>
                            <TableHead 
                              className="text-white font-semibold cursor-pointer hover:text-blue-300 transition-colors"
                              onClick={() => handleSort('question')}
                            >
                              Question {sortField === 'question' && (sortDirection === 'asc' ? '▲' : '▼')}
                            </TableHead>
                            <TableHead 
                              className="text-white font-semibold cursor-pointer hover:text-blue-300 transition-colors"
                              onClick={() => handleSort('category')}
                            >
                              Category {sortField === 'category' && (sortDirection === 'asc' ? '▲' : '▼')}
                            </TableHead>
                            <TableHead 
                              className="text-white font-semibold cursor-pointer hover:text-blue-300 transition-colors"
                              onClick={() => handleSort('final_score')}
                            >
                              Score {sortField === 'final_score' && (sortDirection === 'asc' ? '▲' : '▼')}
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredAndSortedData.map((row, i) => (
                            <TableRow key={i} className="border-white/10 hover:bg-white/5 transition-colors">
                              <TableCell className="text-white/90 font-mono text-sm">{row.custom_id}</TableCell>
                              <TableCell className="text-white/90 max-w-md">
                                <div className="truncate" title={row.question}>
                                  {row.question.length > 100 ? row.question.substring(0, 100) + '...' : row.question}
                                </div>
                              </TableCell>
                              <TableCell className="text-white/90">
                                {row.category && (
                                  <span 
                                    className="px-2 py-1 rounded-full text-xs font-medium text-white"
                                    style={{ backgroundColor: JAILBREAK_CATEGORIES[row.category].color }}
                                  >
                                    {row.category}
                                  </span>
                                )}
                              </TableCell>
                              <TableCell className="text-white/90 font-semibold">
                                {row.final_score.toFixed(2)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    
                    <div className="mt-4 text-center text-white/70">
                      Showing {filteredAndSortedData.length} of {data.length} prompts
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="results" className="space-y-8">
                  {/* Performance Metrics Cards */}
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                    <div className="flex items-center justify-between mb-8">
                      <div>
                        <h2 className="text-3xl font-black text-white flex items-center gap-3">
                          <span className="text-4xl">📊</span>
                          Performance Metrics
                        </h2>
                        <p className="text-white/70 text-lg mt-2">Real-time security analysis dashboard</p>
                      </div>
                      <div className="flex items-center gap-2 bg-green-500/20 px-4 py-2 rounded-full border border-green-400/30">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span className="text-green-300 font-bold text-sm">LIVE</span>
                      </div>
                    </div>
                    
                    {performanceSummary && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <div className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 backdrop-blur-sm rounded-2xl p-6 border border-green-400/30 hover:shadow-green-500/20 hover:shadow-xl transition-all duration-500 group">
                          <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-green-500/30 rounded-xl border border-green-400/50 group-hover:scale-110 transition-transform duration-300">
                              <span className="text-2xl">🛡️</span>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-green-300 font-semibold uppercase tracking-wide">Security Score</div>
                              <div className="text-xs text-green-200/60 mt-1">Overall Protection</div>
                            </div>
                          </div>
                          <div className="mb-3">
                            <div className="text-4xl font-black text-green-300 mb-2 group-hover:text-green-200 transition-colors">
                              {(performanceSummary.averageScore * 100).toFixed(1)}%
                            </div>
                            <div className="w-full bg-green-900/30 rounded-full h-2 overflow-hidden">
                              <AnimatedProgress 
                                value={performanceSummary.averageScore * 100} 
                                className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full shadow-lg shadow-green-500/30"
                                delay={200}
                              />
                            </div>
                          </div>
                          <div className="text-green-200/80 text-sm leading-relaxed">
                            Average protection level across all test cases
                          </div>
                        </div>

                        <div className="bg-gradient-to-br from-red-500/20 to-pink-600/20 backdrop-blur-sm rounded-2xl p-6 border border-red-400/30 hover:shadow-red-500/20 hover:shadow-xl transition-all duration-500 group">
                          <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-red-500/30 rounded-xl border border-red-400/50 group-hover:scale-110 transition-transform duration-300">
                              <span className="text-2xl">⚠️</span>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-red-300 font-semibold uppercase tracking-wide">Vulnerabilities</div>
                              <div className="text-xs text-red-200/60 mt-1">High Risk Items</div>
                            </div>
                          </div>
                          <div className="mb-3">
                            <div className="text-4xl font-black text-red-300 mb-2 group-hover:text-red-200 transition-colors">
                              {performanceSummary.vulnerablePrompts}
                            </div>
                            <div className="w-full bg-red-900/30 rounded-full h-2 overflow-hidden">
                              <AnimatedProgress 
                                value={(performanceSummary.vulnerablePrompts / performanceSummary.totalPrompts) * 100} 
                                className="bg-gradient-to-r from-red-400 to-pink-500 h-2 rounded-full shadow-lg shadow-red-500/30"
                                delay={400}
                              />
                            </div>
                          </div>
                          <div className="text-red-200/80 text-sm leading-relaxed">
                            Critical security issues detected
                          </div>
                        </div>

                        <div className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 backdrop-blur-sm rounded-2xl p-6 border border-blue-400/30 hover:shadow-blue-500/20 hover:shadow-xl transition-all duration-500 group">
                          <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-blue-500/30 rounded-xl border border-blue-400/50 group-hover:scale-110 transition-transform duration-300">
                              <span className="text-2xl">📈</span>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-blue-300 font-semibold uppercase tracking-wide">Total Tests</div>
                              <div className="text-xs text-blue-200/60 mt-1">Coverage Rate</div>
                            </div>
                          </div>
                          <div className="mb-3">
                            <div className="text-4xl font-black text-blue-300 mb-2 group-hover:text-blue-200 transition-colors">
                              {performanceSummary.totalPrompts}
                            </div>
                            <div className="w-full bg-blue-900/30 rounded-full h-2 overflow-hidden">
                              <AnimatedProgress 
                                value={100} 
                                className="bg-gradient-to-r from-blue-400 to-cyan-500 h-2 rounded-full shadow-lg shadow-blue-500/30"
                                delay={600}
                              />
                            </div>
                          </div>
                          <div className="text-blue-200/80 text-sm leading-relaxed">
                            Comprehensive test scenarios executed
                          </div>
                        </div>

                        <div className="bg-gradient-to-br from-purple-500/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-6 border border-purple-400/30 hover:shadow-purple-500/20 hover:shadow-xl transition-all duration-500 group">
                          <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-purple-500/30 rounded-xl border border-purple-400/50 group-hover:scale-110 transition-transform duration-300">
                              <span className="text-2xl">🎯</span>
                            </div>
                            <div className="text-right">
                              <div className="text-xs text-purple-300 font-semibold uppercase tracking-wide">Success Rate</div>
                              <div className="text-xs text-purple-200/60 mt-1">Defense Efficiency</div>
                            </div>
                          </div>
                          <div className="mb-3">
                            <div className="text-4xl font-black text-purple-300 mb-2 group-hover:text-purple-200 transition-colors">
                              {(((performanceSummary.totalPrompts - performanceSummary.vulnerablePrompts) / performanceSummary.totalPrompts) * 100).toFixed(1)}%
                            </div>
                            <div className="w-full bg-purple-900/30 rounded-full h-2 overflow-hidden">
                              <AnimatedProgress 
                                value={((performanceSummary.totalPrompts - performanceSummary.vulnerablePrompts) / performanceSummary.totalPrompts) * 100} 
                                className="bg-gradient-to-r from-purple-400 to-indigo-500 h-2 rounded-full shadow-lg shadow-purple-500/30"
                                delay={800}
                              />
                            </div>
                          </div>
                          <div className="text-purple-200/80 text-sm leading-relaxed">
                            Successfully blocked attack attempts
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Model Comparison and Performance Charts */}
                  <div className="space-y-6">
                    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-4">
                          <div className="p-3 bg-gradient-to-r from-indigo-500/30 to-purple-600/30 rounded-xl border border-indigo-400/50">
                            <span className="text-2xl">🤖</span>
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold text-white">
                              AI Model Comparison Hub
                            </h2>
                            <p className="text-white/70 text-sm mt-1">
                              Attack Success Rate (ASR) comparison across violation categories. Lower scores indicate better safety.
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <label className="text-sm font-medium text-white/80">Select Model:</label>
                          <select 
                            value={selectedModel} 
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="px-4 py-2 bg-white/20 backdrop-blur-sm border border-white/30 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all duration-300"
                          >
                            <option value="GPT-4" className="bg-gray-800 text-white">🧠 GPT-4</option>
                            <option value="GPT-3.5" className="bg-gray-800 text-white">💡 GPT-3.5</option>
                            <option value="Llama3.1" className="bg-gray-800 text-white">🦙 Llama3.1</option>
                            <option value="Llama3" className="bg-gray-800 text-white">🦙 Llama3</option>
                            <option value="Llama2" className="bg-gray-800 text-white">🦙 Llama2</option>
                            <option value="ChatGLM3" className="bg-gray-800 text-white">💬 ChatGLM3</option>
                            <option value="Vicuna" className="bg-gray-800 text-white">🦙 Vicuna</option>
                            <option value="DeepSeek-V3" className="bg-gray-800 text-white">🔍 DeepSeek-V3</option>
                            <option value="PaLM2" className="bg-gray-800 text-white">🌴 PaLM2</option>
                          </select>
                        </div>
                      </div>
                      
                      <ModelComparisonTable 
                        evaluationResults={evaluationResults}
                        selectedModel={selectedModel}
                      />
                    </div>
                    
                    <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                      <CategoryPerformanceChart 
                        evaluationResults={evaluationResults}
                        selectedModels={[selectedModel, 'GPT-3.5', 'Llama3.1']}
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
            
            <div className="text-center mt-8">
              <button
                onClick={() => setIsApiConfigured(false)}
                className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-300"
              >
                Reconfigure API
              </button>
            </div>
          </div>
      )}
      </div>
    </div>
  );
}
