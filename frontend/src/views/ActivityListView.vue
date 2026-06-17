<template>
  <section class="activity-page fade-in">
    <div class="page-panel filter-panel">
      <div class="filter-head">
        <div>
          <h2 class="page-title">活动列表</h2>
          <span class="filter-subtitle">讲座、论坛、沙龙与实践活动</span>
        </div>
        <span class="result-count" v-if="total > 0">共 {{ total }} 场活动</span>
      </div>
      <el-form class="filter-form" label-position="top" @submit.prevent="submitSearch">
        <el-form-item class="filter-field keyword-field" label="关键词">
          <el-input
            v-model="filters.keyword"
            :prefix-icon="Search"
            placeholder="搜索标题或主讲人"
            clearable
          />
        </el-form-item>
        <el-form-item class="filter-field" label="校区">
          <el-select v-model="filters.campus" placeholder="全部校区" clearable>
            <el-option
              v-for="campus in filterOptions.campuses"
              :key="campus"
              :label="campus"
              :value="campus"
            />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-field college-field" label="学院">
          <el-input
            v-model.trim="filters.college"
            placeholder="输入学院名称"
            clearable
          />
        </el-form-item>
        <el-form-item class="filter-field" label="类别">
          <el-select v-model="filters.category" placeholder="全部类别" clearable>
            <el-option
              v-for="category in filterOptions.categories"
              :key="category"
              :label="category"
              :value="category"
            />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-field" label="排序">
          <el-select v-model="filters.sort" placeholder="默认排序" clearable>
            <el-option label="最新发布" value="time" />
            <el-option label="最热门" value="hot" />
            <el-option label="推荐优先" value="recommend" />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions">
          <el-button type="primary" :icon="Search" @click="submitSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>

      <div v-if="activeFilterChips.length" class="active-filters">
        <span class="active-label">已筛选</span>
        <el-tag
          v-for="chip in activeFilterChips"
          :key="chip.key"
          class="active-chip"
          closable
          effect="plain"
          @close="removeFilter(chip.key)"
        >
          {{ chip.label }}：{{ chip.value }}
        </el-tag>
      </div>
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

      <div v-else ref="gridRef" class="card-grid list-grid">
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
        @current-change="changePage"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { getActivities, getActivityFilterOptions } from '../api/activities'
import ActivityCard from '../components/ActivityCard.vue'

const route = useRoute()

const loading = ref(false)
const error = ref('')
const activities = ref([])
const total = ref(0)
const gridRef = ref(null)

const filters = reactive({
  keyword: '',
  campus: '',
  college: '',
  category: '',
  sort: ''
})

const filterOptions = reactive({
  campuses: ['紫金港', '玉泉', '西溪', '华家池', '之江', '舟山', '海宁'],
  categories: ['讲座', '沙龙', '论坛', 'Workshop']
})

const pagination = reactive({
  page: 1,
  pageSize: 12
})

const rowsPerPage = 3
let resizeTimer = null

const sortLabels = {
  time: '最新发布',
  hot: '最热门',
  recommend: '推荐优先'
}

const activeFilterChips = computed(() => {
  const chips = []
  if (filters.keyword) chips.push({ key: 'keyword', label: '关键词', value: filters.keyword })
  if (filters.campus) chips.push({ key: 'campus', label: '校区', value: filters.campus })
  if (filters.college) chips.push({ key: 'college', label: '学院', value: filters.college })
  if (filters.category) chips.push({ key: 'category', label: '类别', value: filters.category })
  if (filters.sort) chips.push({ key: 'sort', label: '排序', value: sortLabels[filters.sort] || filters.sort })
  return chips
})

const getRenderedColumnCount = () => {
  const grid = gridRef.value
  if (!grid) return 0

  const columns = window.getComputedStyle(grid).gridTemplateColumns
  if (!columns || columns === 'none') return 0

  return columns.split(' ').filter(Boolean).length
}

const syncPageSizeWithGrid = () => {
  const columns = getRenderedColumnCount()
  if (!columns) return false

  const nextPageSize = columns * rowsPerPage
  if (nextPageSize === pagination.pageSize) return false

  const firstVisibleIndex = (pagination.page - 1) * pagination.pageSize
  pagination.pageSize = nextPageSize
  pagination.page = Math.floor(firstVisibleIndex / nextPageSize) + 1
  return true
}

const refetchIfPageSizeChanged = async () => {
  await nextTick()
  if (syncPageSizeWithGrid()) {
    await fetchActivities({ skipAdaptiveSync: true })
  }
}

