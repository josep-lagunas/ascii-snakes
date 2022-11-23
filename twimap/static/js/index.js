console.log('script loaded');
let connection = null;

const connectWS = () => {
    connection = new WebSocket('ws://localhost:8888/ws');

    connection.addEventListener('open', (e) => {
        config = { "rows": 55,
        "cols": 80, "apply_restrictions": true, "wall_type": 2,
        "delay": 0.0001, "travellers_count": 50}
        connection.send(JSON.stringify(config))
    });

    connection.addEventListener('message', (e) => {
        //console.log('Map received:\n' + e.data)
        json = JSON.parse(e.data)
        data = ""
        map = document.getElementById('map')
        info = document.getElementById('info')
        if ("progress" in json) {
            progress = `${json["progress"]}%`
            description = json["description"]
            info.innerText = `Building new map ${progress}`
            map.innerText = description
        }
        if ("map" in json) {
            info.innerText = ""
            data = `${json["map"]}`
            map.innerText = data
        }

        if ("type" in json && json["type"] == "traveller_feedback")
            console.log(json)


    });
}

 const send_message = (message) => {
        connection.send(message);
    }