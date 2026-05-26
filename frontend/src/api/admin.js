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

export function recognizeActivityImage(formData) {
  return http.post('/admin/activities/recognize-image', formData, { timeout: 120000 })
}

export function runCrawler(data) {
  return http.post('/admin/crawler/run', data)
}
