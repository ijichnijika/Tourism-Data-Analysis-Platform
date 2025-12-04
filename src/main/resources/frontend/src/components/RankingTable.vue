<script setup>
import { ref, onMounted, watch } from 'vue'
import { getRegionalRank, getHotelStats, searchSpots } from '@/api/analysis'
import axios from 'axios'

import { ElMessage } from 'element-plus'

const props = defineProps({
  cityId: {
    type: Number,
    default: 31 // Default to Hong Kong
  }
})

const rankMode = ref('scenic') // scenic, city, hotel, search
const rankingData = ref([])
const cityData = ref([])
const hotelData = ref([])
const searchData = ref([])
const isSearchActive = ref(false)
const searchInputRef = ref(null)
const sortType = ref('popularity')
const citySortType = ref('sales')
const searchKeyword = ref('')
const loading = ref(false)

const toggleSearch = () => {
  isSearchActive.value = !isSearchActive.value
  if (isSearchActive.value) {
    // Focus input next tick
    setTimeout(() => {
      searchInputRef.value?.focus()
    }, 100)
  } else {
    searchKeyword.value = ''
    searchData.value = []
  }
}

watch(() => searchKeyword.value, (newVal) => {
    if (newVal) {
        handleSearch()
    }
})

const loadRanking = async () => {
  loading.value = true
  try {
    // If cityId is null, use default or handle it
    const id = props.cityId || 31
    const res = await getRegionalRank(id, sortType.value)
    rankingData.value = res
  } catch (error) {
    console.error(error)
    ElMessage.error('获取排名数据失败')
  } finally {
    loading.value = false
  }
}

const loadCityStats = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/analysis/stats/scenic')
    let data = res.data.data || []
    if (citySortType.value === 'score') {
      data = data.sort((a, b) => b.avgScore - a.avgScore)
    } else {
      data = data.sort((a, b) => b.totalSales - a.totalSales)
    }
    cityData.value = data.slice(0, 15)
  } catch (error) {
    console.error(error)
    ElMessage.error('获取城市统计失败')
  } finally {
    loading.value = false
  }
}

