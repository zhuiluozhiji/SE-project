<template>
  <section class="calendar-page fade-in">
    <div class="page-panel calendar-header">
      <div>
        <h2 class="page-title">个人日历</h2>
        <p class="muted">
          第 {{ weekNumber }} 周（{{ weekParity }}）｜
          课程与活动统一呈现，冲突与状态清晰标识
        </p>
      </div>
      <div class="header-actions">
        <el-button-group size="small">
          <el-button :type="showOdd ? 'primary' : 'default'" @click="showOdd = true">单周</el-button>
          <el-button :type="!showOdd ? 'primary' : 'default'" @click="showOdd = false">双周</el-button>
        </el-button-group>
        <el-button-group>
          <el-button @click="prevWeek">上一周</el-button>
          <el-button type="primary" plain>{{ weekRangeText }}</el-button>
          <el-button @click="nextWeek">下一周</el-button>
        </el-button-group>
        <el-button @click="fetchSchedules">刷新</el-button>
        <el-button type="primary" @click="exportIcs" :loading="exporting">导出 ICS</el-button>
      </div>
    </div>

    <div class="legend">
      <span class="legend-item"><span class="dot course"></span>课程</span>
      <span class="legend-item"><span class="dot activity"></span>活动</span>
      <span class="legend-item"><span class="dot recommended"></span>推荐</span>
      <span class="legend-item"><span class="dot conflict"></span>冲突</span>
      <span class="legend-item"><span class="dot exam"></span>考试</span>
    </div>

    <div v-loading="loading" class="main-grid">
      <div class="card timetable-card">
        <div class="timeline-wrap">
          <!-- 时间标尺 + 7 天列 -->
          <div class="timeline-header">
            <div class="ruler-spacer"></div>
            <div
              v-for="d in weekDays"
              :key="d.label"
              class="day-head"
              :class="{ today: d.isToday }"
            >
              <strong>{{ d.label }}</strong>
              <small>{{ d.date }}</small>
            </div>
          </div>
          <div class="timeline-body">
            <!-- 左侧时间标尺 -->
            <div class="time-ruler">
              <div
                v-for="h in hourMarkers"
                :key="h.label"
                class="ruler-tick"
                :style="{ top: h.top + 'px' }"
              >
                {{ h.label }}
              </div>
            </div>
            <!-- 7 天列，事件绝对定位 -->
            <div
              v-for="(day, di) in weekDays"
              :key="di"
              class="day-col"
            >
              <div class="day-bg">
                <div
                  v-for="h in hourMarkers"
                  :key="h.label"
                  class="bg-line"
                  :style="{ top: h.top + 'px' }"
                ></div>
              </div>
              <div
                v-for="event in getTimelineEvents(di)"
                :key="event.id || event.title"
                class="timeline-event"
                :class="[event.type || 'course', { conflict: event.conflict }]"
                :style="{
                  top: event._top + 'px',
                  height: event._height + 'px',
                  left: event._left + '%',
                  width: event._width + '%'
                }"
              >
                <div class="event-name">{{ event.title }}</div>
                <div class="event-time">{{ event.startTime }}-{{ event.endTime }}</div>
                <div class="event-meta" v-if="event.teacher">{{ event.teacher }}</div>
                <div class="event-meta">{{ event.location || '' }}</div>
                <span v-if="event.weekType" class="week-tag">{{ event.weekType }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card side-panel">
        <h3 class="section-title">本周课程一览</h3>
        <div v-if="weekCourses.length === 0" class="empty-hint">
          <p class="muted">本周暂无课程</p>
        </div>
        <div class="course-list" v-else>
          <div class="course-item" v-for="c in weekCourses" :key="c.id || c.title">
            <div class="course-item-left">
              <span class="dot" :class="c.type || 'course'"></span>
              <div>
                <strong>{{ c.title }}</strong>
                <p class="muted">{{ c.teacher }} · {{ c.location }}</p>
              </div>
            </div>
            <div class="course-item-right">
              <span class="muted">{{ c.dayLabel }} {{ c.timeLabel }}</span>
              <span class="chip" v-if="c.weekType">{{ c.weekType }}</span>
            </div>
          </div>
        </div>

        <div class="divider"></div>
        <h3 class="section-title">即将开始</h3>
        <div v-if="upcoming.length === 0" class="empty-hint">
          <p class="muted">本周暂无活动安排</p>
        </div>
        <div class="schedule-list" v-else>
          <div class="schedule-item" v-for="item in upcoming" :key="item.id || item.title">
            <div>
              <strong>{{ item.title }}</strong>
              <p class="muted">{{ formatDate(item.start_time || item.time) }} · {{ item.location || '--' }}</p>
            </div>
            <span class="chip" :class="item.type">{{ typeLabel(item) }}</span>
          </div>
        </div>

        <div class="divider"></div>
        <div class="conflict-panel" v-if="conflictEvents.length > 0">
          <h4>冲突提醒</h4>
          <p class="muted">本周 {{ conflictEvents.length }} 个活动与课程时间重叠。</p>
          <el-button type="danger" plain size="small" @click="conflictVisible = true">查看冲突详情</el-button>
        </div>
        <div class="conflict-panel safe" v-else>
          <h4>冲突提醒</h4>
          <p class="muted">本周暂无冲突，日程安排良好。</p>
        </div>

        <div class="divider"></div>
        <h3 class="section-title">近期考试</h3>
        <div v-if="exams.length === 0" class="empty-hint">
          <p class="muted">暂无临近考试</p>
        </div>
        <div class="exam-list" v-else>
          <div class="exam-item" v-for="e in exams" :key="e.title">
            <strong>{{ e.title }}</strong>
            <p class="muted">{{ e.examDate }} · {{ e.location }}</p>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="conflictVisible" title="冲突明细" width="520px">
      <div class="conflict-list">
        <div class="conflict-item" v-for="item in conflictEvents" :key="item.id || item.title">
          <strong>{{ item.title }}</strong>
          <p class="muted">{{ formatDate(item.start_time || item.time) }} · {{ item.location || '--' }}</p>
        </div>
      </div>
    </el-dialog>

    <div v-if="error" class="empty-state">
      <p>加载失败</p>
      <small>{{ error }}</small>
      <el-button size="small" @click="fetchSchedules">重试</el-button>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedules } from '../api/schedules'

