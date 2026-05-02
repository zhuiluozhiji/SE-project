<template>
  <section class="profile-page fade-in">
    <div class="card profile-card">
      <div class="profile-header">
        <div class="avatar">SZ</div>
        <div>
          <h2 class="page-title">张伟</h2>
          <p class="muted">计算机科学与技术学院 · 大三 </p>
        </div>
      </div>
      <div class="profile-meta">
        <div>
          <span class="muted">已加入活动</span>
          <strong>6</strong>
        </div>
        <div>
          <span class="muted">兴趣标签</span>
          <strong>8</strong>
        </div>
        <div>
          <span class="muted">本周冲突</span>
          <strong>2</strong>
        </div>
      </div>
    </div>

    <div class="profile-grid">
      <div class="card">
        <h3 class="section-title">兴趣标签</h3>
        <div class="tag-row">
          <span class="chip">人工智能</span>
          <span class="chip">知识图谱</span>
          <span class="chip">学术写作</span>
          <span class="chip">数据可视化</span>
          <span class="chip">跨学科协作</span>
        </div>
        <p class="muted">推荐理由将基于以上标签生成。</p>
      </div>
      <div class="card">
        <h3 class="section-title">学术轨迹</h3>
        <div class="timeline">
          <div class="timeline-item">
            <span class="dot"></span>
            <div>
              <strong>参加：AI 赋能城市治理</strong>
              <p class="muted">2026-05-01 · 紫金港</p>
            </div>
          </div>
          <div class="timeline-item">
            <span class="dot"></span>
            <div>
              <strong>收藏：科研写作工作坊</strong>
              <p class="muted">2026-04-28 · 玉泉</p>
            </div>
          </div>
          <div class="timeline-item">
            <span class="dot"></span>
            <div>
              <strong>报名：跨学科研讨会</strong>
              <p class="muted">2026-04-20 · 西溪</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.profile-page {
  display: grid;
  gap: 16px;
}

.profile-card {
  display: grid;
  gap: 14px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
}

.profile-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.profile-meta strong {
  display: block;
  font-size: 20px;
  margin-top: 4px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.timeline {
  display: grid;
  gap: 12px;
}

.timeline-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.timeline-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e27a38;
  margin-top: 6px;
}
</style>
