<template>
  <div class="empty-state">
    <p>{{ title }}</p>
    <small>{{ description }}</small>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '等待开发'
  },
  description: {
    type: String,
    default: '这里先保留页面位置，后续接入接口和交互。'
  }
})
</script>

<style scoped>
.empty-state {
  display: grid;
  min-height: 180px;
  place-items: center;
  align-content: center;
  color: #6b7280;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
}

.empty-state p {
  margin: 0;
  color: #374151;
  font-weight: 600;
}

.empty-state small {
  margin-top: 8px;
}
</style>
