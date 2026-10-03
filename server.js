import 'dotenv/config'
import express from 'express'
import cors from 'cors'

const app = express()
const port = process.env.PORT || 8787
const host = process.env.HOST || '0.0.0.0'
const amadeusHost = process.env.AMADEUS_HOST || 'https://test.api.amadeus.com'
let accessToken = null
let tokenExpiresAt = 0

const allowedOrigins = (process.env.CLIENT_ORIGIN || 'http://localhost:5173,http://127.0.0.1:5173').split(',').map(origin => origin.trim())
app.use(cors({ origin: (origin, callback) => {
  if (!origin || allowedOrigins.includes(origin)) return callback(null, true)
  callback(new Error('Origin is not allowed by Kinetix API'))
} }))
app.use(express.json())

async function getAccessToken() {
  if (accessToken && Date.now() < tokenExpiresAt) return accessToken
  if (!process.env.AMADEUS_CLIENT_ID || !process.env.AMADEUS_CLIENT_SECRET) {
    const error = new Error('Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET')
    error.status = 503
    throw error
  }

  const response = await fetch(`${amadeusHost}/v1/security/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.AMADEUS_CLIENT_ID,
      client_secret: process.env.AMADEUS_CLIENT_SECRET,
    }),
  })
  const payload = await response.json()
  if (!response.ok) throw new Error(payload?.error_description || 'Amadeus authentication failed')
  accessToken = payload.access_token
  tokenExpiresAt = Date.now() + (payload.expires_in - 60) * 1000
  return accessToken
}

async function amadeusRequest(path, options = {}) {
  const token = await getAccessToken()
  const response = await fetch(`${amadeusHost}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  })
  const payload = await response.json()
  if (!response.ok) {
    const error = new Error(payload?.errors?.[0]?.detail || 'Amadeus request failed')
    error.status = response.status
    throw error
  }
  return payload
}

function required(value, name) {
  if (!value || typeof value !== 'string') {
    const error = new Error(`${name} is required`)
    error.status = 400
    throw error
  }
  return value.trim()
}

app.get('/api/health', (_request, response) => response.json({ provider: 'amadeus', configured: Boolean(process.env.AMADEUS_CLIENT_ID && process.env.AMADEUS_CLIENT_SECRET) }))

app.get('/api/flights', async (request, response) => {
  try {
    const origin = required(request.query.origin, 'origin').toUpperCase()
    const destination = required(request.query.destination, 'destination').toUpperCase()
    const departureDate = required(request.query.departureDate, 'departureDate')
    const adults = Math.min(Math.max(Number(request.query.adults) || 1, 1), 9)
    const params = new URLSearchParams({ originLocationCode: origin, destinationLocationCode: destination, departureDate, adults: String(adults), currencyCode: 'EUR', max: '8' })
    const payload = await amadeusRequest(`/v2/shopping/flight-offers?${params}`)
    const flights = (payload.data || []).map(offer => ({
      id: offer.id,
      price: offer.price?.grandTotal,
      currency: offer.price?.currency,
      airline: offer.validatingAirlineCodes?.[0],
      duration: offer.itineraries?.[0]?.duration,
      stops: Math.max((offer.itineraries?.[0]?.segments?.length || 1) - 1, 0),
      departure: offer.itineraries?.[0]?.segments?.[0]?.departure?.at,
      arrival: offer.itineraries?.[0]?.segments?.at(-1)?.arrival?.at,
    }))
    response.json({ source: 'amadeus', results: flights })
  } catch (error) {
    response.status(error.status || 502).json({ error: error.message })
  }
})

app.get('/api/hotels', async (request, response) => {
  try {
    const cityCode = required(request.query.cityCode, 'cityCode').toUpperCase()
    const checkInDate = required(request.query.checkInDate, 'checkInDate')
    const checkOutDate = required(request.query.checkOutDate, 'checkOutDate')
    const adults = Math.min(Math.max(Number(request.query.adults) || 1, 1), 9)
    const params = new URLSearchParams({ cityCode, checkInDate, checkOutDate, adults: String(adults), roomQuantity: '1', currency: 'EUR', radius: '20', radiusUnit: 'KM', hotelSource: 'ALL' })
    const payload = await amadeusRequest(`/v2/shopping/hotel-offers?${params}`)
    const hotels = (payload.data || []).map(item => ({
      hotelId: item.hotel?.hotelId,
      name: item.hotel?.name,
      rating: item.hotel?.rating,
      distance: item.hotel?.distance?.value,
      price: item.offers?.[0]?.price?.total,
      currency: item.offers?.[0]?.price?.currency,
      room: item.offers?.[0]?.room?.description?.text,
    }))
    response.json({ source: 'amadeus', results: hotels })
  } catch (error) {
    response.status(error.status || 502).json({ error: error.message })
  }
})

app.listen(port, host, () => console.log(`Kinetix API listening on http://${host}:${port}`))
