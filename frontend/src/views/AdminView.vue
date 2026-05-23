<template>
  <section class="admin-page fade-in">
    <div class="page-panel admin-top">
      <div>
        <h2 class="page-title">后台管理</h2>
        <p class="muted">活动维护、标签修正与爬虫任务统一管理。</p>
      </div>
      <div class="admin-actions">
        <el-button type="primary" @click="openActivityDialog()">新增活动</el-button>
        <el-button :loading="crawlerRunning" @click="runCrawler">触发爬虫</el-button>
        <el-button @click="showCrawlerLogs = true">查看日志</el-button>
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
      <el-form-item label="开始时间">
        <el-date-picker v-model="activityForm.start_time" type="datetime" placeholder="选择开始时间" />
      </el-form-item>
      <el-form-item label="结束时间">
        <el-date-picker v-model="activityForm.end_time" type="datetime" placeholder="选择结束时间" />
      </el-form-item>
      <el-form-item label="活动简介">
        <el-input v-model="activityForm.description" type="textarea" :rows="3" placeholder="活动描述" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="activityDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="savingActivity" @click="submitActivity">
        {{ editingActivity ? '保存修改' : '创建活动' }}
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getActivities } from '../api/activities'
import { createActivity, updateActivity, offlineActivity, runCrawler as runCrawlerApi } from '../api/admin'
import StatusTag from '../components/StatusTag.vue'

const loading = ref(false)
const activities = ref([])
const searchTitle = ref('')
const savingActivity = ref(false)
const crawlerRunning = ref(false)
const showCrawlerLogs = ref(false)
const crawlerLogsLoading = ref(false)
const crawlerRecords = ref([])

const activityDialogVisible = ref(false)
const editingActivity = ref(null)

const defaultForm = () => ({
  title: '',
  speaker: '',
  organizer: '',
  campus: '',
  category: '',
  location: '',
  start_time: null,
  end_time: null,
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
      description: row.description || ''
    })
  } else {
    Object.assign(activityForm, defaultForm())
  }
  activityDialogVisible.value = true
}

const submitActivity = async () => {
  savingActivity.value = true
  try {
    const data = { ...activityForm }
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

const runCrawler = async () => {
  crawlerRunning.value = true
  try {
    await runCrawlerApi({ source: 'cs_zju' })
    ElMessage.success('爬虫任务已触发')
  } catch { /* 拦截器已处理 */ } finally {
    crawlerRunning.value = false
  }
}

onMounted(fetchActivities)
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
