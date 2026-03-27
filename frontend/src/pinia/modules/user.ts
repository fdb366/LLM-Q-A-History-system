import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUserInfo } from '../../api/auth'

export interface UserInfo { 
  id: number
  username: string
  email: string
  role: string
  avatar_url: string | null
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = null
    localStorage.removeItem('token')
    userInfo.value = null
  }

  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      userInfo.value = await getUserInfo()
    } catch (error) {
      clearToken()
      throw error
    }
  }

  return {
    token,
    userInfo,
    setToken,
    clearToken,
    fetchUserInfo,
  }
})