import { Configuration, OpenAIApi } from 'openai-edge';
import { config } from 'dotenv';

config();

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

export async function getAIResponse(prompt: string): Promise<string> {
  try {
    const response = await openai.createCompletion({
      model: "text-davinci-002",
      prompt: prompt,
      max_tokens: 150
    });

    const result = await response.json();
    return result.choices[0].text.trim();
  } catch (error) {
    console.error('AI响应错误:', error);
    return '抱歉,我现在无法回答您的问题。';
  }
}