import { useUserStore } from '@/pinia/modules/user'
import { ElMessage } from 'element-plus'

// 检查用户是否已认证
export function useAuth() {
  const userStore = useUserStore()

  const isAuthenticated = () => {
    return !!userStore.token
  }

  const requireAuth = () => {
    if (!userStore.token) {
      ElMessage.error('请先登录')
      return false
    }
    return true
  }

  return {
    isAuthenticated,
    requireAuth,
  }
}