const loading = ref(false)
const error = ref('')
const exporting = ref(false)
const conflictVisible = ref(false)
const allEvents = ref([])
const weekOffset = ref(0)
const showOdd = ref(true)

const PX_PER_HOUR = 80
const START_HOUR = 8   // 08:00
const END_HOUR = 21.5  // 21:30

const parseTime = (t) => {
  if (!t) return 0
  const parts = t.split(':')
  return parseInt(parts[0]) * 60 + parseInt(parts[1])
}

const hourMarkers = computed(() => {
  const markers = []
  const totalMinutes = (END_HOUR - START_HOUR) * 60
  const totalPx = totalMinutes / 60 * PX_PER_HOUR
  for (let h = START_HOUR; h <= Math.floor(END_HOUR); h++) {
    const top = (h - START_HOUR) * PX_PER_HOUR
    if (top <= totalPx) {
      markers.push({ label: `${String(h).padStart(2, '0')}:00`, top })
    }
  }
  return markers
})

const timelineHeight = computed(() => (END_HOUR - START_HOUR) * PX_PER_HOUR)

// 重叠检测：按开始时间排序，贪心分配水平轨道
const layoutEvents = (events) => {
  if (!events.length) return events
  const sorted = [...events].sort((a, b) => a._startMin - b._startMin)
  const tracks = [] // 每条轨道的结束时间（分钟）
  sorted.forEach((e) => {
    let placed = false
    for (let i = 0; i < tracks.length; i++) {
      if (tracks[i] <= e._startMin) {
        tracks[i] = e._endMin
        e._track = i
        placed = true
        break
      }
    }
    if (!placed) {
      e._track = tracks.length
      tracks.push(e._endMin)
    }
  })
  const totalTracks = tracks.length || 1
  const gap = 2 // 百分比间距
  sorted.forEach((e) => {
    e._left = (e._track / totalTracks) * 100
    e._width = (100 / totalTracks) - gap
  })
  return sorted
}

