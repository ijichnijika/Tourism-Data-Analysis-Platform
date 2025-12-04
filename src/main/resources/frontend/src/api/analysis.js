import request from '@/utils/request'

export function getHotSpots() {
    return request({
        url: '/analysis/hotspot/scenic',
        method: 'get'
    })
}

export function getWordCloud(scenicId) {
    return request({
        url: '/analysis/wordcloud',
        method: 'get',
        params: { scenicId }
    })
}

export function getRegionalRank(cityId, sortType) {
    return request({
        url: '/analysis/ranking',
        method: 'get',
        params: { cityId, sortType }
    })
}

export function getTrendAnalysis(scenicId) {
    return request({
        url: '/analysis/trend',
        method: 'get',
        params: { scenicId }
    })
}

export function getAspectAnalysis(scenicId) {
    return request({
        url: '/analysis/aspect',
        method: 'get',
        params: { scenicId }
    })
}

export function searchSpots(keyword) {
    return request({
        url: '/analysis/search',
        method: 'get',
        params: { keyword }
    })
}

export function getGlobalStats() {
    return request({
        url: '/analysis/stats/global',
        method: 'get'
    })
}

export function getHotelStats() {
    return request({
        url: '/analysis/stats/hotel',
        method: 'get'
    })
}

export function getTravelConsumption() {
    return request({
        url: '/analysis/stats/consumption',
        method: 'get'
    })
}

export function getGlobalWordCloud() {
    return request({
        url: '/analysis/stats/wordcloud',
        method: 'get'
    })
}
