import express from 'express'
import { WebSocketServer } from 'ws'
import { uuid } from 'uuidv4'
const connections = []
const app = express()
const wss = new WebSocketServer({ port: 8080 })

wss.on('connection', ws => {
  console.log('Node connected')
  connections.push(ws)
  ws.on('close', () => {
    const index = connections.indexOf(ws)
    if (index !== -1) {
      connections.splice(index, 1)
    }
  })

  ws.on('message', async message => {
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

// this is for demo purposes;
// app.get('/v1/images/demo', async (req, res) => {
//   // const { prompt, model, image_url, size } = req.body;

//   const prompt = 'Some random text';
//   const model = 'SD-1.5';
//   const size = '512X512';
//   if (prompt === undefined || prompt === null) {
//     return res.json({ ok: false, error: 'prompt cannot be null or undefined' });
//   }
//   if (prompt.length === 0) {
//     return res.json({ ok: false, error: 'prompt length cannot be 0' });
//   }

//   const request_id = uuid();
//   const randomConnection = connections[Math.floor(Math.random() * connections.length)];
//   const task = {
//     request_id: request_id,
//     prompt,
//     model,
//     size,
//   };

//   randomConnection.send(JSON.stringify(task));

//   res.send({ ok: true });
// });

// app.post('/v1/images/edits/', async (req, res) => {})

app.post('/v1/ping', async (req, res) => {
  return res.json({ ok: true, message: 'Service is online' })
})

app.post('/v1/images/generation/', async (req, res) => {
  const { prompt, model, image_url, size } = req.body

  if (prompt === undefined || prompt === null) {
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
  const task = {
    request_id: request_id,
    prompt,
    model,
    size
  }
  randomConnection.send(JSON.stringify(task))
  res.json({ ok: true, task_id: request_id })
})

// Start the server
const server = app.listen(4040, () => {
  console.log('Server started on port 4040')
})

// Handle errors that occur during the startup process
server.on('error', error => {
  console.error(error)
})
