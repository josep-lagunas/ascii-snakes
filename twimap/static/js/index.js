let connection = null
let mapContainer = null
let cTravelers = null
let cTravelersContext = null
let cMap = null
let cMapContext = null
let blockSize = 0
let blockSize2 = 0
let blockHeight = 0

const connectWS = () => {
    connection = new WebSocket(`ws://${location.host}/ws`)
    mapContainer = document.getElementById("world-container")
    cMap = document.getElementById("c-world")
    cTravelers = document.getElementById("c-travelers")
    connection.addEventListener('open', () => {
        const config = {
            "rows": 55,
            "cols": 200,
            "apply_restrictions": true,
            "wall_type": 1,
            "delay_range": {min: 0.03, max: 0.08},
            "snakes_size": {min: 3, max: 10},
            "travellers_count": 11
        }
        const cell_size = 20
        const str_to_measure = Array.from({length: config.cols}, (value, index) => "a").join("")
        cMapContext = cMap.getContext("2d", {willReadFrequently: true})
        cMapContext.font = `${cell_size}px Courier new`
        const measuredText = cMapContext.measureText(str_to_measure)
        blockHeight = measuredText.actualBoundingBoxAscent + measuredText.actualBoundingBoxDescent
        cMap.width = measuredText.width
        blockSize = measuredText.width / config.cols
        blockSize2 = cMap.width / config.cols
        cMap.height = config.rows * cell_size + cell_size + 10
        const scale = 1
        cMap.width = cMap.width * scale
        cMap.height = cMap.height * scale
        cTravelers.width = cMap.width
        cTravelers.height = cMap.height
        mapContainer.style.width = `${cMap.width}px`
        cMapContext = cMap.getContext("2d", {willReadFrequently: true})
        cMapContext.font = `${cell_size}px Courier new`
        cMapContext.fillStyle = "#deceab"
        cMapContext.scale(scale, scale)
        cTravelersContext = cTravelers.getContext("2d", {willReadFrequently: true})
        cTravelersContext.font = `${cell_size}px Courier new`
        cTravelersContext.fillStyle = "#02fa59"
        cTravelersContext.letterSpacing = "0px"
        cTravelersContext.scale(scale, scale)
        connection.send(JSON.stringify(config))
    })
    let previousSnake = null
    connection.addEventListener('message', async (e) => {
            const json = JSON.parse(e.data)
            let data = ""
            const info = document.getElementById('info')
            if ("progress" in json) {
                const progress = `${json["progress"]}%`
                const row = json["row"]["index"]
                const content = json["row"]["content"]
                info.innerText = `Generating new map ${progress}`
                cMapContext.fillText(content, 0, row * 20)
            }
            if ("snake" in json) {

                const snake = json["snake"]
                const travelerType = json["travelerType"]
                const snakeDiscardedCoord = json["snakeDiscardedCoord"]

                if (snakeDiscardedCoord && snake && snake.length > 0) {
                    cTravelersContext.beginPath()
                    cTravelersContext.lineCap = "round"
                    cTravelersContext.strokeStyle = '#000000'
                    cTravelersContext.moveTo(snakeDiscardedCoord.col * blockSize2 + (blockSize2 / 2),
                        snakeDiscardedCoord.row * 20 + 15)
                    const snakeHead = snake[0]
                    cTravelersContext.lineTo(snakeHead.col * blockSize2 + (blockSize2 / 2), snakeHead.row * 20 + 15)
                    cTravelersContext.lineWidth = 25
                    cTravelersContext.stroke()
                }

                cTravelersContext.beginPath()
                cTravelersContext.lineCap = "round"
                cTravelersContext.strokeStyle = '#ffffff'
                cTravelersContext.lineWidth = 20
                for (let i = 1; i < snake.length; i++) {
                    cTravelersContext.beginPath()
                    // cTravelersContext.lineWidth = (snake[i - 1].col != snake[i].col && snake[i - 1].row != snake[i].row) ? 10 : 15
                    cTravelersContext.moveTo(snake[i - 1].col * blockSize2 + (blockSize2 / 2), snake[i - 1].row * 20 + 15)
                    const colorA = (travelerType === 'rec') ? '#3FCE7DFF': '#FF0026'
                    const colorB = (travelerType === 'rec') ? '#E6FF00FF': '#FFFFFF'
                    cTravelersContext.strokeStyle = i % 2 === 0 ? colorA : colorB
                    cTravelersContext.lineTo(snake[i].col * blockSize2 + (blockSize2 / 2), snake[i].row * 20 + 15)
                    cTravelersContext.stroke()
                }
                cTravelersContext.stroke()
                cTravelersContext.fillStyle = "#243ef6"
                if (snake.length > 0)
                    cTravelersContext.fillRect(snake[snake.length - 1].col * blockSize2 + (blockSize2 / 2) - 3, snake[snake.length - 1].row * 20 + 13, blockSize2 / 2, 5)

            }

            if ("type" in json) {
                if (json["type"] === "traveller_feedback")
                    console.log(json)
                if (json["type"] === "travelerInit") {
                    console.log(json)
                    const init_agents = json["travelersInitializedCount"]
                    const total_agents = json["totalTravelersCount"]
                    info.innerText = `Map generation:     ✅\nGenerating agents ${init_agents}/${total_agents}`
                    if (init_agents === total_agents) {
                        info.innerText = `Map generation:     ✅\nAgents generation: ✅`
                        setTimeout(() => {
                            info.style.display = "none"
                            mapContainer.style.filter = "blur(0px)"
                        }, 500)
                    }
                }
            }

        }
    )

    window.addEventListener('beforeunload', (e) => {
        connection.close()
    })
}


const send_message = (message) => {
    connection.send(message)
}