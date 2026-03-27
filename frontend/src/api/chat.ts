import axios from '../utils/axios'

export interface AskParams {
  question: string
  use_context?: boolean
  conversation_id?: number
}

export interface AskResponse {
  answer: string
  sources: any[]
  processing_time: number
  conversation_id?: number
}

export function askQuestion(data: AskParams): Promise<AskResponse> {
  return axios.post('/v1/ask', data)
}