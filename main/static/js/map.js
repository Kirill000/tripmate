let map = L.map('map', {
    maxZoom: 16,
    worldCopyJump: false // Отключаем дублирование карты
});

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
map.setView([51.505, -0.09], 13);
});

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
attribution: '© OpenStreetMap contributors'
}).addTo(map);

let selectingStart = false;
let selectingEnd = false;
let startMarker = null;
let endMarker = null;
let tempPopup = null;

function toggleForm(show = true) {
let form = document.getElementById('markerForm');
form.style.display = show ? 'flex' : 'none';
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
fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`)
    .then(response => response.json())
    .then(data => {
    callback(data.display_name || `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    })
    .catch(() => {
    callback(`${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    });
}

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
    alert(`Место посадки выбрано: ${pickupPoint}`);
    waitingPickup = false;
    sendGoMessage(markerData);
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
        <button onclick="addMarkerFromPopup(${lat}, ${lng}, \`${address.replace(/`/g, '\\`')}\`)">Добавить здесь</button>
    </div>
    `;
    tempPopup = L.popup()
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
    <strong>Комментарий:</strong> ${data.comment}<br>
    <strong>Период:</strong> ${data.active_from} — ${data.active_to}<br>
    <hr>
    <strong>Контакты:</strong><br>
    Telegram: ${data.telegram}<br>
    WhatsApp: ${data.whatsapp}<br>
    VK: ${data.vk}<br>
    Телефон: ${data.phone_number}
`;
document.getElementById('detailsContent').innerHTML = content;
document.getElementById('markerDetailsCard').style.display = 'flex';
if (data.user != "{{request.user}}") {
    document.getElementById('markerDetailsCardConnect').href = `chat/${data.id}/${data.user_id}`;
    document.getElementById('go-button').addEventListener('click', function(e){
    e.preventDefault();
    go(data);
    });
} else {
    document.getElementById('markerDetailsCardConnect').remove();
    document.getElementById('go-button').remove();
}

// Удалить старый маршрут
if (routeLine) {
    map.removeLayer(routeLine);
}

// Нарисовать новый маршрут (линию между двумя точками)
const startCoords = [data.start_lat, data.start_lon];
const endCoords = [data.end_lat, data.end_lon];
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