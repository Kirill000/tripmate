// //let user_query_data = "{{ user_query_data }}";  // ← заранее объявляем переменную

// setInterval(loadMessages, 3000); // обновление сообщений каждую 3 секунды
// loadMessages();

// document.getElementById('message-form').addEventListener('submit', function(e) {
//     e.preventDefault();
//     SendMessage(0, this.id);
// });

// function SendMessage(notify, id){

//     let formData = new FormData();

//     formData.append("to_user_id", document.getElementById('to_user_id').value);
//     formData.append("marker_id", document.getElementById('marker_id').value);

//     if (!notify) {
//     msg = document.getElementById('message-text').value;
//     } else {
//     if (id == 'decline'){
//         msg = "К сожалению пользователь {{request.user}} отказал Вам в поездке :(";
//     } else {
//         msg = "Пользователь {{request.user}} подтвердил Ваш запрос на поездку!";
//     }
//     }
//     formData.append('notify_type', id);
//     formData.append("text", msg);

//     fetch("send_message", {
//     method: 'POST',
//     headers: {'X-CSRFToken': '{{ csrf_token }}'},
//     body: formData
//     }).then(() => {
//     document.getElementById('message-text').value = ''; // очищаем поле ввода
//     loadMessages(); // перезагружаем чат
//     });
// }