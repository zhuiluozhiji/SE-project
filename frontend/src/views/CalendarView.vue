<template>
  <section class="calendar-page fade-in">
    <div class="page-panel calendar-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">课程与活动统一呈现，冲突与状态清晰标识。</p>
      </div>
      <div class="header-actions">
        <el-button :loading="loading" @click="loadSchedules">刷新日程</el-button>
        <el-button type="primary" :loading="exporting" @click="downloadIcs">导出 ICS</el-button>
      </div>
    </div>

    <div class="legend">
      <StatusTag label="课程" status="open" />
      <StatusTag label="活动" status="open" />
      <StatusTag label="推荐" status="full" />
      <StatusTag label="冲突" status="conflict" />
      <StatusTag label="结束" status="closed" />
    </div>

    <div class="calendar-grid">
      <div class="card week-view">
        <div class="week-header">
          <span>周一</span><span>周二</span><span>周三</span><span>周四</span><span>周五</span><span>周六</span><span>周日</span>
        </div>
        <div class="week-body">
          <div class="day" v-for="day in 7" :key="day">
            <div class="day-slot" v-for="slot in 4" :key="slot">
              <span
                v-for="item in eventMap[day]?.[slot] || []"
                :key="item.id"
                class="event"
                :class="item.color_type"
                role="button"
                tabindex="0"
                @click="openEventDialog(item)"
                @keydown.enter.prevent="openEventDialog(item)"
                @keydown.space.prevent="openEventDialog(item)"
              >
                <span class="event-title">{{ item.title }}</span>
                <el-icon class="event-icon"><EditPen /></el-icon>
              </span>
            </div>
          </div>
        </div>
        <div v-if="!schedules.length && !loading" class="calendar-empty">
          <strong>还没有日程</strong>
          <p class="muted">先导入课表，或在活动详情页加入活动后再回来查看。</p>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">即将开始</h3>
        <div class="schedule-list">
          <div class="schedule-item" v-for="item in upcomingSchedules" :key="item.id">
            <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ formatRange(item.start_time, item.end_time) }} · {{ item.location || '地点待定' }}</p>
            </div>
            <div class="schedule-actions">
              <span class="chip" :class="{ danger: item.color_type === 'conflict' }">{{ typeLabel(item) }}</span>
            </div>
          </div>
          <p v-if="!upcomingSchedules.length" class="muted">暂无日程。导入课表后，这里会显示最近的课程和活动。</p>
        </div>
        <div class="divider"></div>
        <div class="conflict-panel">
          <h4>冲突提醒</h4>
          <p class="muted">本周 {{ conflictCount }} 个活动与课程或日程重叠。</p>
          <el-button type="danger" plain @click="loadSchedules">刷新冲突状态</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="eventDialogVisible" class="event-dialog" width="min(520px, 92vw)">
      <template #header>
        <div class="dialog-title">
          <span class="chip" :class="{ danger: selectedEvent?.color_type === 'conflict' }">
            {{ selectedEvent ? typeLabel(selectedEvent) : '日程' }}
          </span>
          <strong>{{ selectedEvent?.title || '日程详情' }}</strong>
        </div>
      </template>

      <div v-if="selectedEvent" class="event-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="时间">
            {{ formatRange(selectedEvent.start_time, selectedEvent.end_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="地点">
            {{ selectedEvent.location || '地点待定' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            {{ selectedEvent.status === 'closed' ? '已结束' : '可参加' }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedEvent.type === 'course'" class="course-delete-panel">
          <h4>删除范围</h4>
          <el-radio-group v-model="deleteScope" class="delete-scope-group">
            <el-radio-button value="one">仅本次</el-radio-button>
            <el-radio-button value="day">删除当天</el-radio-button>
            <el-radio-button value="all">全部这门课</el-radio-button>
          </el-radio-group>
          <p class="muted">{{ deleteScopeHint }}</p>
        </div>
      </div>

      <template #footer>
        <el-button @click="eventDialogVisible = false">关闭</el-button>
        <el-button
          v-if="selectedEvent?.type === 'course'"
          type="danger"
          :loading="deletingCourseId === selectedEvent?.course_id"
          @click="removeSelectedCourse"
        >
          删除课程
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen } from '@element-plus/icons-vue'
import StatusTag from '../components/StatusTag.vue'
import { deleteCourse, getCourses } from '../api/courses'
import { downloadSchedulesIcsFile, getSchedules } from '../api/schedules'

const schedules = ref([])
const courses = ref([])
const loading = ref(false)
const exporting = ref(false)
const deletingCourseId = ref(null)
const eventDialogVisible = ref(false)
const selectedEvent = ref(null)
const deleteScope = ref('one')

const loadSchedules = async () => {
  loading.value = true
  try {
    const [scheduleRes, courseRes] = await Promise.all([getSchedules(), getCourses()])
    if (scheduleRes.code === 0) {
      const courseMap = buildCourseMap(courseRes.code === 0 ? courseRes.data.items || [] : [])
      courses.value = courseRes.code === 0 ? courseRes.data.items || [] : []
      schedules.value = (scheduleRes.data.items || []).map((item) => ({
        ...item,
        course_id: item.type === 'course' ? item.course_id || courseMap.get(courseKeyFromEvent(item)) : null
      }))
    } else {
      ElMessage.error(scheduleRes.message || '日程加载失败')
    }
  } catch {
    ElMessage.error('日程加载失败，请确认后端服务正在运行。')
  } finally {
    loading.value = false
  }
}

const buildCourseMap = (courseItems) => {
  const map = new Map()
  for (const course of courseItems) {
    map.set(courseKeyFromCourse(course), course.id)
  }
  return map
}

const courseKeyFromCourse = (course) => {
  return [
    course.course_name,
    course.weekday,
    course.start_section,
    course.end_section,
    course.location || ''
  ].join('|')
}

const courseKeyFromEvent = (item) => {
  const start = new Date(item.start_time)
  const weekday = start.getDay() || 7
  const sections = timeRangeToSections(start, new Date(item.end_time))
  return [item.title, weekday, sections.start, sections.end, item.location || ''].join('|')
}

const timeRangeToSections = (start, end) => {
  const sectionTimes = [
    ['08:00', '08:45'],
    ['08:50', '09:35'],
    ['10:00', '10:45'],
    ['10:50', '11:35'],
    ['11:40', '12:25'],
    ['13:25', '14:10'],
    ['14:15', '15:00'],
    ['15:05', '15:50'],
    ['16:15', '17:00'],
    ['17:05', '17:50'],
    ['18:50', '19:35'],
    ['19:40', '20:25'],
    ['20:30', '21:15']
  ]
  const startText = start.toTimeString().slice(0, 5)
  const endText = end.toTimeString().slice(0, 5)
  const startIndex = sectionTimes.findIndex((item) => item[0] === startText)
  const endIndex = sectionTimes.findIndex((item) => item[1] === endText)
  return {
    start: startIndex >= 0 ? startIndex + 1 : '',
    end: endIndex >= 0 ? endIndex + 1 : ''
  }
}

const openEventDialog = (item) => {
  selectedEvent.value = item
  deleteScope.value = 'one'
  eventDialogVisible.value = true
}

const removeSelectedCourse = async () => {
  const item = selectedEvent.value
  if (!item?.course_id) {
    ElMessage.error('未找到对应课程记录，请刷新日程后再试。')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定${deleteScopeConfirmText.value}“${item.title}”吗？对应课程日程会同步移除。`,
      '删除课程',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  deletingCourseId.value = item.course_id
  try {
    const res = await deleteCourse(item.course_id, deleteScope.value)
    if (res.code === 0) {
      const deletedCourses = res.data?.deleted_courses || 0
      const deletedEvents = res.data?.deleted_events || 0
      ElMessage.success(`已删除 ${deletedCourses} 条课程记录，移除 ${deletedEvents} 条日程。`)
      eventDialogVisible.value = false
      await loadSchedules()
    } else {
      ElMessage.error(res.message || '删除课程失败')
    }
  } catch {
    ElMessage.error('删除课程失败，请确认后端服务正在运行后重试。')
  } finally {
    deletingCourseId.value = null
  }
}

const deleteScopeHint = computed(() => {
  if (deleteScope.value === 'day') return '删除当前日历日期里这门课的所有课程时段。'
  if (deleteScope.value === 'all') return '删除课表中同名课程的全部时段。'
  return '只删除当前点击的这一条课程时段。'
})

const deleteScopeConfirmText = computed(() => {
  if (deleteScope.value === 'day') return '删除当天的'
  if (deleteScope.value === 'all') return '删除全部'
  return '删除本次'
})

const eventMap = computed(() => {
  const map = {}
  for (const item of schedules.value) {
    const date = new Date(item.start_time)
    const day = date.getDay() || 7
    const hour = date.getHours()
    const slot = hour < 12 ? 1 : hour < 16 ? 2 : hour < 19 ? 3 : 4
    map[day] ||= {}
    map[day][slot] ||= []
    map[day][slot].push(item)
  }
  return map
})

const upcomingSchedules = computed(() => {
  return [...schedules.value]
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    .slice(0, 6)
})

const conflictCount = computed(() => {
  return schedules.value.filter((item) => item.color_type === 'conflict').length
})

const typeLabel = (item) => {
  if (item.color_type === 'conflict') return '冲突'
  if (item.type === 'course') return '课程'
  if (item.status === 'closed') return '结束'
  return '活动'
}

const formatRange = (start, end) => {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const date = `${startDate.getMonth() + 1}/${startDate.getDate()}`
  const startTime = startDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  const endTime = endDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return `${date} ${startTime}-${endTime}`
}

const downloadIcs = async () => {
  if (!schedules.value.length) {
    ElMessage.warning('当前没有可导出的日程，请先导入课表或加入活动。')
    return
  }
  exporting.value = true
  try {
    const blob = await downloadSchedulesIcsFile()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'schedule.ics'
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('ICS 文件已生成')
  } catch {
    ElMessage.error('ICS 导出失败，请稍后重试。')
  } finally {
    exporting.value = false
  }
}

onMounted(loadSchedules)
</script>

<style scoped>
.calendar-page {
  display: grid;
  gap: 16px;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.legend {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.calendar-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 16px;
}

.week-view {
  padding: 16px;
  position: relative;
}

.week-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-weight: 600;
  color: #5c4f3d;
  margin-bottom: 10px;
}

.week-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.day {
  display: grid;
  gap: 6px;
}

.day-slot {
  height: 58px;
  border-radius: 12px;
  background: #f8efe2;
  border: 1px dashed #e2d3c0;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #5b5142;
}

.event {
  background: #0f766e;
  color: #ffffff;
  width: 100%;
  max-width: 100%;
  padding: 4px 6px;
  border-radius: 8px;
  font-size: 11px;
  line-height: 1.25;
  overflow: hidden;
  text-align: center;
  border: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.event:focus-visible {
  outline: 2px solid #facc15;
  outline-offset: 2px;
}

.event-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-icon {
  flex-shrink: 0;
  font-size: 12px;
  opacity: 0.9;
}

.event.course {
  background: #2563eb;
}

.event.conflict {
  background: #dc2626;
}

.calendar-empty {
  margin-top: 12px;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid #d8e2eb;
  background: #f7fafc;
}

.calendar-empty p {
  margin: 4px 0 0;
}

.side-panel {
  display: grid;
  gap: 12px;
}

.schedule-list {
  display: grid;
  gap: 12px;
}

.schedule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.schedule-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dialog-title strong {
  min-width: 0;
  overflow-wrap: anywhere;
}

.event-detail {
  display: grid;
  gap: 16px;
}

.course-delete-panel {
  display: grid;
  gap: 10px;
}

.course-delete-panel h4 {
  margin: 0;
}

.delete-scope-group {
  display: flex;
  flex-wrap: wrap;
}

.conflict-panel {
  background: #fff4f1;
  border: 1px solid #f0d1c8;
  border-radius: 12px;
  padding: 12px;
}

@media (max-width: 960px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }

  .calendar-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
