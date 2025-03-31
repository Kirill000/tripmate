let map = L.map('map', {
    maxZoom: 16,
    minZoom: 3,
    worldCopyJump: false // Отключаем дублирование карты
});

var blueIcon = L.icon({
    iconUrl: marker_img,
    iconSize: [25, 38],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
});

var orangeIcon = L.icon({
    iconUrl: marker_x,
    iconSize: [25, 38],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
});

function updateProgress(value) {
    let progressBar = document.getElementById("progressBar");
    progressBar.style.width = value + "%";
    if (value == 100){
        setTimeout(function(){progressBar.style.width = 0;}, 1000);
    }
  }  

var southWest = L.latLng(-180, -180),
northEast = L.latLng(180, 180);
var bounds = L.latLngBounds(southWest, northEast);

map.setMaxBounds(bounds);
map.on('drag', function() {
	map.panInsideBounds(bounds, { animate: false });
});

navigator.geolocation.getCurrentPosition(function(pos) {
let { latitude, longitude } = pos.coords;
map.setView([latitude, longitude], 13);
}, function() {
map.setView([55.75, 37.62], 13);
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '© OpenStreetMap contributors'
}).addTo(map);

let selectingStart = false;
let selectingEnd = false;
let startMarker = null;
let endMarker = null;
let tempPopup = null;
let popupRevealed = false;
let tempPopupMarker = null;
let oldMarkers = [];

function toggleForm(show = true) {
let form = document.getElementById('markerForm');
form.style.display = show ? 'flex' : 'none';
}

function hideMakerForm() {
    let markerForm = document.getElementById('markerForm');
    markerForm.style.display = 'none';
    map.removeLayer(tempPopupMarker);
}

function toggleOtherTransport() {
let type = document.getElementById("transport_type").value;
document.getElementById("other_transport_group").style.display = (type === "other") ? "block" : "none";
}

function setStartFromMap() {
selectingStart = true;
selectingEnd = false;
document.getElementById('markerForm').style.display = 'none';
alert("Выберите стартовую точку на карте");
}

function setEndFromMap() {
selectingStart = false;
selectingEnd = true;
document.getElementById('markerForm').style.display = 'none';
alert("Выберите конечную точку на карте");
}

