<script setup>
import { ref, onMounted } from 'vue'
import { getHotSpots, getTrendAnalysis, getAspectAnalysis, getWordCloud, getGlobalStats, getTravelConsumption, getGlobalWordCloud } from '@/api/analysis'
import TrendChart from '@/components/TrendChart.vue'
import RadarChart from '@/components/RadarChart.vue'
import WordCloud from '@/components/WordCloud.vue'
import RankingTable from '@/components/RankingTable.vue'
import SearchBar from '@/components/SearchBar.vue'

import { ElMessage } from 'element-plus'

const hotSpots = ref([])
const consumptionData = ref({ xAxis: [], series: [] })
const aspectData = ref([])
const wordCloudData = ref([])
const globalWordCloudData = ref([])
const globalStats = ref(null)
const currentScenicId = ref(null)
const currentScenicName = ref('请选择景点')
const wordCloudMode = ref('scenic') // scenic, global

// Loading states
const loading = ref({
  global: false,
  hotspots: false,
  consumption: false,
  charts: false
})

const loadGlobalStats = async () => {
  loading.value.global = true
  try {
    const res = await getGlobalStats()
    if (res && res.length > 0) {
      globalStats.value = res[0]
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('获取全球统计数据失败')
  } finally {
    loading.value.global = false
  }
}

const loadConsumption = async () => {
  loading.value.consumption = true
  try {
    const res = await getTravelConsumption()
    if (res) {
        consumptionData.value = {
            xAxis: res.map(item => item.destination),
            series: res.map(item => item.avgCost)
        }
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('获取消费数据失败')
  } finally {
    loading.value.consumption = false
  }
}

const loadGlobalWordCloud = async () => {
  try {
    const res = await getGlobalWordCloud()
    globalWordCloudData.value = res
  } catch (error) {
    console.error(error)
  }
}

const loadHotSpots = async () => {
  loading.value.hotspots = true
  try {
    const res = await getHotSpots()
    hotSpots.value = res
    if (hotSpots.value.length > 0) {
      handleSelect(hotSpots.value[0])
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('获取热门景点失败')
  } finally {
    loading.value.hotspots = false
  }
}

const handleSelect = async (row) => {
  currentScenicId.value = row.scenicId
  currentScenicName.value = row.scenicName
  loadCharts(row.scenicId)
}

const loadCharts = async (id) => {
  loading.value.charts = true
  try {
    const aspectRes = await getAspectAnalysis(id)
    aspectData.value = aspectRes

    const wordCloudRes = await getWordCloud(id)
    wordCloudData.value = wordCloudRes
  } catch (error) {
    console.error(error)
    ElMessage.error('获取图表数据失败')
  } finally {
    loading.value.charts = false
  }
}

const switchWordCloudMode = (mode) => {
    wordCloudMode.value = mode
}

onMounted(() => {
  loadGlobalStats()
  loadHotSpots()
  loadConsumption()
  loadGlobalWordCloud()
})
</script>

<template>
  <div class="dashboard-container">
    <div class="header">
      <div class="title">分布式旅游大数据分析平台</div>
      <div class="search-wrapper">
        <SearchBar @select="handleSelect" />
      </div>
    </div>

    <!-- 全球统计数据卡片 -->
    <div class="stats-cards" v-if="globalStats">
      <div class="stat-card">
        <div class="stat-icon">🌍</div>
        <div class="stat-info">
          <div class="stat-label">覆盖国家</div>
          <div class="stat-value">{{ globalStats.country || '中国' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔥</div>
        <div class="stat-info">
          <div class="stat-label">热门城市</div>
          <div class="stat-value">{{ globalStats.topCity || '香港' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-info">
          <div class="stat-label">总游客量</div>
          <div class="stat-value">{{ globalStats.totalVisitors?.toLocaleString() || '-' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-info">
          <div class="stat-label">平均热度</div>
          <div class="stat-value">{{ globalStats.avgCityHeat?.toFixed(1) || '-' }}</div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-panel">
        <div class="panel-box ranking-box">
          <RankingTable />
        </div>
      </div>
      
      <div class="center-panel">
        <div class="panel-box trend-box" v-loading="loading.consumption" element-loading-background="rgba(0, 0, 0, 0.5)">
          <div class="panel-header">
             <div class="panel-title">热门旅游地人均消费</div>
          </div>
          <div class="chart-content">
             <TrendChart :xAxisData="consumptionData.xAxis" :seriesData="consumptionData.series" chartType="bar" />
          </div>
        </div>
        <div class="panel-box bottom-charts">
            <div class="sub-panel" v-loading="loading.charts" element-loading-background="rgba(0, 0, 0, 0.5)">
                <div class="panel-title">情感分析</div>
                <RadarChart :data="aspectData" />
            </div>
            <div class="sub-panel" v-loading="loading.charts" element-loading-background="rgba(0, 0, 0, 0.5)">
                <div class="panel-header">
                    <div class="panel-title">词云分析</div>
                    <div class="toggle-buttons sm">
                        <span :class="{ active: wordCloudMode === 'scenic' }" @click="switchWordCloudMode('scenic')">景点</span>
                        <span :class="{ active: wordCloudMode === 'global' }" @click="switchWordCloudMode('global')">全网</span>
                    </div>
                </div>
                <WordCloud :data="wordCloudMode === 'scenic' ? wordCloudData : globalWordCloudData" />
            </div>
        </div>
      </div>

      <div class="right-panel">
        <div class="panel-box hotspot-box" v-loading="loading.hotspots" element-loading-background="rgba(0, 0, 0, 0.5)">
          <div class="panel-title">热门景点</div>
          <div class="hotspot-list">
             <div 
                v-for="(item, index) in hotSpots" 
                :key="item.scenicId" 
                class="hotspot-item"
                :class="{ active: currentScenicId === item.scenicId }"
                @click="handleSelect(item)"
             >
                <span class="index" :class="'idx-' + (index + 1)">{{ index + 1 }}</span>
                <span class="name">{{ item.scenicName }}</span>
                <span class="score">{{ item.avgScore }}分</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  width: 100vw;
  height: 100vh;
  background-color: #0f172a;
  background-image: 
    radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.1) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(236, 72, 153, 0.1) 0px, transparent 50%),
    radial-gradient(at 0% 100%, rgba(34, 197, 94, 0.1) 0px, transparent 50%);
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

.header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  z-index: 10;
}

.stats-cards {
  display: flex;
  gap: 24px;
  padding: 0 32px;
  margin-top: 24px;
}

.stat-card {
  flex: 1;
  background: rgba(30, 41, 59, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(30, 41, 59, 0.6);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.1);
}

.stat-icon {
  font-size: 32px;
  background: rgba(255, 255, 255, 0.05);
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  font-family: 'Outfit', sans-serif;
}

.title {
  font-size: 26px;
  font-weight: 800;
  background: linear-gradient(to right, #38bdf8, #818cf8, #c084fc);
  -webkit-background-clip: text;
  color: transparent;
  letter-spacing: 0.5px;
  text-shadow: 0 0 30px rgba(139, 92, 246, 0.3);
}

.main-content {
  flex: 1;
  display: flex;
  padding: 24px 32px;
  gap: 24px;
  overflow: hidden;
}

.left-panel, .right-panel {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.panel-box {
  background: rgba(30, 41, 59, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-box:hover {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  transform: translateY(-2px);
}

.ranking-box {
  height: 100%;
  padding: 0;
  overflow: hidden;
}

.trend-box {
  flex: 2;
}

.bottom-char.trend-box {
  flex: 1;
  min-height: 400px;
  margin-bottom: 20px;
}

.chart-content {
  flex: 1;
  min-height: 0;
  position: relative;
  height: 320px;
  width: 100%;
}

.bottom-charts {
  flex: 1;
  min-height: 420px;
  flex-direction: row;
  gap: 24px;
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
  backdrop-filter: none;
  display: flex;
  gap: 20px;
  height: 450px;
}

.sub-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sub-panel > div:last-child {
  flex: 1;
  min-height: 0;
}

.sub-panel:hover {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.hotspot-box {
  height: 100%;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.toggle-buttons {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px;
  border-radius: 8px;
  gap: 4px;
}

.toggle-buttons span {
  cursor: pointer;
  padding: 4px 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.toggle-buttons span:hover {
  color: rgba(255, 255, 255, 0.9);
}

.toggle-buttons span.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-weight: 600;
}

.toggle-buttons.sm span {
    padding: 2px 8px;
    font-size: 11px;
}

.panel-title::before {
  content: '';
  display: block;
  width: 4px;
  height: 20px;
  background: linear-gradient(to bottom, #38bdf8, #818cf8);
  margin-right: 12px;
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

.chart-content {
  flex: 1;
  min-height: 0;
  position: relative;
}

.hotspot-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.hotspot-item {
  display: flex;
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hotspot-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(4px);
}

.hotspot-item.active {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.3);
}

.index {
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  margin-right: 16px;
  color: rgba(255, 255, 255, 0.5);
}

.idx-1 { background: linear-gradient(135deg, #ef4444, #f87171); color: white; box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.3); }
.idx-2 { background: linear-gradient(135deg, #f97316, #fb923c); color: white; box-shadow: 0 4px 6px -1px rgba(249, 115, 22, 0.3); }
.idx-3 { background: linear-gradient(135deg, #eab308, #facc15); color: white; box-shadow: 0 4px 6px -1px rgba(234, 179, 8, 0.3); }

.name {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: #f8fafc;
}

.score {
  color: #34d399;
  font-weight: 600;
  font-size: 14px;
  background: rgba(52, 211, 153, 0.15);
  padding: 4px 10px;
  border-radius: 6px;
}
</style>
