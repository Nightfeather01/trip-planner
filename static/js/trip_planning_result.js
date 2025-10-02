let map;
let journeyMarkers = {};  // 存放行程標記
let filteredMarkers = [];  // 存放過濾後的推薦景點標記
let infoWindow;
let polylines = [];
const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFA500', '#800080'];
const typeColors = {
    'restaurant': '#FF0000',      // 紅色
    'tourist_attraction': '#00FF00',  // 綠色
    'museum': '#0000FF',          // 藍色
    'park': '#FFA500',           // 橘色
    'bar': '#800080',            // 紫色
    'cafe': '#795548',           // 棕色
    'shopping_mall': '#FF9800',    // 橙色
    'zoo': '#4CAF50'             // 深綠色
};

function initMap() {
    // 使用市政廳位置作為地圖中心
    const cityHallLocation = {
        lat: parseFloat(formData.city_hall_lat),
        lng: parseFloat(formData.city_hall_lng)
    };

    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 13,
        center: cityHallLocation,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: true
    });

    infoWindow = new google.maps.InfoWindow();

    // 初始化標記和路徑
    addJourneyMarkers();
    drawMultiDayJourneyRoutes();

    // 初始化事件監聽器
    initEventListeners();

    // 初始添加所有推薦景點標記
    filterPlaces('all');
}

function generateStarsHtml(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = (rating % 1) >= 0.5;
    let html = '';

    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            html += '<i class="bi bi-star-fill text-warning"></i>';
        } else if (i === fullStars && hasHalfStar) {
            html += '<i class="bi bi-star-half text-warning"></i>';
        } else {
            html += '<i class="bi bi-star text-warning"></i>';
        }
    }
    return html;
}

function createInfoWindowContent(place) {
    return `
        <div class="p-3">
            <h5 class="mb-2">${place.place_name}</h5>
            <div class="d-flex align-items-center mb-2">
                <div class="rating-display">
                    ${generateStarsHtml(place.rating)}
                    <small class="text-muted ms-2">(${place.user_rating_totals})</small>
                </div>
            </div>
            <div class="mb-2">
                價格等級: ${generatePriceIcons(place.price_level)}
            </div>
            <div class="mt-2">
                <strong>營業時間：</strong><br>
                ${formatOpeningHours(place.opening_hour)}
            </div>
        </div>
    `;
}

function addJourneyMarkers() {
    journeyData.forEach((place, index) => {
        const marker = new google.maps.Marker({
            position: { lat: place.lat, lng: place.lng },
            map: map,
            label: (index + 1).toString(),
            title: place.place_name
        });

        marker.addListener('click', () => {
            infoWindow.setContent(createInfoWindowContent(place));
            infoWindow.open(map, marker);
        });

        journeyMarkers[place.place_id] = marker;
    });
}

function filterPlaces(filterType) {
    // 清除現有的過濾標記
    clearFilteredMarkers();

    // 過濾地點
    let filteredPlaces;
    switch(filterType) {
        case 'high_rating':
            filteredPlaces = recommendedPlaces.filter(place => place.rating >= 4.5);
            break;
        case 'budget':
            filteredPlaces = recommendedPlaces.filter(place => place.price_level <= 1);
            break;
        case 'all':
            filteredPlaces = recommendedPlaces;
            break;
        default:
            filteredPlaces = recommendedPlaces.filter(place => place.types[0] === filterType);
            break;
    }

    // 更新側邊欄
    const recommendedList = document.getElementById('recommendedList');
    recommendedList.innerHTML = ''; // 清空現有內容

    // 添加過濾後的地點到側邊欄
    filteredPlaces.forEach(place => {
        // 創建地點卡片
        const placeCard = document.createElement('div');
        placeCard.className = 'recommended-place mb-3 border-start border-4 rounded shadow-sm';
        placeCard.setAttribute('data-place-id', place.place_id);
        placeCard.setAttribute('data-lat', place.lat);
        placeCard.setAttribute('data-lng', place.lng);
        placeCard.style.backgroundColor = `${typeColors[place.types[0]]}20`;
        placeCard.style.borderLeftColor = typeColors[place.types[0]];

        // 生成價格圖示
        const priceIcons = Array(5).fill(0).map((_, i) =>
            i < (place.price_level + 1) ?
                '<i class="bi bi-currency-dollar text-success"></i>' :
                '<i class="bi bi-currency-dollar text-muted"></i>'
        ).join('');

        // 設置卡片內容
        placeCard.innerHTML = `
            <div class="p-3">
                <h6 class="fw-bold mb-2">${place.place_name}</h6>
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="rating-display">
                            ${generateStarsHtml(place.rating)}
                            <small class="text-muted ms-2">(${place.user_rating_totals})</small>
                        </div>
                        <div class="price-level mt-1">
                            ${priceIcons}
                        </div>
                    </div>
                    <span class="badge" style="background-color: ${typeColors[place.types[0]]}">
                        ${place.types[0]}
                    </span>
                </div>
            </div>
        `;

        // 添加點擊事件
        placeCard.addEventListener('click', () => {
            const marker = filteredMarkers.find(m => m.title === place.place_name);
            if (marker) {
                map.panTo(marker.getPosition());
                map.setZoom(15);
                google.maps.event.trigger(marker, 'click');
            }
        });

        recommendedList.appendChild(placeCard);
    });

    // 為過濾後的地點添加標記
    filteredPlaces.forEach(place => {
        const placeType = place.types[0];
        const marker = new google.maps.Marker({
            position: { lat: place.lat, lng: place.lng },
            map: map,
            icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: typeColors[placeType] || '#000000',
                fillOpacity: 0.9,
                strokeWeight: 1,
                strokeColor: '#FFFFFF',
                scale: 8
            },
            title: place.place_name
        });

        marker.addListener('click', () => {
            infoWindow.setContent(createInfoWindowContent(place));
            infoWindow.open(map, marker);
        });

        filteredMarkers.push(marker);
    });

    // 調整地圖視圖以顯示所有標記
    if (filteredPlaces.length > 0) {
        const bounds = new google.maps.LatLngBounds();
        filteredPlaces.forEach(place => {
            bounds.extend(new google.maps.LatLng(place.lat, place.lng));
        });
        map.fitBounds(bounds);
    }
}

