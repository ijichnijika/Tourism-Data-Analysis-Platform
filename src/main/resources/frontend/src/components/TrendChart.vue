<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  xAxisData: {
    type: Array,
    default: () => []
  },
  seriesData: {
    type: Array,
    default: () => []
  },
  chartType: {
    type: String,
    default: 'line'
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
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: props.chartType === 'bar',
        data: props.xAxisData,
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        },
        axisLabel: {
          interval: 0,
          rotate: 45,
          color: '#ccc'
        }
      }
    ],
    yAxis: [
      {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#333'
          }
        },
        axisLabel: {
            color: '#ccc'
        }
      }
    ],
    series: [
      {
        name: '数值',
        type: props.chartType,
        stack: props.chartType === 'line' ? 'Total' : undefined,
        smooth: true,
        lineStyle: {
          width: 0
        },
        showSymbol: false,
        areaStyle: props.chartType === 'line' ? {
          opacity: 0.8,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgb(128, 255, 219)'
            },
            {
              offset: 1,
              color: 'rgb(1, 191, 236)'
            }
          ])
        } : undefined,
        itemStyle: props.chartType === 'bar' ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
            ]),
            borderRadius: [4, 4, 0, 0]
        } : undefined,
        emphasis: {
          focus: 'series'
        },
        data: props.seriesData
      }
    ],
    dataZoom: props.chartType === 'bar' ? [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 0,
        borderColor: 'transparent',
        backgroundColor: 'rgba(255,255,255,0.1)',
        fillerColor: 'rgba(56, 189, 248, 0.2)',
        handleStyle: {
            color: '#38bdf8'
        },
        textStyle: {
            color: '#ccc'
        }
      }
    ] : undefined,
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.chartType === 'bar' ? '15%' : '3%',
      containLabel: true
    }
  }
  chartInstance.setOption(option)
}

const resizeChart = () => {
  chartInstance && chartInstance.resize()
}

watch(() => [props.xAxisData, props.seriesData], () => {
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
