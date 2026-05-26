import { http } from './http'

export function getActivities(params) {
  return http.get('/activities', { params })
}

export function getActivityFilterOptions() {
  return http.get('/activities/filter-options')
}

export function getActivityDetail(id) {
  return http.get(`/activities/${id}`)
}

export function recordActivityInteraction(id, data) {
  return http.post(`/activities/${id}/interactions`, data)
}
