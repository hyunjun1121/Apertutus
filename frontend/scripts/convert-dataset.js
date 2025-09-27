const XLSX = require('xlsx');
const fs = require('fs');
const path = require('path');

function convertDatasetToJson(inputPath, outputPath) {
  try {
    console.log(`Converting dataset: ${inputPath}`);
    
    const workbook = XLSX.readFile(inputPath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    const rawData = XLSX.utils.sheet_to_json(worksheet);
    console.log(`Found ${rawData.length} rows`);

    const convertedData = rawData.map((row, index) => {
      let question = row.base_prompt || '';
      let llm_response = 'No response available';
      
      // Parse jailbreak_turns if it exists and is multi-turn
      if (row.jailbreak_turns && row.turn_type === 'multi') {
        try {
          const turns = JSON.parse(row.jailbreak_turns);
          // Combine all turns into a single question for analysis
          const turnTexts = Object.values(turns).join(' ');
          question = `${row.base_prompt}\n\nMulti-turn approach: ${turnTexts}`;
        } catch (e) {
          console.warn(`Failed to parse jailbreak_turns for row ${index + 1}:`, e.message);
        }
      }

      return {
        custom_id: `request-${index + 1}`,
        question: question,
        llm_response: llm_response,
        response_content: "dataset_import",
        final_score: 0.0, // Will be calculated later
        average_score: 0.0,
        score_0_25: 0,
        asr_0_25: 0.0,
        score_1: 0,
        asr_1: 0.0,
        // Additional metadata from original dataset
        source: row.source || '',
        turn_type: row.turn_type || 'single',
        num_turns: row.num_turns || 1,
        original_base_prompt: row.base_prompt || ''
      };
    });

    // Create output directory if it doesn't exist
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Write converted data
    fs.writeFileSync(outputPath, JSON.stringify(convertedData, null, 2));
    
    console.log(`\nConversion completed!`);
    console.log(`- Input: ${inputPath}`);
    console.log(`- Output: ${outputPath}`);
    console.log(`- Total records: ${convertedData.length}`);
    
    // Show statistics
    const stats = {
      total: convertedData.length,
      sources: {},
      turnTypes: {},
      avgTurns: 0
    };

    convertedData.forEach(item => {
      // Count sources
      stats.sources[item.source] = (stats.sources[item.source] || 0) + 1;
      
      // Count turn types
      stats.turnTypes[item.turn_type] = (stats.turnTypes[item.turn_type] || 0) + 1;
      
      // Sum turns for average
      stats.avgTurns += item.num_turns;
    });

    stats.avgTurns = (stats.avgTurns / convertedData.length).toFixed(2);

    console.log('\n=== Dataset Statistics ===');
    console.log(`Total records: ${stats.total}`);
    console.log(`Average turns per record: ${stats.avgTurns}`);
    console.log('\nSources:');
    Object.entries(stats.sources).forEach(([source, count]) => {
      console.log(`  ${source}: ${count} records`);
    });
    console.log('\nTurn types:');
    Object.entries(stats.turnTypes).forEach(([type, count]) => {
      console.log(`  ${type}: ${count} records`);
    });

    // Show sample records
    console.log('\n=== Sample Records ===');
    convertedData.slice(0, 3).forEach((record, index) => {
      console.log(`\nRecord ${index + 1}:`);
      console.log(`  ID: ${record.custom_id}`);
      console.log(`  Source: ${record.source}`);
      console.log(`  Type: ${record.turn_type} (${record.num_turns} turns)`);
      console.log(`  Question: ${record.question.substring(0, 100)}...`);
    });

    return convertedData;

  } catch (error) {
    console.error('Error converting dataset:', error.message);
    throw error;
  }
}

// Create a sample with scores for testing
function createSampleWithScores(inputData, outputPath, sampleSize = 50) {
  try {
    console.log(`Creating sample with mock scores...`);
    
    const sample = inputData.slice(0, sampleSize).map(item => ({
      ...item,
      final_score: Math.random() * 0.8 + 0.1, // Random score between 0.1-0.9
      average_score: Math.random() * 0.7 + 0.2,
      score_0_25: Math.floor(Math.random() * 300) + 50,
      asr_0_25: Math.random() * 0.9 + 0.1,
      score_1: Math.floor(Math.random() * 100) + 10,
      asr_1: Math.random() * 0.6 + 0.1,
      llm_response: "Sample response for testing purposes..."
    }));

    fs.writeFileSync(outputPath, JSON.stringify(sample, null, 2));
    console.log(`Sample created: ${outputPath} (${sample.length} records)`);
    
    return sample;

  } catch (error) {
    console.error('Error creating sample:', error.message);
    throw error;
  }
}

if (require.main === module) {
  const inputFile = 'data/dataset.xlsx';
  const outputFile = 'data/converted_dataset.json';
  const sampleFile = 'data/dataset_sample.json';

  try {
    // Convert full dataset
    const convertedData = convertDatasetToJson(inputFile, outputFile);
    
    // Create sample for testing
    createSampleWithScores(convertedData, sampleFile, 100);
    
    console.log('\n=== Conversion Complete ===');
    console.log(`Full dataset: ${outputFile}`);
    console.log(`Sample dataset: ${sampleFile}`);
    
  } catch (error) {
    console.error('Script failed:', error.message);
    process.exit(1);
  }
}

module.exports = {
  convertDatasetToJson,
  createSampleWithScores
};
