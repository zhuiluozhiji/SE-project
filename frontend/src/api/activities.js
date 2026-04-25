import { http } from './http'

export function getActivities(params) {
  return http.get('/activities', { params })
}

export function getActivityDetail(id) {
  return http.get(`/activities/${id}`)
}