const getTimelineEvents = (dayIndex) => {
  const wd = dayIndex + 1
  const baseMinutes = START_HOUR * 60
  const raw = defaultCourses
    .filter((c) => {
      if (c.weekday !== wd) return false
      if (!showOdd.value && c.weekType === '单周') return false
      if (showOdd.value && c.weekType === '双周') return false
      return true
    })
    .map((c) => {
      const startMin = parseTime(c.startTime) || (c.startPeriod ? (START_HOUR * 60 + (c.startPeriod - 1) * 45) : 0)
      const endMin = parseTime(c.endTime) || (c.endPeriod ? (START_HOUR * 60 + c.endPeriod * 45) : startMin + 45)
      return {
        ...c,
        _startMin: startMin,
        _endMin: endMin,
        _top: Math.max(0, (startMin - baseMinutes) / 60 * PX_PER_HOUR),
        _height: Math.max(10, (endMin - startMin) / 60 * PX_PER_HOUR)
      }
    })
  return layoutEvents(raw)
}

const defaultCourses = [
  { id: 'c1',  title: '机器学习',     teacher: '李明远', location: '紫金港东1A-203',   weekday: 1, startPeriod: 1, endPeriod: 2, type: 'course', weekType: '每周', startTime: '08:00', endTime: '09:35' },
  { id: 'c2',  title: '机器学习',     teacher: '李明远', location: '紫金港东1A-203',   weekday: 4, startPeriod: 3, endPeriod: 4, type: 'course', weekType: '每周', startTime: '10:00', endTime: '11:35' },
  { id: 'c3',  title: '高等数学',     teacher: '张晓峰', location: '紫金港西2-315',    weekday: 2, startPeriod: 1, endPeriod: 3, type: 'course', weekType: '每周', startTime: '08:00', endTime: '10:45' },
  { id: 'c4',  title: '数据库系统',   teacher: '王海燕', location: '玉泉教3-208',     weekday: 1, startPeriod: 6, endPeriod: 7, type: 'course', weekType: '单周', startTime: '13:25', endTime: '15:00' },
  { id: 'c5',  title: '数据库系统',   teacher: '王海燕', location: '玉泉教3-208',     weekday: 5, startPeriod: 1, endPeriod: 2, type: 'course', weekType: '单周', startTime: '08:00', endTime: '09:35' },
  { id: 'c6',  title: '数据结构',     teacher: '陈志强', location: '紫金港东1B-501',   weekday: 2, startPeriod: 6, endPeriod: 8, type: 'course', weekType: '每周', startTime: '13:25', endTime: '15:50' },
  { id: 'c7',  title: '计算机网络',   teacher: '赵丽娜', location: '玉泉曹光彪东-102', weekday: 4, startPeriod: 6, endPeriod: 7, type: 'course', weekType: '每周', startTime: '13:25', endTime: '15:00' },
  { id: 'c8',  title: '英语写作',     teacher: '刘文博', location: '紫金港外语楼-310', weekday: 5, startPeriod: 3, endPeriod: 4, type: 'course', weekType: '每周', startTime: '10:00', endTime: '11:35' },
  { id: 'c9',  title: '操作系统',     teacher: '孙浩然', location: '玉泉教4-106',     weekday: 3, startPeriod: 3, endPeriod: 5, type: 'course', weekType: '双周', startTime: '10:00', endTime: '12:25' },
  { id: 'c10', title: '学术前沿讲座', teacher: '轮值',   location: '紫金港学术报告厅', weekday: 3, startPeriod: 9, endPeriod: 10, type: 'recommended', weekType: '单周', startTime: '16:15', endTime: '17:50' },
  // 示例：一场不按标准节次起止的活动（14:00 开始，跨第6-9节）
  { id: 'e1',  title: '生成式AI与科研写作', teacher: '特邀嘉宾', location: '紫金港学术报告厅', weekday: 5, startPeriod: 6, endPeriod: 9, type: 'activity', weekType: '每周', startTime: '14:00', endTime: '16:00' },
]

const getMonday = (offset = 0) => {
  const d = new Date()
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(d.setDate(diff))
  monday.setDate(monday.getDate() + offset * 7)
  monday.setHours(0, 0, 0, 0)
  return monday
}

