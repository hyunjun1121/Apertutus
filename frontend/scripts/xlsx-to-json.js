const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

function xlsxToJson(inputPath, outputPath, options = {}) {
  try {
    console.log(`Reading XLSX file: ${inputPath}`);
    
    if (!fs.existsSync(inputPath)) {
      throw new Error(`File not found: ${inputPath}`);
    }

    const workbook = XLSX.readFile(inputPath);
    const sheetNames = workbook.SheetNames;
    
    console.log(`Found ${sheetNames.length} sheets: ${sheetNames.join(', ')}`);

    let result = {};
    let allData = [];

    sheetNames.forEach((sheetName, index) => {
      console.log(`Processing sheet: ${sheetName}`);
      
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, {
        header: options.header || 1,
        defval: options.defaultValue || '',
        blankrows: options.includeBlankRows || false,
        raw: options.raw || false
      });

      console.log(`Sheet "${sheetName}" contains ${jsonData.length} rows`);

      if (options.singleSheet && sheetNames.length === 1) {
        result = jsonData;
      } else if (options.mergeSheets) {
        allData = allData.concat(jsonData.map(row => ({
          ...row,
          _sheet: sheetName
        })));
      } else {
        result[sheetName] = jsonData;
      }
    });

    if (options.mergeSheets) {
      result = allData;
    }

    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
    console.log(`JSON file saved: ${outputPath}`);
    
    if (Array.isArray(result)) {
      console.log(`Total records: ${result.length}`);
    } else if (typeof result === 'object') {
      const totalRecords = Object.values(result).reduce((sum, sheet) => {
        return sum + (Array.isArray(sheet) ? sheet.length : 0);
      }, 0);
      console.log(`Total records across all sheets: ${totalRecords}`);
    }

    return result;

  } catch (error) {
    console.error('Error converting XLSX to JSON:', error.message);
    throw error;
  }
}

function analyzeXlsxStructure(inputPath) {
  try {
    console.log(`Analyzing XLSX structure: ${inputPath}`);
    
    const workbook = XLSX.readFile(inputPath);
    const analysis = {
      fileName: path.basename(inputPath),
      sheets: []
    };

    workbook.SheetNames.forEach(sheetName => {
      const worksheet = workbook.Sheets[sheetName];
      const range = XLSX.utils.decode_range(worksheet['!ref'] || 'A1:A1');
      
      const headers = [];
      for (let col = range.s.c; col <= range.e.c; col++) {
        const cellAddress = XLSX.utils.encode_cell({ r: range.s.r, c: col });
        const cell = worksheet[cellAddress];
        headers.push(cell ? cell.v : `Column${col + 1}`);
      }

      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
      
      analysis.sheets.push({
        name: sheetName,
        rows: range.e.r + 1,
        columns: range.e.c + 1,
        headers: headers,
        sampleData: jsonData.slice(0, 3)
      });
    });

    console.log('\n=== XLSX Structure Analysis ===');
    console.log(JSON.stringify(analysis, null, 2));
    
    return analysis;

  } catch (error) {
    console.error('Error analyzing XLSX:', error.message);
    throw error;
  }
}

function convertWithMapping(inputPath, outputPath, columnMapping = {}) {
  try {
    console.log('Converting with column mapping...');
    
    const workbook = XLSX.readFile(inputPath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    const rawData = XLSX.utils.sheet_to_json(worksheet);
    
    const mappedData = rawData.map((row, index) => {
      const mappedRow = {
        custom_id: `request-${index + 1}`,
        ...Object.keys(columnMapping).reduce((acc, newKey) => {
          const oldKey = columnMapping[newKey];
          acc[newKey] = row[oldKey] || '';
          return acc;
        }, {})
      };
      
      return mappedRow;
    });

    fs.writeFileSync(outputPath, JSON.stringify(mappedData, null, 2));
    console.log(`Mapped JSON saved: ${outputPath}`);
    console.log(`Applied mapping:`, columnMapping);
    
    return mappedData;

  } catch (error) {
    console.error('Error converting with mapping:', error.message);
    throw error;
  }
}

if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.log(`
Usage: node xlsx-to-json.js <input.xlsx> <output.json> [options]

Commands:
  analyze <input.xlsx>                    - Analyze XLSX structure
  convert <input.xlsx> <output.json>     - Convert to JSON
  map <input.xlsx> <output.json>         - Convert with column mapping

Options:
  --single-sheet                         - Output single array (for single sheet files)
  --merge-sheets                         - Merge all sheets into single array
  --raw                                  - Keep raw values (don't format)
  --include-blanks                       - Include blank rows

Examples:
  node xlsx-to-json.js analyze data.xlsx
  node xlsx-to-json.js convert data.xlsx output.json --single-sheet
  node xlsx-to-json.js map data.xlsx output.json
    `);
    process.exit(1);
  }

  const command = args[0];
  const inputFile = args[1];
  const outputFile = args[2];

  const options = {
    singleSheet: args.includes('--single-sheet'),
    mergeSheets: args.includes('--merge-sheets'),
    raw: args.includes('--raw'),
    includeBlankRows: args.includes('--include-blanks')
  };

  try {
    if (command === 'analyze') {
      analyzeXlsxStructure(inputFile);
    } else if (command === 'convert') {
      xlsxToJson(inputFile, outputFile, options);
    } else if (command === 'map') {
      console.log('Please modify the columnMapping object in the script for your specific needs:');
      const sampleMapping = {
        'question': 'Question',
        'llm_response': 'Response', 
        'final_score': 'Score',
        'category': 'Category'
      };
      console.log('Sample mapping:', JSON.stringify(sampleMapping, null, 2));
      convertWithMapping(inputFile, outputFile, sampleMapping);
    } else {
      console.error('Unknown command. Use: analyze, convert, or map');
      process.exit(1);
    }
  } catch (error) {
    console.error('Script failed:', error.message);
    process.exit(1);
  }
}

module.exports = {
  xlsxToJson,
  analyzeXlsxStructure,
  convertWithMapping
};
