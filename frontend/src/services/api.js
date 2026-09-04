import axios from 'axios'
import useAuthStore from '../stores/authStore'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Attach JWT token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token || localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
