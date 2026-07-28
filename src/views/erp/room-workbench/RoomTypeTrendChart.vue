<template>
  <div ref="chart" class="room-type-trend-chart" />
</template>

<script>
import echarts from 'echarts'

export default {
  name: 'RoomTypeTrendChart',
  props: {
    filters: {
      type: Object,
      default: () => ({})
    },
    rows: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      chart: null
    }
  },
  watch: {
    filters: {
      deep: true,
      handler() {
        this.renderChart()
      }
    },
    rows: {
      deep: true,
      handler() {
        this.renderChart()
      }
    }
  },
  mounted() {
    this.chart = echarts.init(this.$refs.chart)
    this.renderChart()
    window.addEventListener('resize', this.resizeChart)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.resizeChart)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    parseDate(value) {
      const parts = String(value || '').split('-').map(Number)
      if (parts.length !== 3 || parts.some(part => !Number.isFinite(part))) return new Date()
      return new Date(parts[0], parts[1] - 1, parts[2])
    },
    dateCategories() {
      const start = this.parseDate(this.filters.startDate)
      const end = this.parseDate(this.filters.endDate)
      const fallbackDays = Math.max(1, Number(this.filters.days || 28))
      const finalDate = end >= start ? end : new Date(start.getFullYear(), start.getMonth(), start.getDate() + fallbackDays)
      const result = []
      const duration = Math.round((finalDate.getTime() - start.getTime()) / 86400000)
      const dayCount = Math.min(367, Math.max(1, duration + 1))
      for (let index = 0; index < dayCount; index++) {
        const cursor = new Date(start)
        cursor.setDate(start.getDate() + index)
        result.push(`${String(cursor.getMonth() + 1).padStart(2, '0')}-${String(cursor.getDate()).padStart(2, '0')}`)
      }
      return result
    },
    roomSeries() {
      return this.rows.map(row => ({
        ...row,
        name: row.roomType,
        total: Number(row.total || 0)
      }))
    },
    remainingValues(room, dateValues) {
      const selected = this.filters.occupancyTypes || []
      return dateValues.map(day => {
        const bookings = (room.bookings || []).filter(item => {
          const start = String(item.startAt || '').slice(0, 10)
          const end = String(item.endAt || '').slice(0, 10)
          if (!(start <= day && end > day)) return false
          if (item.status === '已入住') return selected.includes('入住客户数')
          return selected.includes('订房客户数') || selected.includes('合同预住数')
        }).length
        const maintenance = selected.includes('维修（占用）房数')
          ? Number(room.maintenance || 0)
          : 0
        return Math.max(0, room.total - bookings - maintenance)
      })
    },
    renderChart() {
      if (!this.chart) return
      const categories = this.dateCategories()
      const start = this.parseDate(this.filters.startDate)
      const dateValues = categories.map((_, index) => {
        const cursor = new Date(start)
        cursor.setDate(start.getDate() + index)
        return `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}-${String(cursor.getDate()).padStart(2, '0')}`
      })
      const rooms = this.roomSeries()
      const roomData = rooms.map(room => ({
        ...room,
        values: this.remainingValues(room, dateValues)
      }))
      const totalValues = categories.map((_, dayIndex) => {
        return roomData.reduce((sum, room) => sum + room.values[dayIndex], 0)
      })
      const totalRoomCount = rooms.reduce((sum, room) => sum + room.total, 0)
      const names = [...rooms.map(room => room.name), '总剩余数']
      const series = roomData.map(room => ({
        name: room.name,
        type: 'line',
        symbol: 'emptyCircle',
        symbolSize: 5,
        itemStyle: {
          normal: {
            label: { show: true }
          }
        },
        data: room.values
      }))
      series.push({
        name: '总剩余数',
        type: 'line',
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          normal: {
            label: { show: true },
            lineStyle: { width: 5 }
          }
        },
        data: totalValues
      })
      this.chart.clear()
      this.chart.setOption({
        title: {
          text: '房型可用趋势图',
          subtext: '每日房型剩余数'
        },
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            const rows = params.map(item => {
              const ratio = totalRoomCount ? (Number(item.value) / totalRoomCount * 100).toFixed(2) : '0.00'
              return `${item.marker}${item.seriesName}:${item.value}  余房占比${ratio}%`
            })
            return `${params[0] ? params[0].axisValue : ''}<br>${rows.join('<br>')}`
          }
        },
        legend: {
          data: names
        },
        grid: {
          left: '3%',
          right: '2%',
          bottom: '3%',
          containLabel: true
        },
        toolbox: {
          feature: {
            saveAsImage: {
              name: '房型可用趋势图'
            }
          }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: categories
        },
        yAxis: {
          type: 'value',
          minInterval: 1
        },
        series
      }, true)
    },
    resizeChart() {
      if (this.chart) this.chart.resize()
    }
  }
}
</script>

<style scoped>
.room-type-trend-chart {
  width: 100%;
  height: 560px;
}
</style>
