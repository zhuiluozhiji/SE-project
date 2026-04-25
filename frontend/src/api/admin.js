import { http } from './http'

export function createActivity(data) {
  return http.post('/admin/activities', data)
}

export function updateActivity(id, data) {
  return http.put(`/admin/activities/${id}`, data)
}

export function offlineActivity(id) {
  return http.delete(`/admin/activities/${id}`)
}

export function runCrawler(data) {
  return http.post('/admin/crawler/run', data)
}
