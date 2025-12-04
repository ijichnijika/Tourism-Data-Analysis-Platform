<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

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

  const data = props.data.map(item => ({
      name: item.word,
      value: item.frequency
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {},
    series: [
      {
        type: 'wordCloud',
        gridSize: 2,
        sizeRange: [12, 50],
        rotationRange: [-90, 90],
        shape: 'pentagon',
        width: '100%',
        height: '100%',
        drawOutOfBound: false,
        textStyle: {
          color: function () {
            return 'rgb(' + [
              Math.round(Math.random() * 160),
              Math.round(Math.random() * 160),
              Math.round(Math.random() * 160)
            ].join(',') + ')'
          }
        },
        emphasis: {
          textStyle: {
            shadowBlur: 10,
            shadowColor: '#333'
          }
        },
        data: data
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
