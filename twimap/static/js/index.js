console.log('script loaded');
let connection = null;

const connectWS = () => {
    connection = new WebSocket('ws://localhost:8888/ws');

    connection.addEventListener('open', (e) => {
        connection.send('{ "rows": 30, "cols": 70, "apply_restrictions": true, "wall_type": 2}')
    });

    connection.addEventListener('message', (e) => {
        console.log('Map received:\n' + e.data)
        map = document.getElementById('map')
        map.innerText = e.data
    });
}

 const send_message = (message) => {
        connection.send(message);
    }