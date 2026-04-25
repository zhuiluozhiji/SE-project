<template>
  <section class="page-panel login-panel">
    <h2 class="page-title">登录注册</h2>
    <el-form label-width="72px">
      <el-form-item label="用户名">
        <el-input placeholder="student001" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input type="password" placeholder="请输入密码" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary">登录</el-button>
        <el-button>注册</el-button>
      </el-form-item>
    </el-form>
  </section>
</template>

<style scoped>
.login-panel {
  max-width: 520px;
}
</style>
