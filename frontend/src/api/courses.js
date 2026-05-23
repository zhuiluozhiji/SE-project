import { http } from './http'

export function createCourse(data) {
  return http.post('/courses', data)
}

export function getCourses() {
  return http.get('/courses')
}

export function deleteCourse(id, scope = 'one') {
  return http.delete(`/courses/${id}`, { params: { scope } })
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
