<template>
  <section class="import-page fade-in">
    <div class="page-panel">
      <h2 class="page-title">课表导入</h2>
      <p class="muted">导入个人课表后，系统将自动生成课程事件并参与冲突检测。</p>

      <div class="import-grid">
        <div class="card upload-card">
          <h3 class="section-title">文件导入</h3>
          <el-upload
            ref="uploadRef"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".csv,.xlsx,.xlsm"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <p>拖拽 CSV / Excel 文件到这里</p>
            <small class="faint">支持 .csv / .xlsx / .xlsm，教务导出的课表可直接上传</small>
          </el-upload>
          <div class="upload-actions">
            <el-button type="primary" :loading="uploading" @click="submitFile" :disabled="!fileReady">
              上传并导入
            </el-button>
          </div>

          <div v-if="importSummary" class="import-summary">
            <strong>导入完成</strong>
            <p class="faint">
              成功 {{ importSummary.imported_count }} 条，跳过 {{ importSummary.skipped_count }} 条。
            </p>
          </div>

          <div v-if="parseResult.length" class="parse-result">
            <h4>已导入课程</h4>
            <el-table :data="parseResult" size="small" max-height="300">
              <el-table-column prop="course_name" label="课程名" />
              <el-table-column prop="teacher" label="教师" width="100" />
              <el-table-column label="星期" width="60">
                <template #default="{ row }">周{{ row.weekday }}</template>
              </el-table-column>
              <el-table-column label="节次" width="80">
                <template #default="{ row }">{{ row.start_section }}-{{ row.end_section }}</template>
              </el-table-column>
              <el-table-column prop="location" label="教室" width="100" />
            </el-table>
          </div>

          <div v-if="importErrors.length" class="parse-warning">
            <strong>跳过说明</strong>
            <ul>
              <li v-for="item in importErrors" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div v-if="parseError" class="parse-error">
            <div>
              <strong>导入失败</strong>
              <p>{{ parseError }}</p>
            </div>
            <el-button size="small" @click="parseError = ''">关闭</el-button>
          </div>
        </div>

        <div class="card manual-card">
          <h3 class="section-title">手动录入</h3>
          <el-form :model="manualForm" label-position="top" size="small">
            <el-form-item label="课程名">
              <el-input v-model="manualForm.course_name" placeholder="如：高等数学" />
            </el-form-item>
            <el-form-item label="授课教师">
              <el-input v-model="manualForm.teacher" placeholder="教师姓名" />
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="星期">
                  <el-select v-model="manualForm.weekday" placeholder="选择">
                    <el-option v-for="i in 7" :key="i" :label="'周' + i" :value="i" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="教室">
                  <el-input v-model="manualForm.location" placeholder="如：教学楼A101" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="节次">
              <el-input-number v-model="manualForm.start_section" :min="1" :max="13" size="small" />
              <span class="range-sep">&ndash;</span>
              <el-input-number v-model="manualForm.end_section" :min="1" :max="13" size="small" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="small" :loading="manualSaving" @click="addManualCourse">
                添加课程
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { importCourses, createCourse } from '../api/courses'

const uploadRef = ref(null)
const selectedFile = ref(null)
const fileReady = ref(false)
const uploading = ref(false)
const manualSaving = ref(false)
const parseResult = ref([])
const parseError = ref('')
const importErrors = ref([])
const importSummary = ref(null)

const manualForm = reactive({
  course_name: '',
  teacher: '',
  weekday: 1,
  start_section: 1,
  end_section: 2,
  location: ''
})

const isAllowedFile = (file) => {
  const name = file?.name?.toLowerCase() || ''
  return name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xlsm')
}

const handleFileChange = (file) => {
  const rawFile = file?.raw
  parseResult.value = []
  parseError.value = ''
  importErrors.value = []
  importSummary.value = null
  if (!rawFile || !isAllowedFile(rawFile)) {
    selectedFile.value = null
    fileReady.value = false
    uploadRef.value?.clearFiles()
    parseError.value = '文件格式不支持。请上传 .csv、.xlsx 或 .xlsm 文件；旧版 .xls 请另存为 .xlsx 后再导入。'
    return
  }
  selectedFile.value = rawFile
  fileReady.value = true
}

const handleFileRemove = () => {
  selectedFile.value = null
  fileReady.value = false
  parseResult.value = []
  parseError.value = ''
  importErrors.value = []
  importSummary.value = null
}

const handleExceed = (files) => {
  const file = files?.[0]
  uploadRef.value?.clearFiles()
  if (file) {
    uploadRef.value?.handleStart(file)
    handleFileChange({ raw: file })
  }
}

const submitFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个 .csv、.xlsx 或 .xlsm 课表文件。')
    return
  }
  uploading.value = true
  parseError.value = ''
  importErrors.value = []
  importSummary.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await importCourses(formData)
    const data = res.data || {}
    parseResult.value = data.courses || []
    importErrors.value = data.errors || []
    importSummary.value = data
    if (data.imported_count > 0) {
      ElMessage.success(`已导入 ${data.imported_count} 条课程日程`)
    } else {
      ElMessage.warning('没有导入新课程，请查看跳过说明或检查文件内容。')
    }
    uploadRef.value?.clearFiles()
    selectedFile.value = null
    fileReady.value = false
  } catch (err) {
    parseError.value = err?.message || '文件上传或解析失败，请检查文件格式。'
  } finally {
    uploading.value = false
  }
}

const addManualCourse = async () => {
  if (!manualForm.course_name.trim()) {
    ElMessage.warning('请输入课程名')
    return
  }
  manualSaving.value = true
  try {
    await createCourse({ ...manualForm })
    ElMessage.success('课程添加成功')
    manualForm.course_name = ''
    manualForm.teacher = ''
    manualForm.location = ''
  } catch { /* 拦截器已处理 */ } finally {
    manualSaving.value = false
  }
}
</script>

<style scoped>
.import-page {
  display: grid;
  gap: 16px;
}

.import-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 16px;
  margin-top: 16px;
}

.upload-card {
  display: grid;
  gap: 14px;
}

.upload-icon {
  font-size: 36px;
  color: var(--accent);
}

.upload-actions {
  display: flex;
  gap: 12px;
}

.import-summary,
.parse-result {
  margin-top: 8px;
}

.import-summary {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--success-light);
  border: 1px solid #b8d8c3;
}

.parse-result h4 {
  margin: 10px 0;
  font-size: 14px;
}

.parse-warning,
.parse-error {
  margin-top: 10px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--danger-light);
  border: 1px solid #edc8c6;
  color: var(--danger);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.parse-warning {
  display: block;
  color: var(--warning);
  background: var(--warning-light);
  border-color: #ebd5b0;
}

.parse-warning ul {
  margin: 6px 0 0;
  padding-left: 18px;
}

.parse-error p { margin: 0; }

.manual-card {
  display: grid;
  gap: 4px;
}

.range-sep {
  margin: 0 6px;
  color: var(--text-tertiary);
}

[data-theme="dark"] .parse-error {
  border-color: #5a3a38;
}

@media (max-width: 960px) {
  .import-grid {
    grid-template-columns: 1fr;
  }
}
</style>
