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

  <!-- 爬虫月份选择弹窗 -->
  <el-dialog v-model="crawlerMonthDialogVisible" title="选择爬取起始月份" width="440px" append-to-body align-center>
    <div class="crawler-month-body">
      <p class="muted" style="margin-bottom:16px">
        仅爬取<strong>选定月份及之后</strong>发布的活动。不选择则使用系统默认年份（2026年起）。
      </p>
      <div class="crawler-month-row">
        <el-date-picker
          v-model="crawlerSinceMonth"
          type="month"
          placeholder="选择起始月份"
          format="YYYY-MM"
          value-format="YYYY-MM"
          :disabled="crawlerNoMonthLimit"
          style="width:100%"
        />
      </div>
      <el-checkbox v-model="crawlerNoMonthLimit" class="crawler-month-checkbox">
        不限制月份（爬取全部可用活动）
      </el-checkbox>
    </div>
    <template #footer>
      <el-button @click="crawlerMonthDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="crawlerRunning" @click="confirmRunCrawler">
        开始爬取
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
import { UploadFilled } from '@element-plus/icons-vue'
import { getActivities } from '../api/activities'
import {
  createActivity,
  updateActivity,
  offlineActivity,
  recognizeActivityImage,
  runCrawler as runCrawlerApi,
  getCrawlerRecords
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
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) {
    return value.length === 16 ? `${value}:00` : value
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

const displayedRows = computed(() => {
  if (!searchTitle.value) return activities.value
  const kw = searchTitle.value.toLowerCase()
  return activities.value.filter((a) => (a.title || '').toLowerCase().includes(kw))
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
      start_time: row.start_time || null,
      end_time: row.end_time || null,
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
    if (data.start_time) data.start_time = new Date(data.start_time).toISOString()
    if (data.end_time) data.end_time = new Date(data.end_time).toISOString()

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

const runCrawler = () => {
  // 打开月份选择弹窗，而非直接触发爬虫
  crawlerSinceMonth.value = ''
  crawlerNoMonthLimit.value = false
  crawlerMonthDialogVisible.value = true
}

const confirmRunCrawler = async () => {
  crawlerRunning.value = true
  crawlerMonthDialogVisible.value = false
  try {
    const payload = { source: 'cs_zju' }
    if (!crawlerNoMonthLimit.value && crawlerSinceMonth.value) {
      payload.since = crawlerSinceMonth.value
    }
    const res = await runCrawlerApi(payload)
    const data = res.data || res || {}
    const sinceInfo = data.since_applied ? `（自 ${data.since_applied} 起）` : ''
    ElMessage.success(
      `爬取完成${sinceInfo}：抓取 ${data.fetched || 0} 条，新增 ${data.created || 0} 条，`
      + `去重跳过 ${data.skipped || 0} 条，内容过滤 ${data.filtered || 0} 条，`
      + `月份过滤 ${data.year_filtered || 0} 条`
    )
    fetchActivities()
  } catch { /* 拦截器已处理 */ } finally {
    crawlerRunning.value = false
  }
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

/* 爬虫月份选择弹窗 */
.crawler-month-body {
  display: grid;
  gap: 12px;
}

.crawler-month-row {
  display: flex;
  align-items: center;
}

.crawler-month-checkbox {
  margin-top: 4px;
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
