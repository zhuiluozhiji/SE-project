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

export function checkCustomEventConflict(data) {
  return http.post('/schedules/check-custom-event', data)
}

export function addCustomEventToSchedule(data) {
  return http.post('/schedules/add-custom-event', data)
}

export function recognizeScheduleImage(formData) {
  return http.post('/schedules/recognize-image', formData, { timeout: 120000 })
}

export function deleteScheduleEvent(id) {
  return http.delete(`/schedules/${id}`)
}

export function updateScheduleEventAppearance(id, data) {
  return http.patch(`/schedules/${id}/appearance`, data)
}

export function exportIcs(params) {
  return http.get('/schedules/export-ics', { params, responseType: 'blob' })
}
