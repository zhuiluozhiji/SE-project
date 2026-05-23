<template>
  <div class="empty-state">
    <p>{{ title }}</p>
    <small>{{ description }}</small>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无内容' },
  description: { type: String, default: '此处暂时没有数据，请稍后再来。' }
})
</script>

<style scoped>
.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  min-height: 180px;
  color: var(--text-tertiary);
  border: 1px dashed var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-warm);
  gap: 6px;
}

.empty-state p {
  margin: 0;
  color: var(--text-secondary);
  font-weight: 500;
}

.empty-state small {
  font-size: 13px;
}
</style>
