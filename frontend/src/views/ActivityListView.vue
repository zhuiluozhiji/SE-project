<template>
  <section class="activity-page fade-in">
    <div class="page-panel filter-bar">
      <div class="filter-head">
        <h2 class="page-title">活动列表</h2>
        <span class="faint" v-if="total > 0">共 {{ total }} 场活动</span>
      </div>
      <el-form class="filter-row" inline @submit.prevent="search">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            class="keyword-input"
            placeholder="搜索标题或主讲人"
            clearable
          />
        </el-form-item>
        <el-form-item label="校区">
          <el-select v-model="filters.campus" class="filter-select" placeholder="全部校区" clearable>
            <el-option
              v-for="campus in filterOptions.campuses"
              :key="campus"
              :label="campus"
              :value="campus"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="filters.category" class="filter-select" placeholder="全部类别" clearable>
            <el-option
              v-for="category in filterOptions.categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="filters.sort" class="sort-select" placeholder="默认排序" clearable>
            <el-option label="最新发布" value="time" />
            <el-option label="最热门" value="hot" />
            <el-option label="推荐优先" value="recommend" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-loading="loading" class="list-body">
      <div v-if="error" class="empty-state">
        <p>加载失败</p>
        <small>{{ error }}</small>
        <el-button type="primary" size="small" @click="search">重试</el-button>
      </div>

      <div v-else-if="!loading && activities.length === 0" class="empty-state">
        <p>暂无活动</p>
        <small>试试调整筛选条件或清除关键词</small>
      </div>

      <div v-else class="card-grid list-grid">
        <ActivityCard
          v-for="item in activities"
          :key="item.id"
          :activity="item"
        />
      </div>
    </div>

    <div class="pag-row" v-if="total > 0">
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="search"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getActivities, getActivityFilterOptions } from '../api/activities'
import ActivityCard from '../components/ActivityCard.vue'

const route = useRoute()

const loading = ref(false)
const error = ref('')
const activities = ref([])
const total = ref(0)

const filters = reactive({
  keyword: '',
  campus: '',
  category: '',
  sort: ''
})

const filterOptions = reactive({
  campuses: ['紫金港', '玉泉', '西溪', '华家池', '之江', '舟山', '海宁'],
  categories: ['讲座', '沙龙', '论坛', 'Workshop']
})

const pagination = reactive({
  page: 1,
  pageSize: 9
})

const loadFilterOptions = async () => {
  try {
    const res = await getActivityFilterOptions()
    filterOptions.campuses = res.data?.campuses?.length
      ? res.data.campuses
      : filterOptions.campuses
    filterOptions.categories = res.data?.categories?.length
      ? res.data.categories
      : filterOptions.categories
  } catch {
    // Keep local defaults so the filter bar remains usable if the options endpoint fails.
  }
}

const search = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.campus) params.campus = filters.campus
    if (filters.category) params.category = filters.category
    if (filters.sort) params.sort_by = filters.sort

    const res = await getActivities(params)
    activities.value = res.data?.items || res.data?.activities || res.data || []
    total.value = res.data?.total || 0
  } catch (e) {
    error.value = e.message || '网络异常'
  } finally {
    loading.value = false
  }
}

const reset = () => {
  filters.keyword = ''
  filters.campus = ''
  filters.category = ''
  filters.sort = ''
  pagination.page = 1
  search()
}

onMounted(() => {
  if (route.query.keyword) filters.keyword = route.query.keyword
  loadFilterOptions()
  search()
})
</script>

<style scoped>
.activity-page {
  display: grid;
  gap: 20px;
}

.filter-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-head {
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.filter-row :deep(.el-form-item) {
  margin-right: 0;
}

.keyword-input {
  width: 220px;
}

.filter-select {
  width: 140px;
}

.sort-select {
  width: 150px;
}

.list-body {
  min-height: 200px;
}

.list-grid {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.pag-row {
  display: flex;
  justify-content: center;
}

@media (max-width: 960px) {
  .filter-bar {
    flex-direction: column;
  }
  .filter-row {
    justify-content: flex-start;
  }
  .keyword-input,
  .filter-select,
  .sort-select {
    width: min(100%, 260px);
  }
}
</style>
