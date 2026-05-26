import { http } from './http'

export function createCourse(data) {
  return http.post('/courses', data)
}

export function getCourses() {
  return http.get('/courses')
}

export function deleteCourse(id, scope = 'one', options = {}) {
  const params = { scope }
  if (options.occurrenceStart) {
    params.occurrence_start = options.occurrenceStart
  }
  return http.delete(`/courses/${id}`, { params })
}

export function getCourseTemplate() {
  return http.get('/courses/template')
}

export function importCourses(formData) {
  return http.post('/courses/import', formData)
}

export function recognizeCourseImage(formData) {
  return http.post('/courses/ocr', formData)
}
