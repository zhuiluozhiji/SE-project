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
            <small class="muted">支持 .csv / .xlsx / .xls 格式</small>
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

        <div class="card format-card">
          <h3 class="section-title">示例格式说明</h3>
          <ul>
            <li>课程名（必填）</li>
            <li>星期（1-7）与节次（如 1-2）</li>
            <li>起止时间（24h）</li>
            <li>校区 / 教室 / 授课教师</li>
          </ul>
          <div class="format-tip">
            <strong>解析失败时定位到具体错误行，便于快速修正。</strong>
          </div>
          <div class="divider"></div>
          <h3 class="section-title">手动录入</h3>
          <el-form :model="manualForm" label-width="80px" size="small">
            <el-form-item label="课程名">
              <el-input v-model="manualForm.course_name" placeholder="如：高等数学" />
            </el-form-item>
            <el-form-item label="授课教师">
              <el-input v-model="manualForm.teacher" placeholder="教师姓名" />
            </el-form-item>
            <el-form-item label="星期">
              <el-select v-model="manualForm.weekday" placeholder="选择">
                <el-option v-for="i in 7" :key="i" :label="'周' + i" :value="i" />
              </el-select>
            </el-form-item>
            <el-form-item label="节次">
              <el-input-number v-model="manualForm.start_section" :min="1" :max="12" /> -
              <el-input-number v-model="manualForm.end_section" :min="1" :max="12" />
            </el-form-item>
            <el-form-item label="教室">
              <el-input v-model="manualForm.location" placeholder="如：教学楼A101" />
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

const handleFileChange = (file) => {
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
  } catch {
    // 错误已在拦截器中处理
  } finally {
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
  margin-top: 12px;
}

.upload-card {
  display: grid;
  gap: 12px;
}

.upload-icon {
  font-size: 40px;
  color: #0f766e;
}

.upload-actions {
  display: flex;
  gap: 12px;
}

.parse-result {
  margin-top: 8px;
}

.parse-result h4 {
  margin: 8px 0;
}

.parse-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.parse-error {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fef2f2;
  border: 1px solid #f5c6cb;
  color: #b91c1c;
  font-size: 13px;
}

.format-card ul {
  margin: 0;
  padding-left: 18px;
  color: #6f6a5f;
}

.format-tip {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fef4e1;
  border-radius: 10px;
  border: 1px solid #f3d8b4;
}

@media (max-width: 960px) {
  .import-grid {
    grid-template-columns: 1fr;
  }
}
</style>
