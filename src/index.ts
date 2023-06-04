import 'dotenv/config'

import express from 'express'
import { createServer } from 'http'
import bodyParser from 'body-parser'
import { WebSocket } from 'ws'
import { uuid } from 'uuidv4'
import cors from 'cors'
import { HTTP_PORT } from 'constants/env'
import { verify } from 'verification'

const connections: WebSocket[] = [];
const app = express()
app.options('*', cors())
app.use(cors())

app.use(bodyParser.urlencoded({ extended: false }))
app.use(bodyParser.json())


interface Task {
  request_id: string;
  prompt: string;
  model: string;
  size: number;
}

// Create http server
const server = createServer(app)

const wss = new WebSocket.Server({ server })

wss.on('connection', (ws: WebSocket) => {
  console.log('Node connected')
  connections.push(ws)
  ws.on('close', () => {
    const index = connections.indexOf(ws)
    if (index !== -1) {
      connections.splice(index, 1)
    }
  })

  ws.on('message', async (message: string) => {
    const data = JSON.parse(message)
    const { type, request_id } = data
    if (type === 'status') {
      const { status } = data
      if (status === 'ready') {
        // can process request_id
      }
      if (status === 'busy') {
        // cannot process request_id
      }
    }
    if (type === 'result') {
      const { result_url } = data
      // result for { request_id };
    }
    if (type === 'error') {
      // failure for { request_id }
    }
    if (type === 'greetings') {
      console.log(data.node_id)
    }
  })
})

app.post('/v1/client/hello', async (req, res) => {
  return res.json({ ok: true, url: 'ws://orca-app-feq22.ondigitalocean.app/' })
})

app.post('/v1/images/generation/', async (req, res) => {
  const { prompt, model, image_url, size, token } = req.body

  if (!verify(token)) {
    return res.json({ ok: false, error: 'operation is not permitted' })
  }

  if (!prompt) {
    return res.json({ ok: false, error: 'prompt cannot be null or undefined' })
  }
  if (prompt.length === 0) {
    return res.json({ ok: false, error: 'prompt length cannot be 0' })
  }

  const request_id = uuid()
  if (connections.length === 0) {
    return res.json({ ok: false, message: 'nodes are not available' })
  }
  const randomConnection =
    connections[Math.floor(Math.random() * connections.length)]
  const task: Task = {
    request_id,
    prompt,
    model,
    size
  }
  randomConnection.send(JSON.stringify(task))
  res.json({ ok: true, task_id: task.request_id })
})

// Start the server
server.listen(HTTP_PORT, () => {
  console.log(`HTTP ans WS started on port ${HTTP_PORT}`)
});

// Handle errors that occur during the startup process
server.on('error', error => {
  console.error(error)
})
