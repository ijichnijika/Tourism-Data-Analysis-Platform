<script setup>
import { ref } from 'vue'
import { searchSpots } from '@/api/analysis'
import { Search } from '@element-plus/icons-vue'

const keyword = ref('')
const searchResult = ref([])
const emit = defineEmits(['select'])

const handleSearch = async () => {
  if (!keyword.value) return
  try {
    const res = await searchSpots(keyword.value)
    searchResult.value = res
  } catch (error) {
    console.error(error)
  }
}

const handleSelect = (item) => {
  emit('select', item)
  searchResult.value = []
  keyword.value = ''
}
</script>

<template>
  <div class="search-container">
    <el-input
      v-model="keyword"
      placeholder="搜索景点..."
      class="search-input"
      @keyup.enter="handleSearch"
    >
      <template #prefix>
        <el-icon class="el-input__icon"><search /></el-icon>
      </template>
    </el-input>
    
    <div v-if="searchResult.length > 0" class="search-dropdown">
      <div 
        v-for="item in searchResult" 
        :key="item.scenicId" 
        class="search-item"
        @click="handleSelect(item)"
      >
        {{ item.scenicName }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-container {
  position: relative;
  width: 300px;
}

.search-input :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.1);
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.search-input :deep(.el-input__inner) {
  color: #fff;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background: #1f2d3d;
  border: 1px solid #333;
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  border-radius: 4px;
  margin-top: 5px;
}

.search-item {
  padding: 10px;
  cursor: pointer;
  color: #fff;
}

.search-item:hover {
  background: #2c3e50;
}
</style>
