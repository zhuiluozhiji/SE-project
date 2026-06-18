import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi, getCurrentUser } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token)
  },
  actions: {
    async login(credentials) {
      const res = await loginApi(credentials)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
    },
    async register(payload) {
      const res = await registerApi(payload)
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
    },
    async fetchUser() {
      const res = await getCurrentUser()
      this.user = res.data
      localStorage.setItem('user', JSON.stringify(res.data))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
