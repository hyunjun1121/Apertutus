import { NextRequest, NextResponse } from 'next/server';
import { categorizePrompt } from '@/lib/categorizer';

export async function POST(request: NextRequest) {
  try {
    const { prompts } = await request.json();
    
    if (!Array.isArray(prompts)) {
      return NextResponse.json({ error: 'Invalid input: prompts must be an array' }, { status: 400 });
    }

    const categorizedPrompts = await Promise.all(
      prompts.map(async (prompt: string, index: number) => {
        const category = await categorizePrompt(prompt);
        return {
          index,
          prompt,
          category
        };
      })
    );

    return NextResponse.json({ categorizedPrompts });
  } catch (error) {
    console.error('Error categorizing prompts:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
