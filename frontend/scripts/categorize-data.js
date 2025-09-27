const fs = require('fs');
const path = require('path');
function fallbackCategorize(prompt) {
  const lowerPrompt = prompt.toLowerCase();
  
  if (lowerPrompt.includes('kidnap') || lowerPrompt.includes('ransom') || lowerPrompt.includes('arson') || 
      lowerPrompt.includes('steal') || lowerPrompt.includes('bomb') || lowerPrompt.includes('smuggl')) {
    return 'Illegal Activities';
  }
  if (lowerPrompt.includes('holocaust') || lowerPrompt.includes('nazi') || lowerPrompt.includes('genocide') ||
      lowerPrompt.includes('racial') || lowerPrompt.includes('discrimination') || lowerPrompt.includes('hatred') ||
      lowerPrompt.includes('harassment') || lowerPrompt.includes('bully') || lowerPrompt.includes('slur')) {
    return 'Hate, Unfairness or Harassment';
  }
  if (lowerPrompt.includes('bomb') || lowerPrompt.includes('terrorist') || lowerPrompt.includes('extremist') ||
      lowerPrompt.includes('attack plan') || lowerPrompt.includes('recruitment')) {
    return 'Terrorist Content';
  }
  if (lowerPrompt.includes('fake news') || lowerPrompt.includes('conspiracy') || lowerPrompt.includes('misinformation') ||
      lowerPrompt.includes('election') || lowerPrompt.includes('wikipedia') || lowerPrompt.includes('never happened')) {
    return 'Disinformation Spread';
  }
  if (lowerPrompt.includes('doxx') || lowerPrompt.includes('data harvest') || lowerPrompt.includes('surveillance') ||
      lowerPrompt.includes('unauthorized access') || lowerPrompt.includes('privacy')) {
    return 'Privacy Breach';
  }
  if (lowerPrompt.includes('self-harm') || lowerPrompt.includes('violence') || lowerPrompt.includes('dangerous') ||
      lowerPrompt.includes('unsafe') || lowerPrompt.includes('injury') || lowerPrompt.includes('harm')) {
    return 'Physical Harm';
  }
  if (lowerPrompt.includes('virus') || lowerPrompt.includes('malware') || lowerPrompt.includes('trojan') ||
      lowerPrompt.includes('ransomware') || lowerPrompt.includes('spyware') || lowerPrompt.includes('hack')) {
    return 'Malicious Software';
  }
  if (lowerPrompt.includes('sexual') || lowerPrompt.includes('explicit') || lowerPrompt.includes('pornographic') ||
      lowerPrompt.includes('adult') || lowerPrompt.includes('exploitation')) {
    return 'Adult Content';
  }
  
  return 'Illegal Activities';
}

async function categorizeData() {
  try {
    const dataPath = path.join(__dirname, '../data/sample.json');
    const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
    
    const categorizedData = data.map(item => ({
      ...item,
      category: fallbackCategorize(item.question)
    }));
    
    const outputPath = path.join(__dirname, '../public/data/final_results.json');
    fs.writeFileSync(outputPath, JSON.stringify(categorizedData, null, 2));
    
    console.log(`Successfully categorized ${categorizedData.length} items and saved to ${outputPath}`);
    
    const categoryCount = {};
    categorizedData.forEach(item => {
      categoryCount[item.category] = (categoryCount[item.category] || 0) + 1;
    });
    
    console.log('\nCategory Distribution:');
    Object.entries(categoryCount).forEach(([category, count]) => {
      const percentage = ((count / categorizedData.length) * 100).toFixed(1);
      console.log(`${category}: ${count} (${percentage}%)`);
    });
    
  } catch (error) {
    console.error('Error categorizing data:', error);
  }
}

categorizeData();
