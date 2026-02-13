import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, user, conversationHistory } = body;

    // Call your ML model
    const mlResponse = await fetch(process.env.ML_MODEL_ENDPOINT!, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(process.env.ML_MODEL_API_KEY && {
          'Authorization': `Bearer ${process.env.ML_MODEL_API_KEY}`
        })
      },
      body: JSON.stringify({
        query: message,
        user: user,
        history: conversationHistory || []
      })
    });

    if (!mlResponse.ok) {
      throw new Error(`ML Model Error: ${mlResponse.statusText}`);
    }

    const mlData = await mlResponse.json();

    return NextResponse.json({
      reply: mlData.response || mlData.answer,
      metadata: mlData.metadata || {},
      confidence: mlData.confidence
    });

  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { error: 'Failed to process message' },
      { status: 500 }
    );
  }
}