const weekDays = computed(() => {
  const monday = getMonday(weekOffset.value)
  const today = new Date()
  const labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return {
      label: labels[i],
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      isToday: d.toDateString() === today.toDateString(),
      fullDate: d
    }
  })
})

const weekRangeText = computed(() => {
  const monday = getMonday(weekOffset.value)
  const sunday = new Date(monday)
  sunday.setDate(sunday.getDate() + 6)
  const fmt = (d) => `${d.getMonth() + 1}/${d.getDate()}`
  return `${fmt(monday)} - ${fmt(sunday)}`
})

const weekNumber = computed(() => {
  const monday = getMonday(weekOffset.value)
  const startOfYear = new Date(monday.getFullYear(), 0, 1)
  const days = Math.floor((monday - startOfYear) / (24 * 60 * 60 * 1000))
  return Math.ceil((days + startOfYear.getDay() + 1) / 7)
})

const weekParity = computed(() => weekNumber.value % 2 === 1 ? '单周' : '双周')

const prevWeek = () => { weekOffset.value--; fetchSchedules() }
const nextWeek = () => { weekOffset.value++; fetchSchedules() }

const formatDate = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const typeLabel = (event) => {
  const map = { course: '课程', activity: '活动', recommended: '推荐', conflict: '冲突', exam: '考试' }
  return map[event.color_type || event.type] || '活动'
}

const weekCourses = computed(() => {
  return defaultCourses.filter((c) => {
    if (!showOdd.value && c.weekType === '单周') return false
    if (showOdd.value && c.weekType === '双周') return false
    return true
  }).map((c) => ({
    ...c,
    dayLabel: ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'][c.weekday],
    timeLabel: `${c.startPeriod}-${c.endPeriod}节`
  }))
})

const upcoming = computed(() => {
  return allEvents.value
    .filter((e) => new Date(e.start_time || e.time) >= new Date())
    .sort((a, b) => new Date(a.start_time || a.time) - new Date(b.start_time || b.time))
    .slice(0, 5)
})

const conflictEvents = computed(() => {
  return allEvents.value.filter((e) => (e.color_type || e.type) === 'conflict')
})

const exams = computed(() => {
  const seen = new Set()
  return defaultCourses
    .filter((c) => c.examDate && !seen.has(c.title + c.examDate) && seen.add(c.title + c.examDate))
    .map((c) => ({ title: c.title, examDate: c.examDate, location: c.location }))
})

const fetchSchedules = async () => {
  loading.value = true
  error.value = ''
  try {
    const pad = (n) => String(n).padStart(2, '0')
    const monday = getMonday(weekOffset.value)
    const sunday = new Date(monday)
    sunday.setDate(sunday.getDate() + 6)
    const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    const res = await getSchedules({ start_date: fmt(monday), end_date: fmt(sunday) })
    allEvents.value = res.data?.events || res.data?.items || res.data || []
  } catch {
    // 后端不可用时使用内置课表数据，静默处理
  } finally {
    loading.value = false
  }
}