function reverseGeocode(lat, lng, callback) {
updateProgress(50);
fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`)
    .then(response => response.json())
    .then(data => {
    updateProgress(100);
    callback(data.display_name || `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    })
    .catch(() => {
    callback(`${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    });
}

function loadMarkers(){
    let center = map.getCenter();
    let bounds = map.getBounds();
    let distance = center.distanceTo(bounds.getNorthEast()); // Радиус для поиска

    const now = new Date();
    // Получаем текущую дату и время
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0'); // Месяц начинается с 0
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    // Форматируем строку в нужный формат (yyyy-mm-ddThh:mm)
    const currentTime = `${year}-${month}-${day}T${hours}:${minutes}`;

    if (~isDetailsOpen) {
    fetch(`/markers/?lat=${center.lat}&lon=${center.lng}&radius=${distance}&ctime=${currentTime}`)
        .then(response => response.json())
        .then(data => {

            oldMarkers.forEach(mk => map.removeLayer(mk));

            //delete from webpage

            marker_imgs = document.getElementsByClassName('leaflet-marker-icon leaflet-zoom-animated leaflet-interactive');
            marker_imgs_box = document.getElementsByClassName('leaflet-marker-shadow leaflet-zoom-animated');

            Array.prototype.forEach.call(marker_imgs, (mk) => {
                mk.remove();
            })
            let i = 0;
            Array.prototype.forEach.call(marker_imgs_box, (mk) => {
                if ((i >= marker_imgs.length)){
                    mk.remove();
                }
                i++;
            })

            oldMarkers = [];
            
            data.markers.forEach(marker => {
                markerData = {
                id:  marker.id,
                title: marker.title,
                user_id: marker.user,
                start_point: marker.start_point,
                end_point: marker.end_point,
                start_lat: marker.start_lat,
                start_lon: marker.start_lon,
                end_lat: marker.end_lat,
                end_lon: marker.end_lon,
                transport_type: marker.transport_type,
                people_count: marker.people_count,
                price: marker.price,
                comment: marker.comment,
                active_from: marker.active_from,
                active_to: marker.active_to,
                telegram: marker.telegram,
                whatsapp: marker.whatsapp,
                vk: marker.vk,
                phone_number: marker.phone_number
                };
                
                popupHtml = `
                <div>
                    <strong>Маршрут:</strong> ${markerData.start_point} → ${markerData.end_point}<br>
                    <strong>Транспорт:</strong> ${markerData.transport_type}<br>
                    <strong>Цена:</strong> ${markerData.price} ₽<br>
                    <button class="show-details-button" onclick='showDetails(${JSON.stringify(markerData)})'>Подробнее</button>
                </div>
                `;

                let icon = null;

                if (marker.transport_type == "Ищу транспорт"){
                    icon = orangeIcon;
                }else {
                    icon = blueIcon;
                }
                
                L.marker([marker.start_lat, marker.start_lon], { icon: icon }).addTo(map)
                .bindPopup(popupHtml);
                oldMarkers.push(marker);
            });
        })
    }
        //.catch(error => console.error('Ошибка загрузки маркеров:', error));
}

map.on('moveend', function(e) {
    loadMarkers();
});

map.on('click', function(e) {
if (isDetailsOpen) return;  // Блокируем добавление маркера при открытом окне
let lat = e.latlng.lat;
let lng = e.latlng.lng;

if (waitingPickup) {
    console.log('waiting pickup')
    if (pickupMarker) map.removeLayer(pickupMarker);
    pickupLat = e.latlng.lat;
    pickupLng = e.latlng.lng;
    pickupMarker = L.marker([pickupLat, pickupLng], { draggable: true }).addTo(map);
    reverseGeocode(pickupLat, pickupLng, function(address) {
    pickupPoint = address;
    
    // Показываем модальное окно подтверждения
    const confirmed = confirm(`Вы выбрали точку: ${address}\n\nКоординаты: ${pickupLat.toFixed(6)}, ${pickupLng.toFixed(6)}\n\nПодтвердить выбор?`);
            
     if (confirmed) {
        waitingPickup = false;
        sendGoMessage(markerData);
     }else {
        // Если пользователь не подтвердил, оставляем режим выбора
        map.removeLayer(pickupMarker);
        pickupMarker = null;
        alert("Выберите точку снова");
     }
    });
    return;
}    

// Если в режиме выбора стартовой/конечной точки — используем старую логику
if (selectingStart) {
    if (startMarker) map.removeLayer(startMarker);
    startMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
    reverseGeocode(lat, lng, function(address) {
    document.getElementById('start_point').value = address;
    document.getElementById('start_lat').value = lat;
    document.getElementById('start_lon').value = lng;
    });
    selectingStart = false;
    document.getElementById('markerForm').style.display = 'flex';
    return;
}

if (selectingEnd) {
    if (endMarker) map.removeLayer(endMarker);
    endMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
    reverseGeocode(lat, lng, function(address) {
    document.getElementById('end_point').value = address;
    document.getElementById('end_lat').value = lat;
    document.getElementById('end_lon').value = lng;
    });
    selectingEnd = false;
    document.getElementById('markerForm').style.display = 'flex';
    return;
}

// Иначе — просто клик по карте: показать popup "Добавить здесь"
if (tempPopup) {
    map.closePopup(tempPopup)
    toggleForm(show=false)
};

reverseGeocode(lat, lng, function(address) {
    let popupContent = `
    <div>
        <strong>${address}</strong><br/>
        <button class="add-marker-button" onclick="addMarkerFromPopup(${lat}, ${lng}, \`${address.replace(/`/g, '\\`')}\`)">Добавить здесь</button>
    </div>
    `;
    tempPopupMarker = L.popup();
    tempPopup = tempPopupMarker
    .setLatLng([lat, lng])
    .setContent(popupContent)
    .openOn(map);
});
});

// Функция при нажатии кнопки "Добавить здесь"
function addMarkerFromPopup(lat, lng, address) {
if (startMarker) map.removeLayer(startMarker);
startMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
document.getElementById('start_point').value = address;
document.getElementById('start_lat').value = lat;
document.getElementById('start_lon').value = lng;
setDefaultTime();
toggleForm(true);

if (tempPopup) map.closePopup(tempPopup);
}

let isDetailsOpen = false;
let pickupPoint = null;
let pickupLat = null;
let pickupLng = null;
let pickupMarker = null;
let waitingPickup = false;

let currentMarkerId = null;
let routeLine = null;

// Функция для установки текущего времени в формате datetime-local
function setDefaultTime() {
    const now = new Date();
    // Получаем текущую дату и время
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0'); // Месяц начинается с 0
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');

    // Форматируем строку в нужный формат (yyyy-mm-ddThh:mm)
    const currentTime = `${year}-${month}-${day}T${hours}:${minutes}`;
    
    // Устанавливаем текущее время в input
    document.getElementById('active_from').value = currentTime;
}

function showDetails(data) {


let content = `
    <h3 style="margin-top: 0;">Детали маршрута</h3>
    <strong>Старт:</strong> ${data.start_point}<br>
    <strong>Финиш:</strong> ${data.end_point}<br>
    <strong>Транспорт:</strong> ${data.transport_type}<br>
    <strong>Кол-во людей:</strong> ${data.people_count}<br>
    <strong>Цена:</strong> ${data.price} ₽<br>
    ${data.comment ? `<strong>Комментарий:</strong> ${data.comment}<br>` : ""}
    <strong>Время начала поездки:</strong> ${data.active_to}<br>
    <hr>
    <strong>Контакты:</strong><br>
    ${data.telegram ? `Telegram: ${data.telegram}<br>` : ""}
    ${data.whatsapp ? `WhatsApp: ${data.whatsapp}<br>` : ""}
    ${data.vk ? `VK: ${data.vk}<br>` : ""}
    ${data.phone_number ? `Телефон: ${data.phone_number}` : ""}
`;
document.getElementById('detailsContent').innerHTML = content;
document.getElementById('markerDetailsCard').style.display = 'flex';
console.log('her')
if (data.user_id != user_id) {
    try{
        document.getElementById('edit-button').remove();
    } catch {
        ;
    }
    document.getElementById('markerDetailsCard').innerHTML += `<button id="go-button">Поехали</button><a href="" class="chat-button" id="markerDetailsCardConnect">Связаться</a>`;
    document.getElementById('markerDetailsCardConnect').href = `chat/${data.id}/${data.user_id}`;
    document.getElementById('go-button').addEventListener('click', function(e){
    e.preventDefault();
    go(data);
    });
} else {
    try {
        document.getElementById('markerDetailsCardConnect').remove();
        document.getElementById('go-button').remove();
    } catch {
        ;
    }
    document.getElementById('markerDetailsCard').innerHTML += `<a href="/profile/${user_id}" class="edit-button" id="edit-button">Редактировать</a>`
    
}

// Нарисовать новый маршрут (линию между двумя точками)
const startCoords = [data.start_lat, data.start_lon];
const endCoords = [data.end_lat, data.end_lon];

// Удалить старый маршрут
if (routeLine) {
    map.removeLayer(routeLine);
}

routeLine = L.polyline([startCoords, endCoords], {
    color: '#007bff',
    weight: 5,
    opacity: 0.8,
    dashArray: '8,6'
}).addTo(map);

// Подогнать карту под маршрут
map.fitBounds(routeLine.getBounds(), { padding: [40, 40] });

currentMarkerId = data.id;
isDetailsOpen = true;
}

function hideDetails() {
const box = document.getElementById('details-box');
if (box) box.remove();
if (routeLine) map.removeLayer(routeLine);
isDetailsOpen = false;
document.getElementById('markerDetailsCard').style.display = 'none';
isDetailsOpen = false;
}

function go(data) {
// Показываем плашку выбора точки
document.getElementById('pickupPrompt').style.display = 'block';

document.getElementsByClassName('leaflet-popup-content')[0].style.display = 'none';
// Скрываем детали
hideDetails()

// По кнопке "Подтвердить стартовую точку"
document.getElementById('confirmDefaultPickup').onclick = function() {
    pickupPoint = data.start_point;
    pickupLat = data.start_lat || null;
    pickupLng = data.start_lon || null;
    sendGoMessage(data);
    document.getElementById('pickupPrompt').style.display = 'none';
};

// По кнопке "Выбрать на карте"
document.getElementById('selectPickupFromMap').onclick = function() {
    waitingPickup = true;
    alert("Кликните по карте, чтобы указать точку, где Вас забрать");
    hideDetails()
    document.getElementById('pickupPrompt').style.display = 'none';
};
}

map.addEventListener('load', (event) => {
    loadMarkers()
})

function sendGoMessage(data) {
console.log("Отправка сообщения пользователю...");
console.log("Pickup point:", pickupPoint);
console.log("Pickup coordinates:", pickupLat, pickupLng);

let formData = new FormData();
formData.append("text", "");
formData.append("to_user_id", data.user_id);
formData.append("pickup_point", pickupPoint)
formData.append("pickup_lat", pickupLat)
formData.append("pickup_lon", pickupLng)
formData.append("marker_id", data.id);
formData.append("notify_type", "user_query");
formData.append("from_user", "{{request.user.id}}");

fetch('send-message', {
    method: 'POST',
    headers: {'X-CSRFToken': csrf_token},
    body: formData
}).then(() => {
    alert("Сообщение успешно отправлено!");
    //document.getElementById('go-button').style = "background-color: yellow";
    //document.getElementById('go-button').innerHTML = "Ожидание ответа";
});
}