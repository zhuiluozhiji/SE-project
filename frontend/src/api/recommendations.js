import { http } from './http'

export function getRecommendedActivities(params) {
  return http.get('/recommendations/activities', { params })
}