const exportIcs = async () => {
  exporting.value = true
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const token = localStorage.getItem('token')
    const monday = getMonday(weekOffset.value)
    const sunday = new Date(monday)
    sunday.setDate(sunday.getDate() + 6)
    const pad = (n) => String(n).padStart(2, '0')
    const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    const response = await fetch(`${baseUrl}/schedules/export-ics?start_date=${fmt(monday)}&end_date=${fmt(sunday)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error('导出失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schedule_${fmt(monday)}_${fmt(sunday)}.ics`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('ICS 导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchSchedules)
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
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.legend {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #5c4f3d;
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.course { background: #3b82f6; }
.dot.activity { background: #0f766e; }
.dot.recommended { background: #e27a38; }
.dot.conflict { background: #ef4444; }
.dot.exam { background: #8b5cf6; }

.main-grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

/* ── 时间轴课表 ── */
.timetable-card {
  padding: 0;
  overflow: hidden;
}

.timeline-wrap {
  position: relative;
}

.timeline-header {
  display: flex;
  border-bottom: 1px solid var(--line);
  background: #faf7f0;
}

.ruler-spacer {
  width: 56px;
  flex-shrink: 0;
}

.day-head {
  flex: 1;
  padding: 10px 4px;
  text-align: center;
}

.day-head strong {
  display: block;
  font-size: 13px;
  color: var(--ink);
}

.day-head small {
  font-size: 11px;
  color: var(--muted);
}

.day-head.today {
  background: rgba(15, 118, 110, 0.08);
}

.day-head.today strong {
  color: var(--brand);
}

.timeline-body {
  display: flex;
  position: relative;
  height: v-bind(timelineHeight + 'px');
}

/* 时间标尺 */
.time-ruler {
  width: 56px;
  flex-shrink: 0;
  position: relative;
  border-right: 1px solid var(--line);
  background: #fdfcf8;
}

.ruler-tick {
  position: absolute;
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #bbb6a8;
  transform: translateY(-50%);
}

/* 天列 */
.day-col {
  flex: 1;
  position: relative;
  border-right: 1px solid #f0eade;
}

.day-col:last-child {
  border-right: none;
}

.day-bg {
  position: absolute;
  inset: 0;
}

.bg-line {
  position: absolute;
  width: 100%;
  border-top: 1px solid #f0eade;
}

/* 时间轴事件块 */
.timeline-event {
  position: absolute;
  background: #dbeafe;
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
  padding: 3px 5px;
  font-size: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 16px;
}

.timeline-event.activity {
  background: #d1f2eb;
  border-left-color: #0f766e;
}

.timeline-event.recommended {
  background: #fef3e4;
  border-left-color: #e27a38;
}

.timeline-event.conflict {
  background: #ffeeee;
  border-left-color: #ef4444;
}

.timeline-event.exam {
  background: #ede9fe;
  border-left-color: #8b5cf6;
}

.event-name {
  font-weight: 600;
  color: #1e3a5f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.event-time {
  color: #64748b;
  font-size: 9px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-meta {
  color: #94a3b8;
  font-size: 9px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.week-tag {
  position: absolute;
  top: 2px;
  right: 3px;
  font-size: 8px;
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  padding: 0px 3px;
  border-radius: 2px;
}

.course-name {
  font-weight: 600;
  color: #1e3a5f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-meta {
  color: #64748b;
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.week-tag {
  position: absolute;
  top: 3px;
  right: 4px;
  font-size: 9px;
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  padding: 1px 4px;
  border-radius: 3px;
}

.exam-tag {
  display: block;
  font-size: 9px;
  color: #8b5cf6;
  margin-top: auto;
}

/* ── 侧边栏 ── */
.side-panel {
  display: grid;
  gap: 12px;
  position: sticky;
  top: 108px;
}

.course-list {
  display: grid;
  gap: 8px;
}

.course-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #faf7f0;
  border: 1px solid #f0eade;
}

.course-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-item-left strong {
  font-size: 13px;
}

.course-item-left p {
  margin: 0;
  font-size: 11px;
}

.course-item-right {
  text-align: right;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.schedule-list {
  display: grid;
  gap: 10px;
}

.schedule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.schedule-item strong {
  font-size: 13px;
}

.schedule-item p {
  margin: 2px 0 0;
  font-size: 11px;
}

.empty-hint {
  text-align: center;
  padding: 12px 0;
}

.conflict-panel {
  background: #fff4f1;
  border: 1px solid #f0d1c8;
  border-radius: 12px;
  padding: 12px;
}

.conflict-panel.safe {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.conflict-panel.safe p {
  color: #166534;
}

.conflict-list {
  display: grid;
  gap: 10px;
}

.conflict-item {
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8efe2;
  border: 1px solid #e2d3c0;
}

.exam-list {
  display: grid;
  gap: 8px;
}

.exam-item {
  padding: 8px 10px;
  border-radius: 10px;
  background: #faf5ff;
  border: 1px solid #e9d5ff;
}

.exam-item strong {
  font-size: 13px;
  color: #6b21a8;
}

.exam-item p {
  margin: 2px 0 0;
  font-size: 11px;
}

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 160px;
  gap: 8px;
  color: #6b7280;
}

@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  .side-panel {
    position: static;
  }
  .timetable-card {
    overflow-x: auto;
  }
  .timeline-wrap {
    min-width: 720px;
  }
}
</style>