const handleResize = () => {
  window.clearTimeout(resizeTimer)
  resizeTimer = window.setTimeout(() => {
    refetchIfPageSizeChanged()
  }, 180)
}

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

const fetchActivities = async (options = {}) => {
  loading.value = true
  error.value = ''
  try {
    const params = { page: pagination.page, page_size: pagination.pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.campus) params.campus = filters.campus
    if (filters.college) params.college = filters.college
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

  if (!options.skipAdaptiveSync) {
    await refetchIfPageSizeChanged()
  }
}

const submitSearch = () => {
  pagination.page = 1
  fetchActivities()
}

const changePage = (page) => {
  pagination.page = page
  fetchActivities()
}

const reset = () => {
  filters.keyword = ''
  filters.campus = ''
  filters.college = ''
  filters.category = ''
  filters.sort = ''
  pagination.page = 1
  fetchActivities()
}

const removeFilter = (key) => {
  if (!Object.prototype.hasOwnProperty.call(filters, key)) return
  filters[key] = ''
  pagination.page = 1
  fetchActivities()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (route.query.keyword) filters.keyword = route.query.keyword
  if (route.query.college) filters.college = route.query.college
  if (route.query.sort) filters.sort = route.query.sort
  loadFilterOptions()
  fetchActivities()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.clearTimeout(resizeTimer)
})
</script>

<style scoped>
.activity-page {
  display: grid;
  gap: 20px;
  min-width: 0;
}

.filter-panel {
  --filter-control-height: 48px;
  display: grid;
  gap: 18px;
  padding: 28px;
  min-width: 0;
}

.filter-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.filter-subtitle {
  display: block;
  margin-top: 6px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.result-count {
  flex-shrink: 0;
  padding: 7px 12px;
  color: var(--text-secondary);
  background: var(--bg-warm);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1;
}

.filter-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(180px, 100%), 1fr));
  gap: 14px;
  align-items: end;
  min-width: 0;
}

.filter-form :deep(.el-form-item) {
  margin: 0;
  min-width: 0;
}

.filter-form :deep(.el-form-item__label) {
  margin-bottom: 7px;
  padding: 0;
  color: var(--text-secondary);
  font-weight: 600;
  line-height: 1.2;
}

.filter-field :deep(.el-input),
.filter-field :deep(.el-select) {
  width: 100%;
  height: var(--filter-control-height);
  min-width: 0;
}

.filter-field :deep(.el-input__wrapper),
.filter-field :deep(.el-select__wrapper) {
  width: 100%;
  height: var(--filter-control-height);
  min-height: var(--filter-control-height);
  box-sizing: border-box;
  background: var(--bg-surface);
  box-shadow: 0 0 0 1px var(--border) inset;
}

.filter-field :deep(.el-select__wrapper) {
  padding-top: 0;
  padding-bottom: 0;
}

.filter-field :deep(.el-input__inner) {
  height: calc(var(--filter-control-height) - 2px);
  line-height: calc(var(--filter-control-height) - 2px);
}

.filter-field :deep(.el-input__wrapper.is-focus),
.filter-field :deep(.el-input__wrapper:hover),
.filter-field :deep(.el-select__wrapper.is-focused),
.filter-field :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--accent) inset;
}

.filter-actions :deep(.el-form-item__content) {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-actions :deep(.el-button) {
  flex: 1 1 78px;
  height: var(--filter-control-height);
  margin-left: 0;
  min-width: 0;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 2px;
}

.active-label {
  color: var(--text-tertiary);
  font-size: 13px;
}

.active-chip {
  max-width: 100%;
  border-color: var(--border);
  background: var(--bg-warm);
  color: var(--text-secondary);
}

.list-body {
  min-height: 200px;
}

.list-grid {
  grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr));
  grid-auto-rows: 1fr;
  align-items: stretch;
  gap: 16px;
}

.pag-row {
  display: flex;
  justify-content: center;
}

@media (max-width: 960px) {
  .filter-panel {
    padding: 24px;
  }

  .filter-head {
    flex-direction: column;
  }
}

@media (max-width: 560px) {
  .filter-panel {
    padding: 20px;
  }

  .filter-form {
    grid-template-columns: 1fr;
  }

  .filter-actions :deep(.el-form-item__content) {
    flex-direction: column;
  }

  .result-count {
    width: 100%;
    text-align: center;
  }
}
</style>
