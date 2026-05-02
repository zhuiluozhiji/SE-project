<template>
  <section class="import-page fade-in">
    <div class="page-panel">
      <h2 class="page-title">课表导入</h2>
      <p class="muted">导入个人课表后，系统将自动生成课程事件并参与冲突检测。</p>
      <div class="import-grid">
        <div class="card upload-card">
          <el-upload drag action="#" :auto-upload="false" class="upload-zone">
            <p>拖拽 CSV / Excel 文件到这里</p>
            <small class="muted">OCR 截图导入作为后续扩展位保留</small>
          </el-upload>
          <div class="upload-actions">
            <el-button type="primary">选择文件</el-button>
            <el-button>查看示例模板</el-button>
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
        </div>
      </div>
    </div>
  </section>
</template>

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
