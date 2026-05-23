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
            :auto-upload="false"
            :limit="1"
            accept=".csv,.xlsx,.xls"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <p>拖拽 CSV / Excel 文件到这里</p>
            <small class="faint">支持 .csv / .xlsx / .xls 格式</small>
          </el-upload>
          <div class="upload-actions">
            <el-button type="primary" :loading="uploading" @click="submitFile" :disabled="!fileReady">
              上传并解析
            </el-button>
            <el-button @click="showTemplate">查看示例模板</el-button>
          </div>

          <div v-if="parseResult" class="parse-result">
            <h4>解析结果</h4>
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
            <div class="parse-actions">
              <el-button type="primary" size="small" :loading="saving" @click="saveCourses">
                确认导入
              </el-button>
              <el-button size="small" @click="parseResult = null">清除重选</el-button>
            </div>
          </div>

          <div v-if="parseError" class="parse-error">
            <p>{{ parseError }}</p>
            <el-button size="small" @click="parseError = ''">重试</el-button>
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
              <el-input-number v-model="manualForm.start_section" :min="1" :max="12" size="small" />
              <span class="range-sep">&ndash;</span>
              <el-input-number v-model="manualForm.end_section" :min="1" :max="12" size="small" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="small" :loading="manualSaving" @click="addManualCourse">
                添加课程
              </el-button>
            </el-form-item>
          </el-form>

          <div class="divider"></div>
          <div class="format-hint">
            <strong>文件格式说明</strong>
            <p class="faint">支持 CSV / Excel，包含列：课程名、星期(1-7)、节次(如 1-2)、起止时间、教室、授课教师。</p>
          </div>
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
const fileReady = ref(false)
const uploading = ref(false)
const saving = ref(false)
const manualSaving = ref(false)
const parseResult = ref(null)
const parseError = ref('')

const manualForm = reactive({
  course_name: '',
  teacher: '',
  weekday: 1,
  start_section: 1,
  end_section: 2,
  location: ''
})

const handleFileChange = () => {
  parseResult.value = null
  parseError.value = ''
  fileReady.value = true
}

const handleFileRemove = () => {
  fileReady.value = false
  parseResult.value = null
  parseError.value = ''
}

const submitFile = async () => {
  if (!uploadRef.value) return
  const files = uploadRef.value.uploadFiles
  if (!files.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  parseError.value = ''
  try {
    const formData = new FormData()
    formData.append('file', files[0].raw)
    const res = await importCourses(formData)
    parseResult.value = res.data?.courses || res.data?.items || res.data || []
    ElMessage.success(`解析成功，共 ${parseResult.value.length} 门课程`)
  } catch {
    parseError.value = '文件上传或解析失败，请检查文件格式'
  } finally {
    uploading.value = false
  }
}

const saveCourses = async () => {
  saving.value = true
  try {
    for (const course of parseResult.value) {
      await createCourse(course)
    }
    ElMessage.success(`成功导入 ${parseResult.value.length} 门课程`)
    parseResult.value = null
    uploadRef.value?.clearFiles()
    fileReady.value = false
  } catch {
    ElMessage.error('保存课程失败')
  } finally {
    saving.value = false
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

const showTemplate = () => {
  ElMessage.info('示例格式：课程名,星期,开始节次,结束节次,教师,教室')
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

.parse-result {
  margin-top: 8px;
}

.parse-result h4 {
  margin: 10px 0;
  font-size: 14px;
}

.parse-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

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

.parse-error p { margin: 0; }

.manual-card {
  display: grid;
  gap: 4px;
}

.range-sep {
  margin: 0 6px;
  color: var(--text-tertiary);
}

.format-hint {
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--warning-light);
  border: 1px solid #ebd5b0;
}

.format-hint strong {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
}

.format-hint p { font-size: 12px; }

[data-theme="dark"] .parse-error {
  border-color: #5a3a38;
}

[data-theme="dark"] .format-hint {
  border-color: #5a4a2a;
}

@media (max-width: 960px) {
  .import-grid {
    grid-template-columns: 1fr;
  }
}
</style>
