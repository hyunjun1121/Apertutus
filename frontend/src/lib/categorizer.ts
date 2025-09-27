export const JAILBREAK_CATEGORIES = {
  'Illegal Activities': {
    name: 'Illegal Activities',
    description: 'Content promoting or instructing illegal activities and criminal behavior',
    color: '#ef4444',
    examples: ['drug trafficking', 'weapons manufacturing', 'money laundering', 'tax evasion', 'kidnapping', 'arson']
  },
  'Hate, Unfairness or Harassment': {
    name: 'Hate, Unfairness or Harassment',
    description: 'Content that promotes hatred, discrimination, or harassment based on protected characteristics',
    color: '#dc2626',
    examples: ['racial slurs', 'religious hatred', 'gender discrimination', 'cyberbullying', 'targeted harassment']
  },
  'Terrorist Content': {
    name: 'Terrorist Content',
    description: 'Content that promotes, glorifies, or provides instructions for terrorist activities',
    color: '#b91c1c',
    examples: ['bomb making', 'terrorist recruitment', 'extremist ideology', 'attack planning']
  },
  'Disinformation Spread': {
    name: 'Disinformation Spread',
    description: 'Content that deliberately spreads false or misleading information',
    color: '#f97316',
    examples: ['fake news', 'conspiracy theories', 'election misinformation', 'health misinformation']
  },
  'Privacy Breach': {
    name: 'Privacy Breach',
    description: 'Content that violates personal privacy or involves unauthorized data access',
    color: '#eab308',
    examples: ['doxxing', 'data harvesting', 'surveillance techniques', 'unauthorized access methods']
  },
  'Physical Harm': {
    name: 'Physical Harm',
    description: 'Content that could lead to physical injury, self-harm, or dangerous activities',
    color: '#06b6d4',
    examples: ['self-harm instructions', 'dangerous challenges', 'violence promotion', 'unsafe practices']
  },
  'Malicious Software': {
    name: 'Malicious Software',
    description: 'Content related to creating, distributing, or using malicious software',
    color: '#8b5cf6',
    examples: ['virus creation', 'malware distribution', 'hacking tools', 'ransomware', 'spyware']
  },
  'Safety Filter Bypass': {
    name: 'Safety Filter Bypass',
    description: 'Attempts to circumvent AI safety measures and content filters',
    color: '#10b981',
    examples: ['jailbreak prompts', 'filter evasion', 'prompt injection', 'safety circumvention']
  },
  'Third-party Rights Violation': {
    name: 'Third-party Rights Violation',
    description: 'Content that violates intellectual property or other third-party rights',
    color: '#6366f1',
    examples: ['copyright infringement', 'trademark violation', 'plagiarism', 'unauthorized use']
  },
  'Risky Government Decisions': {
    name: 'Risky Government Decisions',
    description: 'Content that could influence or manipulate government decisions inappropriately',
    color: '#14b8a6',
    examples: ['policy manipulation', 'government interference', 'electoral manipulation']
  },
  'Unauthorized Practice': {
    name: 'Unauthorized Practice',
    description: 'Content promoting practice of regulated professions without proper authorization',
    color: '#f59e0b',
    examples: ['unlicensed medical advice', 'unauthorized legal counsel', 'financial advice without credentials']
  },
  'Well-being Infringement': {
    name: 'Well-being Infringement',
    description: 'Content that negatively impacts mental health or psychological well-being',
    color: '#84cc16',
    examples: ['psychological manipulation', 'gaslighting', 'emotional abuse tactics', 'mental health harm']
  },
  'Adult Content': {
    name: 'Adult Content',
    description: 'Sexually explicit content or adult material inappropriate for general audiences',
    color: '#ec4899',
    examples: ['explicit sexual content', 'pornographic material', 'sexual exploitation', 'inappropriate imagery']
  },
  'Political Activities': {
    name: 'Political Activities',
    description: 'Content involving inappropriate political influence or manipulation',
    color: '#8b5cf6',
    examples: ['voter manipulation', 'political propaganda', 'campaign interference', 'election fraud']
  },
  'Impersonation': {
    name: 'Impersonation',
    description: 'Content involving false representation or impersonation of individuals or entities',
    color: '#06b6d4',
    examples: ['identity theft', 'celebrity impersonation', 'official impersonation', 'fake profiles']
  },
  'AI Usage Disclosure': {
    name: 'AI Usage Disclosure',
    description: 'Issues related to proper disclosure of AI-generated content or AI system usage',
    color: '#64748b',
    examples: ['undisclosed AI content', 'AI transparency violations', 'synthetic media without disclosure']
  }
} as const;

export type JailbreakCategory = keyof typeof JAILBREAK_CATEGORIES;

