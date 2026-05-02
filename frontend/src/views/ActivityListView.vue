<template>
  <section class="activity-page fade-in">
    <div class="page-panel filter-panel">
      <div>
        <h2 class="page-title">活动列表</h2>
        <p class="muted">支持关键词、校区、类别与时间范围的组合筛选。</p>
      </div>
      <el-form class="filter-row" inline>
        <el-form-item label="关键词">
          <el-input placeholder="人工智能 / 讲座 / 学院" />
        </el-form-item>
        <el-form-item label="校区">
          <el-select placeholder="全部校区" clearable>
            <el-option label="紫金港" value="zjg" />
            <el-option label="玉泉" value="yq" />
            <el-option label="西溪" value="xx" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别">
          <el-select placeholder="全部类别" clearable>
            <el-option label="学术讲座" value="lecture" />
            <el-option label="研讨会" value="seminar" />
            <el-option label="工作坊" value="workshop" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary">查询</el-button>
          <el-button>重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card-grid list-grid">
      <article class="card activity-card" v-for="item in activities" :key="item.title">
        <div class="card-top">
          <span class="chip">{{ item.status }}</span>
          <span class="muted">{{ item.time }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="muted">{{ item.summary }}</p>
        <div class="tag-row">
          <span class="chip" v-for="tag in item.tags" :key="tag">{{ tag }}</span>
        </div>
        <div class="card-meta">
          <span>{{ item.location }}</span>
          <el-button size="small" type="primary" plain @click="goDetail(item.id)">
            查看详情
          </el-button>
        </div>
      </article>
    </div>

    <div class="pagination">
      <span class="muted">共 128 场活动</span>
      <el-pagination layout="prev, pager, next" :total="128" :page-size="9" />
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const activities = [
  {
    id: 1,
    title: 'AI 赋能城市治理：从算法到公共服务',
    time: '今天 15:00',
    status: '开放报名',
    location: '紫金港｜行政楼 A302',
    summary: '聚焦城市治理智能化转型，讨论数据治理与公共服务实践案例。',
    tags: ['人工智能', '城市治理', '跨学科']
  },
  {
    id: 2,
    title: '量子信息前沿报告：纠缠与计算的新突破',
    time: '明天 10:30',
    status: '推荐',
    location: '玉泉｜信息学院报告厅',
    summary: '面向研究生与青年学者的前沿分享，含实验室参访机会。',
    tags: ['量子计算', '前沿报告']
  },
  {
    id: 3,
    title: '社会科学数据分析工作坊',
    time: '本周三 13:30',
    status: '名额紧张',
    location: '西溪｜人文楼 402',
    summary: '结合真实调查数据，讲解研究设计、清洗与可视化流程。',
    tags: ['数据分析', '工作坊']
  },
  {
    id: 4,
    title: '新生科研导航：如何选择研究方向',
    time: '本周四 18:00',
    status: '开放报名',
    location: '紫金港｜学术交流中心',
    summary: '面向新生的科研入门交流，学长学姐分享经验路径。',
    tags: ['科研规划', '新生']
  },
  {
    id: 5,
    title: '人文社科青年论坛',
    time: '本周五 14:00',
    status: '学院推荐',
    location: '西溪｜文科楼 201',
    summary: '围绕学术表达与跨学科协作，邀请多学院青年学者对话。',
    tags: ['人文社科', '论坛']
  },
  {
    id: 6,
    title: '科研写作与国际投稿策略分享',
    time: '本周六 16:00',
    status: '热门',
    location: '玉泉｜图书馆报告厅',
    summary: '从选刊、投稿到审稿回复，提供实操策略与案例拆解。',
    tags: ['学术写作', '科研训练']
  }
]

const goDetail = (id) => {
  router.push(`/activities/${id}`)
}
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
