<template>
  <section class="import-page fade-in">
    <div class="page-panel">
      <h2 class="page-title">课表导入</h2>
      <p class="muted">导入个人课表后，系统将自动生成课程事件并参与冲突检测。</p>
      <div class="import-grid">
        <div class="card upload-card">
          <el-upload
            ref="uploadRef"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
            class="upload-zone"
          >
            <p>拖拽 CSV / XLSX 文件到这里</p>
            <small class="muted">请使用右侧示例表头；截图 OCR 仍为预留能力。</small>
          </el-upload>
          <div class="upload-actions">
            <el-button type="primary" :loading="importing" :disabled="!selectedFile" @click="submitImport">
              导入课表
            </el-button>
            <el-button @click="downloadTemplate">下载示例模板</el-button>
          </div>
          <div v-if="selectedFile" class="file-note">
            <strong>{{ selectedFile.name }}</strong>
            <span class="muted">{{ fileSizeText }}</span>
          </div>
          <div v-if="lastError" class="import-error">
            <strong>导入失败</strong>
            <p>{{ lastError }}</p>
            <pre>{{ templateCsv }}</pre>
          </div>
          <div v-if="importResult" class="import-result">
            <strong>已导入 {{ importResult.imported_count }} 门课程</strong>
            <p class="muted">跳过 {{ importResult.skipped_count }} 行，可前往日历查看课程事件。</p>
            <ul v-if="importResult.errors?.length">
              <li v-for="error in importResult.errors" :key="error">{{ error }}</li>
            </ul>
          </div>
        </div>
        <div class="card format-card">
          <h3 class="section-title">示例格式说明</h3>
          <ul>
            <li>必填：课程名、星期、节次</li>
            <li>星期：1-7、周一、星期一均可</li>
            <li>节次：3-4，或拆成开始节次和结束节次</li>
            <li>可选：地点、教师、周次</li>
            <li>也支持教务导出的课表：课程名称、教师姓名、上课时间、上课地点</li>
          </ul>
          <div class="template-table">
            <div class="template-row header">
              <span v-for="header in template.headers" :key="header">{{ header }}</span>
            </div>
            <div class="template-row" v-for="(row, index) in template.rows" :key="index">
              <span v-for="(cell, cellIndex) in row" :key="cellIndex">{{ cell }}</span>
            </div>
          </div>
          <div class="format-tip">
            <strong>解析失败时会定位到具体错误行。</strong>
            <p class="muted">如果不确定格式，先下载模板，在模板上替换自己的课程。</p>
            <p class="muted">教务导出格式会自动拆分多个上课时段，例如“周一第3,4,5节;周三第1,2节”。</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getCourseTemplate, importCourses } from '../api/courses'

const uploadRef = ref(null)
const selectedFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const lastError = ref('')
const template = ref({
  headers: ['课程名', '星期', '节次', '地点', '教师', '周次'],
  rows: [['软件工程', '周二', '3-4', '玉泉曹楼', '李老师', '1-16']]
})

const templateCsv = computed(() => {
  const lines = [template.value.headers.join(',')]
  for (const row of template.value.rows) lines.push(row.join(','))
  return lines.join('\n')
})

const fileSizeText = computed(() => {
  if (!selectedFile.value) return ''
  const kb = selectedFile.value.size / 1024
  return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`
})

const loadTemplate = async () => {
  const res = await getCourseTemplate()
  if (res.code === 0) template.value = res.data
}

const handleFileChange = (file) => {
  const rawFile = file.raw
  const name = rawFile.name.toLowerCase()
  const isAllowed = name.endsWith('.csv') || name.endsWith('.xlsx') || name.endsWith('.xlsm')
  if (!isAllowed) {
    selectedFile.value = null
    uploadRef.value?.clearFiles()
    ElMessage.error('仅支持 CSV、XLSX 或 XLSM 课表文件。请下载示例模板后重试。')
    return
  }
  selectedFile.value = rawFile
  importResult.value = null
  lastError.value = ''
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const handleExceed = () => {
  ElMessage.warning('一次只能导入一个课表文件，请先移除当前文件。')
}

const submitImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个 CSV 或 XLSX 课表文件。')
    return
  }

  importing.value = true
  lastError.value = ''
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await importCourses(formData)
    if (res.code === 0) {
      importResult.value = res.data
      if (res.data.imported_count > 0) {
        ElMessage.success(`已导入 ${res.data.imported_count} 门课程`)
      } else {
        ElMessage.warning('没有导入任何课程，请检查文件内容。')
      }
    } else {
      lastError.value = res.message || '课表导入失败，请检查表头和课程行。'
      ElMessage.error(lastError.value)
    }
  } catch {
    lastError.value = '网络或服务异常，请确认后端服务正在运行后重试。'
    ElMessage.error(lastError.value)
  } finally {
    importing.value = false
  }
}

const downloadTemplate = () => {
  const blob = new Blob([templateCsv.value], { type: 'text/csv;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'course-template.csv'
  link.click()
  window.URL.revokeObjectURL(url)
}

onMounted(loadTemplate)
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

.upload-zone {
  width: 100%;
}

.upload-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.file-note,
.import-result,
.import-error {
  padding: 12px;
  border-radius: 10px;
}

.file-note {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  background: #f7fafc;
  border: 1px solid #d8e2eb;
}

.format-card ul {
  margin: 0;
  padding-left: 18px;
  color: #6f6a5f;
}

.template-table {
  margin-top: 12px;
  overflow-x: auto;
  border: 1px solid #e2d3c0;
  border-radius: 8px;
}

.template-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(72px, 1fr));
  min-width: 520px;
}

.template-row span {
  padding: 8px;
  border-right: 1px solid #e2d3c0;
  border-bottom: 1px solid #e2d3c0;
  font-size: 12px;
}

.template-row span:last-child {
  border-right: 0;
}

.template-row:last-child span {
  border-bottom: 0;
}

.template-row.header {
  background: #f8efe2;
  font-weight: 600;
}

.format-tip {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fef4e1;
  border-radius: 10px;
  border: 1px solid #f3d8b4;
}

.format-tip p {
  margin: 4px 0 0;
}

.import-result {
  border: 1px solid #cde7df;
  background: #eefaf6;
}

.import-result ul {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #b42318;
}

.import-error {
  border: 1px solid #f0d1c8;
  background: #fff4f1;
}

.import-error p {
  margin: 6px 0;
  color: #b42318;
}

.import-error pre {
  margin: 8px 0 0;
  padding: 10px;
  overflow-x: auto;
  border-radius: 8px;
  background: #ffffff;
  color: #5b5142;
  font-size: 12px;
}

@media (max-width: 960px) {
  .import-grid {
    grid-template-columns: 1fr;
  }
}
</style>