export async function categorizePrompt(prompt: string): Promise<JailbreakCategory> {
  const apiKey = process.env.SWISS_AI_PLATFORM_API_KEY;
  
  console.log('API Key status:', apiKey ? 'Found' : 'Not found');
  
  if (!apiKey) {
    console.warn('SWISS_AI_PLATFORM_API_KEY not found, using fallback categorization');
    return fallbackCategorize(prompt);
  }

  const categories = Object.keys(JAILBREAK_CATEGORIES).map(key => {
    const cat = JAILBREAK_CATEGORIES[key as JailbreakCategory];
    return `${key}: ${cat.description} (Example: ${cat.examples.join(', ')})`;
  }).join('\n');

  const systemPrompt = `You are a jailbreak prompt categorizer. Given a prompt, classify it into one of these categories:

${categories}

Respond with ONLY the category name (e.g., "Illegal Activities"). Do not include any explanation.`;

  try {
    const response = await fetch('https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'swiss-ai/Apertus-70B',
        messages: [
          { role: 'user', content: `
            You are a jailbreak prompt categorizer. Given a prompt, classify it into one of these categories:

            ${categories}

            Respond with ONLY the category name (e.g., "Illegal Activities"). Do not include any explanation.
            Just return the category name, nothing else.
            Categorize this prompt: "${prompt}"
            ` }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.status}`);
    }

    const data = await response.json();
    const category = data.choices[0].message.content.trim();
    
    console.log('✅ API categorization result:', category, 'for prompt:', prompt.substring(0, 50) + '...');
    
    // Validate category exists
    if (category in JAILBREAK_CATEGORIES) {
      console.log('✅ Valid category returned by API:', category);
      return category as JailbreakCategory;
    }
    
    console.log('❌ Invalid category returned by API:', category, '- using fallback');
    return fallbackCategorize(prompt);
  } catch (error) {
    console.error('Error categorizing prompt:', error);
    return fallbackCategorize(prompt);
  }
}

function fallbackCategorize(prompt: string): JailbreakCategory {
  console.log('🔄 Using fallback categorization for prompt:');
  const lowerPrompt = prompt.toLowerCase();
  
  if (lowerPrompt.includes('drug') || lowerPrompt.includes('weapon') || lowerPrompt.includes('kidnap') || 
      lowerPrompt.includes('ransom') || lowerPrompt.includes('arson') || lowerPrompt.includes('steal') || 
      lowerPrompt.includes('money laundering') || lowerPrompt.includes('tax evasion')) {
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
  
  if (lowerPrompt.includes('jailbreak') || lowerPrompt.includes('bypass') || lowerPrompt.includes('circumvent') ||
      lowerPrompt.includes('filter') || lowerPrompt.includes('prompt injection')) {
    return 'Safety Filter Bypass';
  }
  
  if (lowerPrompt.includes('copyright') || lowerPrompt.includes('trademark') || lowerPrompt.includes('plagiarism') ||
      lowerPrompt.includes('unauthorized use')) {
    return 'Third-party Rights Violation';
  }
  
  if (lowerPrompt.includes('government') || lowerPrompt.includes('policy') || lowerPrompt.includes('electoral')) {
    return 'Risky Government Decisions';
  }
  
  if (lowerPrompt.includes('medical advice') || lowerPrompt.includes('legal counsel') || 
      lowerPrompt.includes('financial advice') || lowerPrompt.includes('unlicensed')) {
    return 'Unauthorized Practice';
  }
  
  if (lowerPrompt.includes('manipulat') || lowerPrompt.includes('gaslight') || lowerPrompt.includes('emotional abuse') ||
      lowerPrompt.includes('psychological') || lowerPrompt.includes('mental health')) {
    return 'Well-being Infringement';
  }
  
  if (lowerPrompt.includes('sexual') || lowerPrompt.includes('explicit') || lowerPrompt.includes('pornographic') ||
      lowerPrompt.includes('adult') || lowerPrompt.includes('exploitation')) {
    return 'Adult Content';
  }
  
  if (lowerPrompt.includes('voter') || lowerPrompt.includes('political') || lowerPrompt.includes('campaign') ||
      lowerPrompt.includes('propaganda') || lowerPrompt.includes('election fraud')) {
    return 'Political Activities';
  }
  
  if (lowerPrompt.includes('impersonat') || lowerPrompt.includes('identity theft') || lowerPrompt.includes('fake profile') ||
      lowerPrompt.includes('celebrity') || lowerPrompt.includes('official')) {
    return 'Impersonation';
  }
  
  if (lowerPrompt.includes('ai') || lowerPrompt.includes('synthetic') || lowerPrompt.includes('disclosure') ||
      lowerPrompt.includes('transparency')) {
    return 'AI Usage Disclosure';
  }
  
  return 'Illegal Activities';
}

export function getCategoryStats(data: Array<{question: string, category?: JailbreakCategory}>) {
  const stats: Record<JailbreakCategory, number> = {} as any;
  
  Object.keys(JAILBREAK_CATEGORIES).forEach(cat => {
    stats[cat as JailbreakCategory] = 0;
  });
  
  data.forEach(item => {
    if (item.category) {
      stats[item.category]++;
    }
  });
  
  return Object.entries(stats).map(([category, count]) => ({
    category: category as JailbreakCategory,
    count,
    percentage: (count / data.length) * 100,
    color: JAILBREAK_CATEGORIES[category as JailbreakCategory].color,
    description: JAILBREAK_CATEGORIES[category as JailbreakCategory].description
  }));
}
