import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    user: null
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token)
  },
  actions: {
    setSession(payload) {
      this.token = payload.token
      this.user = payload.user
    },
    clearSession() {
      this.token = ''
      this.user = null
    }
  }
})
