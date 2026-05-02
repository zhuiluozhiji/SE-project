<template>
  <section class="login-page fade-in">
    <div class="login-hero">
      <h2>校园学术活动智能推荐平台</h2>
      <p>以兴趣为线索，连接活动发现、日程管理与学术成长轨迹。</p>
      <div class="hero-stats">
        <div>
          <strong>1,280</strong>
          <span>已汇聚活动</span>
        </div>
        <div>
          <strong>92%</strong>
          <span>推荐匹配率</span>
        </div>
      </div>
    </div>
    <div class="card login-card">
      <h2 class="page-title">登录注册</h2>
      <el-form label-width="72px">
        <el-form-item label="用户名">
          <el-input placeholder="student001" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large">登录</el-button>
          <el-button size="large">注册</el-button>
        </el-form-item>
      </el-form>
      <p class="muted">登录后可同步课表、生成日程冲突提示与个性化推荐。</p>
    </div>
  </section>
</template>

<style scoped>
.login-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr);
  gap: 20px;
}

.login-hero {
  padding: 24px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f6efe4 0%, #f2dfc5 60%, #f0d2b1 100%);
  border: 1px solid #eadac6;
  box-shadow: 0 14px 30px rgba(54, 40, 18, 0.1);
}

.login-hero h2 {
  margin: 0 0 8px;
  font-family: "Noto Serif SC", "Noto Sans SC", serif;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.hero-stats strong {
  display: block;
  font-size: 22px;
}

.login-card {
  align-self: center;
}

@media (max-width: 960px) {
  .login-page {
    grid-template-columns: 1fr;
  }
}
</style>
