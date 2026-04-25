import { http } from './http'

export function createCourse(data) {
  return http.post('/courses', data)
}

export function importCourses(formData) {
  return http.post('/courses/import', formData)
}

export function recognizeCourseImage(formData) {
  return http.post('/courses/ocr', formData)
}
