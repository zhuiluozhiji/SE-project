import { http } from './http'

export function login(data) {
  return http.post('/auth/login', data)
}

export function getCurrentUser() {
  return http.get('/users/me')
}
