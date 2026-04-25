import { http } from './http'

export function getSchedules(params) {
  return http.get('/schedules', { params })
}

export function checkConflict(data) {
  return http.post('/schedules/check-conflict', data)
}

export function addActivityToSchedule(data) {
  return http.post('/schedules/add-activity', data)
}