const loadHotelStats = async () => {
  loading.value = true
  try {
    const res = await getHotelStats()
    hotelData.value = res
  } catch (error) {
    console.error(error)
    ElMessage.error('获取酒店数据失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchKeyword.value) return
  // loading.value = true // Search is instant usually, but can add if needed
  try {
    const res = await searchSpots(searchKeyword.value)
    searchData.value = res
  } catch (error) {
    console.error(error)
  }
}

const handleSortChange = (type) => {
  sortType.value = type
  loadRanking()
}

const handleCitySortChange = (type) => {
  citySortType.value = type
  loadCityStats()
}

const switchMode = (mode) => {
  rankMode.value = mode
  if (mode === 'scenic' && rankingData.value.length === 0) {
    loadRanking()
  } else if (mode === 'city' && cityData.value.length === 0) {
    loadCityStats()
  } else if (mode === 'hotel' && hotelData.value.length === 0) {
    loadHotelStats()
  } else if (mode === 'search') {
    searchData.value = [] // Clear previous search results
  }
}

const handleCityClick = (item) => {
  if (item.cityId) {
    loadRankingWithId(item.cityId)
    rankMode.value = 'scenic'
  }
}

const loadRankingWithId = async (id) => {
  try {
    const res = await getRegionalRank(id, sortType.value)
    rankingData.value = res
  } catch (error) {
    console.error(error)
  }
}

watch(() => props.cityId, (newVal) => {
  if (newVal) {
    loadRanking()
  }
})

onMounted(() => {
  loadRanking()
})
</script>

<template>
  <div class="ranking-container">
    <div class="ranking-header">
      <div class="header-top">
        <div class="tab-buttons">
          <span :class="{ active: rankMode === 'scenic' }" @click="switchMode('scenic')">景点排行</span>
          <span :class="{ active: rankMode === 'city' }" @click="switchMode('city')">城市统计</span>
          <span :class="{ active: rankMode === 'hotel' }" @click="switchMode('hotel')">酒店统计</span>
        </div>
        <div class="search-trigger" @click="toggleSearch" :class="{ active: isSearchActive }">
          🔍
        </div>
      </div>
      
      <div class="search-bar-container" v-if="isSearchActive">
         <input 
          v-model="searchKeyword" 
          @keyup.enter="handleSearch"
          placeholder="搜索景点..." 
          class="mini-search-input"
          ref="searchInputRef"
        />
        <span class="close-search" @click="toggleSearch">×</span>
      </div>
    </div>
    
    <!-- 景点排行控制栏 -->
    <div class="sub-header" v-if="rankMode === 'scenic' && !isSearchActive">
      <div class="sort-buttons">
        <span :class="{ active: sortType === 'popularity' }" @click="handleSortChange('popularity')">人气</span>
        <span :class="{ active: sortType === 'rating' }" @click="handleSortChange('rating')">评分</span>
        <span :class="{ active: sortType === 'price' }" @click="handleSortChange('price')">价格</span>
      </div>
    </div>

    <!-- 城市统计控制栏 -->
    <div class="sub-header" v-if="rankMode === 'city' && !isSearchActive">
      <div class="sort-buttons">
        <span :class="{ active: citySortType === 'sales' }" @click="handleCitySortChange('sales')">销量</span>
        <span :class="{ active: citySortType === 'score' }" @click="handleCitySortChange('score')">评分</span>
      </div>
    </div>

    <div class="ranking-list" v-loading="loading" element-loading-background="rgba(0, 0, 0, 0.5)">
      <!-- 搜索结果列表 -->
      <template v-if="isSearchActive">
        <div v-if="searchData.length === 0 && searchKeyword" class="empty-state">无结果</div>
        <div v-if="!searchKeyword" class="empty-state">请输入关键词搜索</div>
        <div v-for="(item, index) in searchData" :key="item.scenicId" class="ranking-item">
          <div class="rank-index">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="rank-name">{{ item.scenicName }}</div>
            <div class="rank-score">{{ item.category }} | {{ item.cityId === 31 ? '香港' : '其他' }}</div>
          </div>
          <div class="rank-value">
              <span>{{ item.avgScore }}分</span>
          </div>
        </div>
      </template>

      <!-- 景点列表 -->
      <template v-else-if="rankMode === 'scenic'">
        <div v-for="(item, index) in rankingData" :key="item.scenicId" class="ranking-item">
          <div class="rank-index" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="rank-name">{{ item.scenicName }}</div>
            <div class="rank-score">评分: {{ item.avgScore }}</div>
          </div>
          <div class="rank-value">
              <span v-if="sortType === 'price'">¥{{ item.avgPrice }}</span>
              <span v-else-if="sortType === 'rating'">{{ item.avgScore }}分</span>
              <span v-else>Hot</span>
          </div>
        </div>
      </template>

      <!-- 城市列表 -->
      <template v-if="rankMode === 'city'">
        <div 
          v-for="(item, index) in cityData" 
          :key="item.city" 
          class="ranking-item clickable"
          @click="handleCityClick(item)"
        >
          <div class="rank-index" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="rank-name">{{ item.city }}</div>
            <div class="rank-score">景点: {{ item.spotCount }}</div>
          </div>
          <div class="rank-value">
              <span v-if="citySortType === 'score'">{{ item.avgScore?.toFixed(1) }}分</span>
              <span v-else>{{ item.totalSales }}</span>
          </div>
        </div>
      </template>

      <!-- 酒店列表 -->
      <template v-if="rankMode === 'hotel'">
        <div v-for="(item, index) in hotelData" :key="item.region" class="ranking-item">
          <div class="rank-index" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="rank-name">{{ item.region }}</div>
            <div class="rank-score">酒店: {{ item.hotelCount }}</div>
          </div>
          <div class="rank-value">
              <span>¥{{ item.avgPrice?.toFixed(0) }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ranking-container {
  background: transparent;
  padding: 0;
  color: #fff;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ranking-header {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
  padding: 0 10px;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-buttons {
  display: flex;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 8px;
  overflow-x: auto;
}

.tab-buttons span {
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.tab-buttons span.active {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.search-trigger {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s;
}

.search-trigger:hover, .search-trigger.active {
  background: rgba(255, 255, 255, 0.15);
}

.search-bar-container {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 6px 10px;
  margin-top: 8px;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.mini-search-input {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 13px;
  width: 100%;
  outline: none;
}

.close-search {
  cursor: pointer;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 8px;
}

.close-search:hover {
  color: #fff;
}

.sub-header {
  display: flex;
  justify-content: flex-end;
  padding: 0 10px;
  margin-bottom: 10px;
}

.sort-buttons {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px;
  border-radius: 6px;
}

.sort-buttons span {
  cursor: pointer;
  padding: 2px 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.sort-buttons span:hover {
  color: rgba(255, 255, 255, 0.9);
}

.sort-buttons span.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-weight: 600;
}

.ranking-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.ranking-item:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateX(4px);
  border-color: rgba(255, 255, 255, 0.1);
}

.ranking-item.clickable {
  cursor: pointer;
}

.rank-index {
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  margin-right: 16px;
  font-weight: 600;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.rank-1 { background: linear-gradient(135deg, #ef4444, #f87171); color: white; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3); }
.rank-2 { background: linear-gradient(135deg, #f97316, #fb923c); color: white; box-shadow: 0 2px 4px rgba(249, 115, 22, 0.3); }
.rank-3 { background: linear-gradient(135deg, #eab308, #facc15); color: white; box-shadow: 0 2px 4px rgba(234, 179, 8, 0.3); }

.rank-info {
  flex: 1;
}

.rank-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.rank-score {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.rank-value {
  font-size: 14px;
  font-weight: 600;
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
}

.empty-state {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 20px;
  font-size: 12px;
}
</style>
