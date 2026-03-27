import axios from '../utils/axios'

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export const conversationApi = {
  // 获取会话列表
  getList(): Promise<Conversation[]> {
    return axios.get('/chat/conversations')
  },
  // 创建会话
  create(data: { title: string }): Promise<Conversation> {
    return axios.post('/chat/conversations', data)
  },
  // 删除会话
  delete(id: number): Promise<any> {
    return axios.delete(`/chat/conversations/${id}`)
  },
  // 获取会话消息（需要定义 Message 类型）
  getMessages(convId: number): Promise<any[]> {
    return axios.get(`/chat/conversations/${convId}/messages`)
  }
}