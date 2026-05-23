<template>
  <section class="activity-page fade-in">
    <div class="page-panel filter-panel">
      <div>
        <h2 class="page-title">活动列表</h2>
        <p class="muted">支持关键词、校区、类别与时间范围的组合筛选。</p>
      </div>
      <el-form class="filter-row" inline @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="人工智能 / 讲座 / 学院" clearable />
        </el-form-item>
        <el-form-item label="校区">
          <el-select v-model="filters.campus" placeholder="全部校区" clearable>
            <el-option label="紫金港" value="紫金港" />
            <el-option label="玉泉" value="玉泉" />
            <el-option label="西溪" value="西溪" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="filters.category" placeholder="全部类别" clearable>
            <el-option label="讲座" value="讲座" />
            <el-option label="研讨会" value="研讨会" />
            <el-option label="工作坊" value="工作坊" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadActivities">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card-grid list-grid" v-loading="loading">
      <article class="card activity-card" v-for="item in activities" :key="item.id">
        <div class="card-top">
          <span class="chip">{{ statusLabel(item.status) }}</span>
          <span class="muted">{{ formatTime(item.start_time) }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="muted">{{ item.description || '暂无活动简介。' }}</p>
        <div class="tag-row">
          <span class="chip" v-for="tag in item.tags || []" :key="tag">{{ tag }}</span>
          <span v-if="!item.tags?.length" class="muted">暂无标签</span>
        </div>
        <div class="card-meta">
          <span>{{ item.location || '地点待定' }}</span>
          <el-button size="small" type="primary" plain @click="goDetail(item.id)">
            查看详情
          </el-button>
        </div>
      </article>
    </div>

    <div class="pagination">
      <span class="muted">共 {{ total }} 场活动</span>
      <el-pagination
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getActivities } from '../api/activities'

const router = useRouter()
const activities = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(9)
const loading = ref(false)
const filters = reactive({
  keyword: '',
  campus: '',
  category: ''
})

const loadActivities = async () => {
  loading.value = true
  try {
    const res = await getActivities({
      ...filters,
      page: page.value,
      page_size: pageSize.value
    })
    if (res.code === 0) {
      activities.value = res.data.items || []
      total.value = res.data.total || activities.value.length
    } else {
      ElMessage.error(res.message || '活动加载失败')
    }
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.campus = ''
  filters.category = ''
  page.value = 1
  loadActivities()
}

const handlePageChange = (value) => {
  page.value = value
  loadActivities()
}

const goDetail = (id) => {
  router.push(`/activities/${id}`)
}

const statusLabel = (status) => {
  return status === 'open' ? '开放报名' : '已下架'
}

const formatTime = (value) => {
  if (!value) return '时间待定'
  const date = new Date(value)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
}

onMounted(loadActivities)
</script>

<style scoped>
.activity-page {
  display: grid;
  gap: 20px;
}

.filter-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.list-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.activity-card h3 {
  margin: 8px 0 6px;
  font-size: 18px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

@media (max-width: 960px) {
  .filter-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-row {
    justify-content: flex-start;
  }
}
</style>
