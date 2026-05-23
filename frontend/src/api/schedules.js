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

export function exportSchedulesIcs() {
  return http.get('/schedules/export-ics')
}

export function downloadSchedulesIcsFile() {
  return http.get('/schedules/export-ics/file', { responseType: 'blob' })
}
