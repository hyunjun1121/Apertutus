'use client';

import { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import * as XLSX from 'xlsx';

interface XlsxUploaderProps {
  onDataConverted?: (data: any[], fileName: string) => void;
  onError?: (error: string) => void;
}

interface SheetInfo {
  name: string;
  rows: number;
  columns: number;
  headers: string[];
  preview: any[];
}

export default function XlsxUploader({ onDataConverted, onError }: XlsxUploaderProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [sheets, setSheets] = useState<SheetInfo[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [convertedData, setConvertedData] = useState<any[]>([]);
  const [fileName, setFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      onError?.('Please select a valid Excel file (.xlsx or .xls)');
      return;
    }

    setIsProcessing(true);
    setProgress(10);
    setFileName(file.name);

    try {
      const arrayBuffer = await file.arrayBuffer();
      setProgress(30);

      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      setProgress(50);

      const sheetsInfo: SheetInfo[] = workbook.SheetNames.map(sheetName => {
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        const headers = jsonData[0] as string[] || [];
        
        return {
          name: sheetName,
          rows: jsonData.length,
          columns: headers.length,
          headers: headers,
          preview: jsonData.slice(0, 5)
        };
      });

      setSheets(sheetsInfo);
      setSelectedSheet(sheetsInfo[0]?.name || '');
      setProgress(100);

    } catch (error) {
      console.error('Error reading Excel file:', error);
      onError?.(`Error reading file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  const convertSheet = (sheetName: string) => {
    if (!sheets.length) return;

    setIsProcessing(true);
    
    try {
      const sheet = sheets.find(s => s.name === sheetName);
      if (!sheet) throw new Error('Sheet not found');

      // Re-read the workbook to get actual data
      const fileInput = fileInputRef.current;
      const file = fileInput?.files?.[0];
      
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = e.target?.result;
            const workbook = XLSX.read(data, { type: 'binary' });
            const worksheet = workbook.Sheets[sheetName];
            
            const jsonData = XLSX.utils.sheet_to_json(worksheet, {
              header: 1,
              defval: '',
              blankrows: false
            });

            // Convert to objects using first row as headers
            const headers = jsonData[0] as string[];
            const rows = jsonData.slice(1) as any[][];
            
            const convertedRows = rows.map((row, index) => {
              const obj: any = {
                custom_id: `request-${index + 1}`
              };
              
              headers.forEach((header, colIndex) => {
                const cleanHeader = header.toString().trim();
                obj[cleanHeader] = row[colIndex] || '';
              });
              
              return obj;
            });

            setConvertedData(convertedRows);
            onDataConverted?.(convertedRows, fileName);
            
          } catch (error) {
            console.error('Error converting sheet:', error);
            onError?.(`Error converting sheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
          } finally {
            setIsProcessing(false);
          }
        };
        
        reader.readAsBinaryString(file);
      }
      
    } catch (error) {
      console.error('Error converting sheet:', error);
      onError?.(`Error converting sheet: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsProcessing(false);
    }
  };

  const downloadJson = () => {
    if (!convertedData.length) return;

    const dataStr = JSON.stringify(convertedData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName.replace(/\.(xlsx|xls)$/i, '.json');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Excel to JSON Converter</CardTitle>
        <p className="text-sm text-muted-foreground">
          Upload an Excel file (.xlsx or .xls) to convert it to JSON format
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Upload */}
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing}
            className="w-full"
          >
            {isProcessing ? 'Processing...' : 'Select Excel File'}
          </Button>
        </div>

        {/* Progress Bar */}
        {progress > 0 && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Processing...</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}

        {/* Sheet Selection */}
        {sheets.length > 0 && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Select Sheet:</label>
              <select
                value={selectedSheet}
                onChange={(e) => setSelectedSheet(e.target.value)}
                className="w-full mt-1 p-2 border border-gray-300 rounded-md"
              >
                {sheets.map(sheet => (
                  <option key={sheet.name} value={sheet.name}>
                    {sheet.name} ({sheet.rows} rows, {sheet.columns} columns)
                  </option>
                ))}
              </select>
            </div>

            {/* Sheet Preview */}
            {selectedSheet && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Preview:</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs border">
                    <thead>
                      <tr className="bg-gray-50">
                        {sheets.find(s => s.name === selectedSheet)?.headers.map((header, i) => (
                          <th key={i} className="border p-1 text-left">{header}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sheets.find(s => s.name === selectedSheet)?.preview.slice(1, 4).map((row: any[], i) => (
                        <tr key={i}>
                          {row.map((cell, j) => (
                            <td key={j} className="border p-1">{cell || ''}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Convert Button */}
            <div className="flex gap-2">
              <Button
                onClick={() => convertSheet(selectedSheet)}
                disabled={!selectedSheet || isProcessing}
                className="flex-1"
              >
                Convert to JSON
              </Button>
              
              {convertedData.length > 0 && (
                <Button
                  onClick={downloadJson}
                  variant="outline"
                  className="flex-1"
                >
                  Download JSON ({convertedData.length} records)
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Success Message */}
        {convertedData.length > 0 && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">
              ✅ Successfully converted {convertedData.length} records from "{selectedSheet}" sheet
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
