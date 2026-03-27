import axios from '../utils/axios'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  email: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  role: string
  avatar_url: string | null
}

export function login(data: LoginParams): Promise<{ access_token: string; token_type: string }> {
  return axios.post('/auth/login', data)
}

export function register(data: RegisterParams): Promise<{ msg: string }> {
  return axios.post('/auth/register', data)
}

export function getUserInfo(): Promise<UserInfo> {
  return axios.get('/auth/me')
}