function drawMultiDayJourneyRoutes() {
    clearPolylines();

    let routeIndex = 0;
    let currentDate = null;

    // 遍歷所有景點
    journeyData.forEach((place, index) => {
        const placeDate = place.place_start_datetime.split(' ')[0];

        // 判斷是否為新的一天
        if (currentDate !== placeDate) {
            currentDate = placeDate;
        }

        // 如果有下一個地點，且是同一天的
        if (index < journeyData.length - 1) {
            const nextPlace = journeyData[index + 1];
            const nextDate = nextPlace.place_start_datetime.split(' ')[0];

            // 只在同一天的景點之間繪製路線
            if (placeDate === nextDate && routeData.routes_data[routeIndex]) {
                const pathData = routeData.routes_data[routeIndex].overview_polyline;
                if (pathData) {
                    // 解碼路線數據
                    const decodedPath = google.maps.geometry.encoding.decodePath(pathData);

                    // 計算當前是第幾天來決定顏色
                    const dayIndex = Object.keys(
                        journeyData.reduce((days, p) => {
                            days[p.place_start_datetime.split(' ')[0]] = true;
                            return days;
                        }, {})
                    ).indexOf(placeDate);

                    // 創建路線
                    const polyline = new google.maps.Polyline({
                        path: decodedPath,
                        strokeColor: colors[dayIndex % colors.length],
                        strokeOpacity: 0.5,
                        strokeWeight: 5,
                        map: map
                    });

                    polylines.push(polyline);
                }
                routeIndex++;
            }
        }
    });

    // 調整地圖視角以顯示所有標記
    const bounds = new google.maps.LatLngBounds();
    journeyData.forEach(place => {
        bounds.extend(new google.maps.LatLng(place.lat, place.lng));
    });
    map.fitBounds(bounds);
}

function drawDayRoutes(dayRoutes, dayIndex) {
    dayRoutes.forEach(routeInfo => {
        if (routeInfo.route && routeInfo.route.overview_polyline) {
            const decodedPath = google.maps.geometry.encoding.decodePath(routeInfo.route.overview_polyline);

            const polyline = new google.maps.Polyline({
                path: decodedPath,
                strokeColor: colors[dayIndex % colors.length],
                strokeOpacity: 1.0,
                strokeWeight: 2,
                map: map
            });

            polylines.push(polyline);
        }
    });
}

function generatePriceIcons(level) {
    level = parseInt(level) + 1;
    let html = '';
    for (let i = 0; i < 5; i++) {
        if (i < level) {
            html += '<i class="bi bi-currency-dollar text-success"></i>';
        } else {
            html += '<i class="bi bi-currency-dollar text-muted"></i>';
        }
    }
    return html;
}

function formatOpeningHours(openingHour) {
    if (!openingHour) return '無營業時間資訊';

    const weekMap = {
        '0': '週日', '1': '週一', '2': '週二', '3': '週三',
        '4': '週四', '5': '週五', '6': '週六'
    };

    return Object.entries(openingHour)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .map(([day, times]) => {
            const timeRanges = [];
            for (let i = 0; i < times.length; i += 2) {
                timeRanges.push(`${times[i].substring(0, 5)}~${times[i + 1].substring(0, 5)}`);
            }
            return `${weekMap[day]}: ${timeRanges.join(', ')}`;
        }).join('<br>');
}

function initEventListeners() {
    // 點擊行程景點
    document.querySelectorAll('.place-item').forEach(element => {
        element.addEventListener('click', () => {
            const placeId = element.getAttribute('data-place-id');
            const marker = journeyMarkers[placeId];
            if (marker) {
                map.panTo(marker.getPosition());
                map.setZoom(15);
                google.maps.event.trigger(marker, 'click');
            }
        });
    });

    // 點擊推薦景點
    document.querySelectorAll('.recommended-place').forEach(element => {
        element.addEventListener('click', () => {
            const placeId = element.getAttribute('data-place-id');
            const marker = filteredMarkers.find(m => m.title === element.querySelector('h6').textContent);
            if (marker) {
                map.panTo(marker.getPosition());
                map.setZoom(15);
                google.maps.event.trigger(marker, 'click');
            }
        });
    });

    // 過濾器變更事件
    document.getElementById('placeFilter').addEventListener('change', (e) => {
        filterPlaces(e.target.value);
    });
}

function clearFilteredMarkers() {
    filteredMarkers.forEach(marker => marker.setMap(null));
    filteredMarkers = [];
}

function clearPolylines() {
    polylines.forEach(polyline => polyline.setMap(null));
    polylines = [];
}

// 頁面載入完成後初始化地圖
window.addEventListener('load', () => {
    if (typeof google !== 'undefined') {
        initMap();
    } else {
        console.error('Google Maps API not loaded');
    }
});