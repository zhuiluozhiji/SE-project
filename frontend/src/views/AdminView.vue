<template>
  <section class="admin-page fade-in">
    <div class="page-panel admin-top">
      <div>
        <h2 class="page-title">后台管理</h2>
        <p class="muted">活动维护、标签修正与爬虫任务统一管理。</p>
      </div>
      <div class="admin-actions">
        <el-button type="primary" @click="openActivityDialog()">新增活动</el-button>
        <el-button @click="openOcrDialog">识别截图</el-button>
        <el-button :loading="crawlerRunning" @click="runCrawler">触发爬虫</el-button>
        <el-button @click="showCrawlerLogs = true; fetchCrawlerRecords()">查看日志</el-button>
      </div>
    </div>

    <div class="card admin-table" v-loading="loading">
      <div class="table-top">
        <h3 class="section-title">活动管理</h3>
        <el-input v-model="searchTitle" placeholder="搜索活动标题..." class="table-search" clearable />
      </div>
      <el-table :data="displayedRows" style="width: 100%" stripe>
        <el-table-column prop="title" label="活动标题" min-width="200" />
        <el-table-column prop="campus" label="校区" width="100" />
        <el-table-column label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <StatusTag :label="statusLabel(row.status)" :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="openActivityDialog(row)">编辑</el-button>
            <el-popconfirm title="确认下架该活动？" @confirm="handleOffline(row.id)">
              <template #reference>
                <el-button size="small" type="danger" plain>下架</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>

  <!-- 新增/编辑弹窗 -->
  <el-dialog v-model="activityDialogVisible" :title="editingActivity ? '编辑活动' : '新增活动'" width="600px" append-to-body align-center>
    <el-form :model="activityForm" label-width="100px">
      <el-form-item label="活动标题">
        <el-input v-model="activityForm.title" placeholder="请输入活动标题" />
      </el-form-item>
      <el-form-item label="主讲人">
        <el-input v-model="activityForm.speaker" placeholder="主讲人" />
      </el-form-item>
      <el-form-item label="组织单位">
        <el-input v-model="activityForm.organizer" placeholder="承办单位" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="校区">
            <el-select v-model="activityForm.campus" placeholder="选择校区">
              <el-option label="紫金港" value="紫金港" />
              <el-option label="玉泉" value="玉泉" />
              <el-option label="西溪" value="西溪" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="类别">
            <el-select v-model="activityForm.category" placeholder="选择类别">
              <el-option label="学术讲座" value="学术讲座" />
              <el-option label="研讨会" value="研讨会" />
              <el-option label="工作坊" value="工作坊" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="地点">
        <el-input v-model="activityForm.location" placeholder="具体地点" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="开始时间">
            <el-date-picker
              v-model="activityStartTime"
              type="datetime"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DDTHH:mm:ss"
              placeholder="选择开始时间"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计时长">
            <div class="duration-input">
              <el-input-number
                v-model="activityEstimatedDurationMinutes"
                :min="1"
                :step="15"
                controls-position="right"
              />
              <span>min</span>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="结束时间">
        <el-date-picker
          v-model="activityEndTime"
          type="datetime"
          format="YYYY-MM-DD HH:mm"
          value-format="YYYY-MM-DDTHH:mm:ss"
          placeholder="选择结束时间"
        />
      </el-form-item>
      <el-form-item label="活动简介">
        <el-input
          v-model="activityForm.description"
          type="textarea"
          :autosize="{ minRows: 4, maxRows: 10 }"
          placeholder="活动描述"
        />
      </el-form-item>
      <el-form-item label="原文链接" v-if="editingSourceUrl">
        <el-link
          type="primary"
          :href="editingSourceUrl"
          target="_blank"
          :underline="false"
        >
          {{ editingSourceUrl }}
          <el-icon style="margin-left:2px;vertical-align:middle"><Link /></el-icon>
        </el-link>
        <p class="faint" style="margin-top:2px">爬虫来源原文，点击可跳转核对</p>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="activityDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="savingActivity" @click="submitActivity">
        {{ editingActivity ? '保存修改' : '创建活动' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- 活动截图识别弹窗 -->
  <el-dialog v-model="ocrDialogVisible" title="识别活动截图" width="560px" append-to-body align-center>
    <div class="ocr-dialog-body">
      <el-upload
        ref="ocrUploadRef"
        drag
        action="#"
        :auto-upload="false"
        multiple
        :limit="MAX_SCREENSHOT_FILES"
        accept=".png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
        :on-change="handleOcrFileChange"
        :on-remove="handleOcrFileRemove"
        :on-exceed="handleOcrFileExceed"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <p>拖拽活动截图到这里</p>
        <small class="faint">支持 PNG / JPG / WEBP / BMP / TIFF</small>
      </el-upload>

      <div class="ocr-capture-actions">
        <el-button size="small" @click="captureOcrScreenshot" :disabled="ocrFiles.length >= MAX_SCREENSHOT_FILES">
          快捷截屏
        </el-button>
        <span class="faint">{{ ocrFiles.length }}/{{ MAX_SCREENSHOT_FILES }} · {{ SCREENSHOT_SHORTCUT_LABEL }}</span>
      </div>

      <div v-if="recognizedText" class="ocr-preview">
        <strong>识别文本</strong>
        <p>{{ recognizedText }}</p>
      </div>
    </div>
    <template #footer>
      <el-button @click="ocrDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="recognizing" :disabled="!ocrFileReady" @click="submitOcrFile">
        识别并填入
      </el-button>
    </template>
  </el-dialog>

  <!-- 爬虫触发弹窗：选择学院 + 选择月份 -->
  <el-dialog v-model="crawlerMonthDialogVisible" title="触发爬虫" width="500px" append-to-body align-center>
    <div class="crawler-dialog-body">
      <!-- 学院选择 -->
      <div class="crawler-section">
        <p class="crawler-label">选择学院来源</p>
        <p class="muted" style="margin-bottom:12px">
          可多选，将<strong>依次</strong>爬取所选学院的活动。
        </p>
        <div v-if="crawlerSourcesLoading" class="faint" style="padding:20px 0">加载学院列表…</div>
        <div v-else class="crawler-source-cards">
          <div
            v-for="src in crawlerSourceOptions"
            :key="src.value"
            class="source-card"
            :class="{ 'source-card--active': crawlerSelectedSources.includes(src.value) }"
            @click="toggleSource(src.value)"
          >
            <div class="source-card-badge">
              {{ getSourceBadge(src.value) }}
            </div>
            <div class="source-card-body">
              <span class="source-card-name">{{ src.label }}</span>
            </div>
            <div class="source-card-check" v-if="crawlerSelectedSources.includes(src.value)">
              <el-icon><Check /></el-icon>
            </div>
          </div>
        </div>
        <p v-if="crawlerSelectedSources.length === 0" class="faint" style="margin-top:8px">
          请至少选择一个学院来源
        </p>
        <p v-else class="faint" style="margin-top:8px">
          已选择 <strong>{{ crawlerSelectedSources.length }}</strong> 个学院
          <el-button size="small" text type="primary" @click="crawlerSelectedSources = crawlerSourceOptions.map(s => s.value)">全选</el-button>
          <el-button size="small" text type="primary" @click="crawlerSelectedSources = []">清空</el-button>
        </p>
      </div>

      <!-- 分隔线 -->
      <el-divider />

      <!-- 月份选择 -->
      <div class="crawler-section">
        <p class="crawler-label">时间范围</p>
        <p class="muted" style="margin-bottom:10px">
          仅爬取<strong>选定月份及之后</strong>发布的活动。<br>
          不选择则使用系统默认年份（2026年起）。
        </p>
        <el-date-picker
          v-model="crawlerSinceMonth"
          type="month"
          placeholder="选择起始月份"
          format="YYYY-MM"
          value-format="YYYY-MM"
          :disabled="crawlerNoMonthLimit"
          style="width:100%"
        />
        <el-checkbox v-model="crawlerNoMonthLimit" class="crawler-month-checkbox">
          不限制月份（爬取全部可用活动）
        </el-checkbox>
      </div>
    </div>
    <template #footer>
      <el-button @click="crawlerMonthDialogVisible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="crawlerRunning"
        :disabled="crawlerSelectedSources.length === 0"
        @click="confirmRunCrawler"
      >
        开始爬取（{{ crawlerSelectedSources.length }} 个学院）
      </el-button>
    </template>
  </el-dialog>

  <!-- 爬虫日志弹窗 -->
  <el-dialog v-model="showCrawlerLogs" title="爬虫运行记录" width="700px" append-to-body align-center>
    <el-table :data="crawlerRecords" v-loading="crawlerLogsLoading">
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="fetched_count" label="抓取数" width="80" />
      <el-table-column prop="success_count" label="成功数" width="80" />
      <el-table-column prop="run_time" label="运行时间" width="180" />
      <el-table-column prop="error_msg" label="错误信息" min-width="150" />
    </el-table>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Link, Check } from '@element-plus/icons-vue'
import { getActivities } from '../api/activities'
import {
  createActivity,
  updateActivity,
  offlineActivity,
  recognizeActivityImage,
  runCrawler as runCrawlerApi,
  getCrawlerRecords,
  getCrawlerSources
} from '../api/admin'
import StatusTag from '../components/StatusTag.vue'
import {
  captureScreenImage,
  isAllowedScreenshotFile,
  isScreenshotShortcut,
  MAX_SCREENSHOT_FILES,
  SCREENSHOT_SHORTCUT_LABEL
} from '../utils/screenCapture'

const loading = ref(false)
const activities = ref([])
const searchTitle = ref('')
const savingActivity = ref(false)
const crawlerRunning = ref(false)
const crawlerMonthDialogVisible = ref(false)
const crawlerSinceMonth = ref('')
const crawlerNoMonthLimit = ref(false)
const crawlerSelectedSources = ref([])
const crawlerSourceOptions = ref([])
const crawlerSourcesLoading = ref(false)
const showCrawlerLogs = ref(false)
const crawlerLogsLoading = ref(false)
const crawlerRecords = ref([])

const activityDialogVisible = ref(false)
const editingActivity = ref(null)
const ocrDialogVisible = ref(false)
const ocrUploadRef = ref(null)
const ocrFiles = ref([])
const ocrFileReady = ref(false)
const recognizing = ref(false)
const recognizedText = ref('')
const DEFAULT_ESTIMATED_DURATION_MINUTES = 120

const defaultForm = () => ({
  title: '',
  speaker: '',
  organizer: '',
  campus: '',
  category: '',
  location: '',
  start_time: null,
  end_time: null,
  estimated_duration_minutes: DEFAULT_ESTIMATED_DURATION_MINUTES,
  description: ''
})

const activityForm = reactive(defaultForm())

const statusMap = {
  open: '可加入', full: '已满', closed: '已结束', offline: '已下架', draft: '草稿'
}
const statusLabel = (s) => statusMap[s] || s

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const toLocalIso = (value) => {
  if (!value) return null
  if (typeof value === 'string') {
    const normalized = value.trim().replace(' ', 'T')
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(normalized)) {
      return normalized.length === 16 ? `${normalized}:00` : normalized.slice(0, 19)
    }
  }
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00`
}

const normalizeDurationMinutes = (value) => {
  const minutes = Number(value)
  return Number.isFinite(minutes) && minutes > 0 ? minutes : DEFAULT_ESTIMATED_DURATION_MINUTES
}

const addMinutesToLocalIso = (value, minutes) => {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  date.setMinutes(date.getMinutes() + normalizeDurationMinutes(minutes))
  return toLocalIso(date)
}

const shouldReplaceEstimatedEnd = (start, end) => {
  if (!start) return false
  if (!end) return true
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) return true
  return endDate <= startDate
}

const getPositiveDurationFromRange = (start, end) => {
  if (!start || !end) return null
  const startDate = new Date(start)
  const endDate = new Date(end)
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return null
  }
  const minutes = Math.round((endDate - startDate) / 60000)
  return minutes > 0 ? minutes : null
}

const getDurationFromRange = (start, end) => {
  return getPositiveDurationFromRange(start, end) || DEFAULT_ESTIMATED_DURATION_MINUTES
}

const syncEstimatedDurationFromRange = (start = activityForm.start_time, end = activityForm.end_time) => {
  const minutes = getPositiveDurationFromRange(start, end)
  if (!minutes) return false
  activityForm.estimated_duration_minutes = minutes
  return true
}

const fillActivityEstimatedEndTime = (force = false) => {
  if (!activityForm.start_time) return
  if (!force && !shouldReplaceEstimatedEnd(activityForm.start_time, activityForm.end_time)) return
  const endTime = addMinutesToLocalIso(
    activityForm.start_time,
    activityForm.estimated_duration_minutes
  )
  if (endTime) activityForm.end_time = endTime
}

const activityStartTime = computed({
  get: () => activityForm.start_time,
  set: (value) => {
    activityForm.start_time = value
    if (syncEstimatedDurationFromRange(value, activityForm.end_time)) return
    fillActivityEstimatedEndTime(true)
  }
})

const activityEndTime = computed({
  get: () => activityForm.end_time,
  set: (value) => {
    activityForm.end_time = value
    syncEstimatedDurationFromRange(activityForm.start_time, value)
  }
})

const activityEstimatedDurationMinutes = computed({
  get: () => activityForm.estimated_duration_minutes,
  set: (value) => {
    activityForm.estimated_duration_minutes = normalizeDurationMinutes(value)
    fillActivityEstimatedEndTime(true)
  }
})

const PINNED_ADMIN_ACTIVITY_TITLES = [
  'Uniqueness of asymptotically conical K\\\\"ahler-Ricci flow',
  'Quantitative maximal diameter rigidity of positive Ricci curvature',
  'Advanced Seminar on Partial Differential Equations',
]

const getAdminPinnedPriority = (activity) => {
  const index = PINNED_ADMIN_ACTIVITY_TITLES.indexOf(activity?.title || '')
  return index >= 0 ? index : PINNED_ADMIN_ACTIVITY_TITLES.length
}

const sortPinnedAdminRows = (rows) => {
  return [...rows].sort((a, b) => {
    const priorityDiff = getAdminPinnedPriority(a) - getAdminPinnedPriority(b)
    return priorityDiff || 0
  })
}

const displayedRows = computed(() => {
  if (!searchTitle.value) return sortPinnedAdminRows(activities.value)
  const kw = searchTitle.value.toLowerCase()
  return sortPinnedAdminRows(
    activities.value.filter((a) => (a.title || '').toLowerCase().includes(kw))
  )
})

const editingSourceUrl = computed(() => {
  return editingActivity.value?.source_url || ''
})

const fetchActivities = async () => {
  loading.value = true
  try {
    const res = await getActivities({ page: 1, page_size: 100 })
    activities.value = res.data?.items || res.data?.activities || res.data || []
  } catch { /* 拦截器已处理 */ } finally {
    loading.value = false
  }
}

const openActivityDialog = (row = null) => {
  editingActivity.value = row
  if (row) {
    Object.assign(activityForm, {
      title: row.title || '',
      speaker: row.speaker || '',
      organizer: row.organizer || '',
      campus: row.campus || '',
      category: row.category || '',
      location: row.location || '',
      start_time: toLocalIso(row.start_time),
      end_time: toLocalIso(row.end_time),
      estimated_duration_minutes: getDurationFromRange(row.start_time, row.end_time),
      description: row.description || ''
    })
  } else {
    Object.assign(activityForm, defaultForm())
  }
  activityDialogVisible.value = true
}

const resetOcrState = () => {
  ocrFiles.value = []
  ocrFileReady.value = false
  recognizedText.value = ''
  ocrUploadRef.value?.clearFiles()
}

const openOcrDialog = () => {
  resetOcrState()
  ocrDialogVisible.value = true
}

const syncOcrFiles = (uploadFiles = []) => {
  const rawFiles = uploadFiles
    .map((item) => item.raw || item)
    .filter(Boolean)

  if (rawFiles.some((file) => !isAllowedScreenshotFile(file))) {
    ocrFiles.value = []
    ocrFileReady.value = false
    ocrUploadRef.value?.clearFiles()
    ElMessage.warning('请上传 PNG、JPG、WEBP、BMP 或 TIFF 格式的图片。')
    return
  }

  ocrFiles.value = rawFiles.slice(0, MAX_SCREENSHOT_FILES)
  ocrFileReady.value = ocrFiles.value.length > 0
}

const handleOcrFileChange = (_file, uploadFiles = []) => {
  recognizedText.value = ''
  syncOcrFiles(uploadFiles)
}

const handleOcrFileRemove = (_file, uploadFiles = []) => {
  recognizedText.value = ''
  syncOcrFiles(uploadFiles)
}

const handleOcrFileExceed = (files) => {
  const nextFiles = [...ocrFiles.value, ...(files || [])].slice(0, MAX_SCREENSHOT_FILES)
  ocrUploadRef.value?.clearFiles()
  nextFiles.forEach((file) => ocrUploadRef.value?.handleStart(file))
  syncOcrFiles(nextFiles)
  ElMessage.warning(`一个活动最多支持 ${MAX_SCREENSHOT_FILES} 张截图。`)
}

const captureOcrScreenshot = async () => {
  if (!ocrDialogVisible.value) openOcrDialog()
  if (ocrFiles.value.length >= MAX_SCREENSHOT_FILES) {
    ElMessage.warning(`一个活动最多支持 ${MAX_SCREENSHOT_FILES} 张截图。`)
    return
  }
  try {
    const file = await captureScreenImage('activity-admin')
    ocrUploadRef.value?.handleStart(file)
    syncOcrFiles([...ocrFiles.value, file])
  } catch (err) {
    ElMessage.warning(err?.message || '截屏已取消')
  }
}

const handleOcrShortcut = (event) => {
  if (!isScreenshotShortcut(event)) return
  event.preventDefault()
  captureOcrScreenshot()
}

const submitOcrFile = async () => {
  if (!ocrFiles.value.length) {
    ElMessage.warning('请先选择活动截图。')
    return
  }
  recognizing.value = true
  recognizedText.value = ''
  try {
    const formData = new FormData()
    ocrFiles.value.forEach((file) => formData.append('files', file))
    const res = await recognizeActivityImage(formData)
    const data = res.data || {}
    const recognized = data.activity || {}
    recognizedText.value = data.raw_text || ''
    editingActivity.value = null
    Object.assign(activityForm, {
      ...defaultForm(),
      title: recognized.title || '',
      speaker: recognized.speaker || '',
      organizer: recognized.organizer || '',
      campus: recognized.campus || '',
      category: recognized.category || '',
      location: recognized.location || '',
      start_time: recognized.start_time || null,
      end_time: recognized.end_time || null,
      description: recognized.description || ''
    })
    if (!syncEstimatedDurationFromRange()) {
      fillActivityEstimatedEndTime(false)
    }
    ocrDialogVisible.value = false
    activityDialogVisible.value = true

    const warnings = data.warnings || []
    if (warnings.length) {
      ElMessage.warning(`已填入表单，仍需补充：${warnings.join('、')}`)
    } else {
      ElMessage.success('已识别并填入活动表单')
    }
  } catch { /* 拦截器已处理 */ } finally {
    recognizing.value = false
  }
}

const submitActivity = async () => {
  savingActivity.value = true
  try {
    const { estimated_duration_minutes, ...data } = activityForm
    if (data.start_time) data.start_time = toLocalIso(data.start_time)
    if (data.end_time) data.end_time = toLocalIso(data.end_time)

    if (editingActivity.value) {
      await updateActivity(editingActivity.value.id, data)
      ElMessage.success('活动已更新')
    } else {
      await createActivity(data)
      ElMessage.success('活动已创建')
    }
    activityDialogVisible.value = false
    fetchActivities()
  } catch { /* 拦截器已处理 */ } finally {
    savingActivity.value = false
  }
}

const handleOffline = async (id) => {
  try {
    await offlineActivity(id)
    ElMessage.success('活动已下架')
    fetchActivities()
  } catch { /* 拦截器已处理 */ }
}

const runCrawler = async () => {
  // 打开爬虫弹窗：先获取可用学院列表，再让用户选择
  crawlerSinceMonth.value = ''
  crawlerNoMonthLimit.value = false
  crawlerSelectedSources.value = []
  crawlerSourcesLoading.value = true
  crawlerMonthDialogVisible.value = true

  try {
    const res = await getCrawlerSources()
    const sources = res.data?.sources || []
    crawlerSourceOptions.value = sources.map((s) => ({
      value: s,
      label: SOURCE_LABEL_MAP[s] || s,
    }))
  } catch {
    // 如果获取失败，回退到硬编码列表
    crawlerSourceOptions.value = Object.entries(SOURCE_LABEL_MAP).map(([value, label]) => ({
      value,
      label,
    }))
  } finally {
    crawlerSourcesLoading.value = false
  }
}

// 学院 source → 可读名称映射（前后端都需要保持一致）
const SOURCE_LABEL_MAP = {
  cs_zju: '计算机科学与技术学院',
  cse_zju: '控制科学与工程学院',
  math_zju: '数学科学学院',
  geo_zju: '地球科学学院',
}

// 学院 source → 卡片缩写/徽章文字
const SOURCE_BADGE_MAP = {
  cs_zju: 'CS',
  cse_zju: 'CSE',
  math_zju: 'MATH',
  geo_zju: 'GEO',
}

const getSourceBadge = (value) => {
  return SOURCE_BADGE_MAP[value] || value.slice(0, 4).toUpperCase()
}

const toggleSource = (value) => {
  const idx = crawlerSelectedSources.value.indexOf(value)
  if (idx >= 0) {
    crawlerSelectedSources.value.splice(idx, 1)
  } else {
    crawlerSelectedSources.value.push(value)
  }
}

const confirmRunCrawler = async () => {
  if (crawlerSelectedSources.value.length === 0) {
    ElMessage.warning('请至少选择一个学院来源')
    return
  }

  crawlerRunning.value = true
  crawlerMonthDialogVisible.value = false

  const sources = crawlerSelectedSources.value
  const sincePayload = (!crawlerNoMonthLimit.value && crawlerSinceMonth.value)
    ? crawlerSinceMonth.value
    : undefined

  let totalFetched = 0
  let totalCreated = 0
  let totalSkipped = 0
  let totalFiltered = 0
  let totalYearFiltered = 0
  const errors = []

  for (let i = 0; i < sources.length; i++) {
    const source = sources[i]
    const label = SOURCE_LABEL_MAP[source] || source
    try {
      ElMessage.info(`[${i + 1}/${sources.length}] 正在爬取 ${label}…`)
      const payload = { source }
      if (crawlerNoMonthLimit.value) {
        payload.no_limit = true
      } else if (sincePayload) {
        payload.since = sincePayload
      }
      const res = await runCrawlerApi(payload)
      const data = res.data || res || {}
      totalFetched += data.fetched || 0
      totalCreated += data.created || 0
      totalSkipped += data.skipped || 0
      totalFiltered += data.filtered || 0
      totalYearFiltered += data.year_filtered || 0

      const sinceInfo = crawlerNoMonthLimit.value
        ? '（不限制月份）'
        : (data.since_applied ? `（自 ${data.since_applied} 起）` : '')
      ElMessage.success(
        `[${label}] 爬取完成${sinceInfo}：抓取 ${data.fetched || 0} 条，`
        + `新增 ${data.created || 0} 条，去重跳过 ${data.skipped || 0} 条`
      )
    } catch (err) {
      const msg = err?.response?.data?.message || err?.message || '未知错误'
      errors.push(`${label}: ${msg}`)
      ElMessage.error(`[${label}] 爬取失败: ${msg}`)
    }
  }

  // 汇总
  const sinceInfo = crawlerNoMonthLimit.value
    ? '（不限制月份）'
    : (sincePayload ? `（自 ${sincePayload} 起）` : '')
  if (errors.length === 0) {
    ElMessage.success(
      `全部爬取完成${sinceInfo}：共 ${sources.length} 个学院，`
      + `抓取 ${totalFetched} 条，新增 ${totalCreated} 条，`
      + `去重跳过 ${totalSkipped} 条，内容过滤 ${totalFiltered} 条，`
      + `月份过滤 ${totalYearFiltered} 条`
    )
  } else if (errors.length < sources.length) {
    ElMessage.warning(
      `部分完成${sinceInfo}：${sources.length - errors.length}/${sources.length} 个学院成功，`
      + `新增 ${totalCreated} 条。失败: ${errors.join('；')}`
    )
  }

  fetchActivities()
  crawlerRunning.value = false
}

const fetchCrawlerRecords = async () => {
  crawlerLogsLoading.value = true
  try {
    const res = await getCrawlerRecords()
    crawlerRecords.value = res.data?.items || res.data || []
  } catch { /* 拦截器已处理 */ } finally {
    crawlerLogsLoading.value = false
  }
}

onMounted(() => {
  fetchActivities()
  window.addEventListener('keydown', handleOcrShortcut)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleOcrShortcut)
})
</script>

<style scoped>
.admin-page {
  display: grid;
  gap: 20px;
}

.admin-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.admin-actions {
  display: flex;
  gap: 10px;
}

.ocr-dialog-body {
  display: grid;
  gap: 14px;
}

.upload-icon {
  font-size: 36px;
  color: var(--accent);
}

.ocr-capture-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ocr-preview {
  max-height: 180px;
  overflow: auto;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-muted);
  border: 1px solid var(--border);
}

.ocr-preview p {
  margin: 8px 0 0;
  white-space: pre-wrap;
}

/* 爬虫触发弹窗 */
.crawler-dialog-body {
  display: grid;
  gap: 4px;
}

.crawler-section {
  display: grid;
  gap: 4px;
}

.crawler-label {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  margin: 0;
}

/* 学院卡片网格 */
.crawler-source-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.source-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid #dde1e7;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fff;
  position: relative;
  user-select: none;
}

.source-card:hover {
  border-color: #93bdf8;
  background: #f4f8ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(64, 128, 255, 0.1);
}

.source-card--active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 2px 12px rgba(64, 128, 255, 0.12);
}

.source-card--active:hover {
  border-color: #409eff;
  background: #d9ecff;
}

.source-card-badge {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #eef1f6;
  color: #475569;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.source-card--active .source-card-badge {
  background: #409eff;
  color: #fff;
}

.source-card-body {
  flex: 1;
  min-width: 0;
}

.source-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  display: block;
  word-break: keep-all;
}

.source-card-check {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--accent, #409eff);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 1px 4px rgba(64, 128, 255, 0.3);
}

/* 响应式：窄屏时单列 */
@media (max-width: 480px) {
  .crawler-source-cards {
    grid-template-columns: 1fr;
  }
}

.crawler-month-checkbox {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.duration-input {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.duration-input span {
  color: var(--text-secondary);
  font-size: 13px;
}

.admin-table {
  display: grid;
  gap: 12px;
}

.table-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-search {
  width: 240px;
}

@media (max-width: 960px) {
  .admin-top {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
