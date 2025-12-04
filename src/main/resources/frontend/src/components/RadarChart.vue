<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value, 'dark')
  setOptions()
  window.addEventListener('resize', resizeChart)
}

const setOptions = () => {
  if (!chartInstance) return
  
  const indicators = props.data.map(item => ({
    name: item.aspectName,
    max: 10 // Assuming score is out of 10 or 5, adjust max accordingly. Let's assume 10 for now based on typical sentiment scores or normalize it.
  }))
  
  const values = props.data.map(item => item.score)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {},
    radar: {
      // shape: 'circle',
      indicator: indicators.length ? indicators : [
          { name: '食', max: 10 },
          { name: '住', max: 10 },
          { name: '行', max: 10 },
          { name: '游', max: 10 },
          { name: '购', max: 10 },
          { name: '娱', max: 10 }
      ],
      splitNumber: 5,
      axisName: {
        color: 'rgb(238, 197, 102)'
      },
      splitLine: {
        lineStyle: {
          color: [
            'rgba(238, 197, 102, 0.1)',
            'rgba(238, 197, 102, 0.2)',
            'rgba(238, 197, 102, 0.4)',
            'rgba(238, 197, 102, 0.6)',
            'rgba(238, 197, 102, 0.8)',
            'rgba(238, 197, 102, 1)'
          ].reverse()
        }
      },
      splitArea: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(238, 197, 102, 0.5)'
        }
      }
    },
    series: [
      {
        name: '情感评分',
        type: 'radar',
        lineStyle: {
            width: 1,
            opacity: 0.5
        },
        data: [
          {
            value: values,
            name: '情感评分',
            symbol: 'none',
            itemStyle: {
                color: '#F9713C'
            },
            areaStyle: {
                opacity: 0.1
            }
          }
        ]
      }
    ]
  }
  chartInstance.setOption(option)
}

const resizeChart = () => {
  chartInstance && chartInstance.resize()
}

watch(() => props.data, () => {
  setOptions()
}, { deep: true })

onMounted(() => {
  initChart()
})
</script>

<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
}
</style>
