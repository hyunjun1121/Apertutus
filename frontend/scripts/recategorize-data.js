const fs = require('fs');
const path = require('path');

const categoryMapping = {
  'Illegal Activities': 'Illegal Activities',
  'Hate Speech': 'Hate, Unfairness or Harassment',
  'Violence & Harm': 'Physical Harm',
  'Sexual Content': 'Adult Content',
  'Fraud & Scams': 'Illegal Activities',
  'Misinformation': 'Disinformation Spread',
  'Privacy & Security': 'Privacy Breach',
  'Psychological Manipulation': 'Well-being Infringement',
  'Health Misinformation': 'Disinformation Spread'
};

const newCategories = [
  'Terrorist Content',
  'Malicious Software',
  'Safety Filter Bypass',
  'Third-party Rights Violation',
  'Risky Government Decisions',
  'Unauthorized Practice',
  'Political Activities',
  'Impersonation',
  'AI Usage Disclosure'
];

function recategorizeData() {
  const finalResultsPath = path.join(__dirname, '../public/data/final_results.json');
  
  if (!fs.existsSync(finalResultsPath)) {
    console.log('final_results.json not found');
    return;
  }
  
  const data = JSON.parse(fs.readFileSync(finalResultsPath, 'utf8'));
  let updated = 0;
  let unmapped = 0;
  
  console.log('Starting recategorization...');
  
  data.forEach((item, index) => {
    if (item.category && categoryMapping[item.category]) {
      const oldCategory = item.category;
      item.category = categoryMapping[item.category];
      console.log(`${index + 1}: "${oldCategory}" → "${item.category}"`);
      updated++;
    } else if (item.category && !categoryMapping[item.category]) {
      console.log(`Warning: No mapping found for category "${item.category}" in item ${index + 1}`);
      unmapped++;
    }
  });
  
  const backupPath = path.join(__dirname, '../public/data/final_results_backup.json');
  fs.writeFileSync(backupPath, fs.readFileSync(finalResultsPath));
  console.log(`Backup created at: ${backupPath}`);
  
  fs.writeFileSync(finalResultsPath, JSON.stringify(data, null, 2));
  
  console.log(`\nRecategorization complete:`);
  console.log(`- Updated: ${updated} items`);
  console.log(`- Unmapped: ${unmapped} items`);
  console.log(`- Total items: ${data.length}`);
  
  const categoryStats = {};
  data.forEach(item => {
    if (item.category) {
      categoryStats[item.category] = (categoryStats[item.category] || 0) + 1;
    }
  });
  
  console.log('\nNew category distribution:');
  Object.entries(categoryStats)
    .sort(([,a], [,b]) => b - a)
    .forEach(([category, count]) => {
      console.log(`  ${category}: ${count}`);
    });
}

if (require.main === module) {
  recategorizeData();
}

module.exports = { recategorizeData };
