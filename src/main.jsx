import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ArrowUpRight, Backpack, Camera, Check, CloudRain, Compass, CreditCard, FileCheck, HeartPulse, Hotel, Languages, MapPin, MapPinned, MoreHorizontal, Navigation, Plane, Play, Plus, ScanLine, Search, ShieldCheck, Sparkles, Sun, Users, Utensils, Wallet, WifiOff, Wind, X } from 'lucide-react'
import './styles.css'

const agenda = [
  { time: '08:30', title: 'Coffee & a slow start', place: 'Fábrica Coffee Roasters', tag: 'Easy pace', color: 'yellow', icon: Sun },
  { time: '10:15', title: 'Street art in Alfama', place: 'Graça → Alfama', tag: 'Walk 1.2 km', color: 'coral', icon: Navigation },
  { time: '13:00', title: 'Lunch with a view', place: 'Miradouro da Senhora', tag: 'Booked', color: 'blue', icon: MapPin },
  { time: '15:30', title: 'Ceramic studio visit', place: 'Oficina 166', tag: 'Group pick', color: 'purple', icon: Sparkles },
]

function App() {
  const [notice, setNotice] = useState(true)
  const [activeTab, setActiveTab] = useState('Today')
  const [playing, setPlaying] = useState(false)
  const [vibe, setVibe] = useState('quiet corners')
  const [packed, setPacked] = useState(false)
  const [receiptSplit, setReceiptSplit] = useState(false)
  const [flightSearch, setFlightSearch] = useState({ origin: 'LIS', destination: 'PAR', departureDate: '2026-10-18', adults: '2' })
  const [hotelSearch, setHotelSearch] = useState({ cityCode: 'LIS', checkInDate: '2026-10-18', checkOutDate: '2026-10-21', adults: '2' })
  const [travelResults, setTravelResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const [apiMessage, setApiMessage] = useState('')

  const scrollTo = (id, tab) => {
    setActiveTab(tab)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  const searchTravel = async (type) => {
    setSearching(true)
    setApiMessage('')
    const search = type === 'flights'
      ? { origin: flightSearch.origin, destination: flightSearch.destination, departure_date: flightSearch.departureDate, adults: Number(flightSearch.adults) }
      : { city_code: hotelSearch.cityCode, check_in_date: hotelSearch.checkInDate, check_out_date: hotelSearch.checkOutDate, adults: Number(hotelSearch.adults || 1) }
    try {
      const response = await fetch(`/api/${type}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(search) })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || payload.error || 'Search unavailable')
      setTravelResults({ type, results: payload.results })
    } catch (error) {
      setTravelResults(null)
      setApiMessage(error.message.includes('Amadeus credentials') || error.message.includes('Missing AMADEUS') ? 'Add Amadeus credentials to .env to search live inventory.' : error.message)
    } finally {
      setSearching(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Kinetix home"><span className="brand-mark"><Compass size={18} /></span> kinetix</a>
        <nav className="main-nav" aria-label="Primary navigation">
          {['Today', 'Explore', 'Memories'].map(tab => <button className={activeTab === tab ? 'nav-link active' : 'nav-link'} onClick={() => scrollTo(tab === 'Explore' ? 'before-trip' : tab === 'Memories' ? 'memory' : 'top', tab)} key={tab}>{tab}</button>)}
        </nav>
        <div className="profile-area"><button className="icon-button" aria-label="Add to trip"><Plus size={18} /></button><span className="avatar">AL</span></div>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy"><p className="eyebrow"><span className="pulse-dot" /> Your trip, in motion</p><h1>Lisbon,<br /><em>right now.</em></h1><p className="hero-subtitle">A living plan that listens to your energy, your people, and the city around you.</p><div className="hero-actions"><button className="primary-button" onClick={() => setNotice(true)}>Tune my day <Sparkles size={16} /></button><button className="text-button" onClick={() => setPlaying(!playing)}>{playing ? 'Pause preview' : 'Play trip preview'} <Play size={14} fill="currentColor" /></button></div></div>
        <div className="hero-art" aria-label="Lisbon travel illustration"><div className="sun-disc" /><div className="hill hill-back" /><div className="hill hill-front" /><div className="tram"><div className="tram-window" /><div className="tram-window" /><div className="tram-window" /></div><span className="art-label label-one">38° 42′ N</span><span className="art-label label-two">São Vicente</span><div className="route-line" /></div>
      </section>

      {notice && <section className="adaptive-notice"><div className="notice-icon"><HeartPulse size={18} /></div><div><strong>We noticed your battery is at 62%</strong><p>Today is now a little lighter. Your Alfama walk has a shaded shortcut, and the studio is staying in.</p></div><button className="close-button" aria-label="Dismiss update" onClick={() => setNotice(false)}><X size={17} /></button></section>}

      <section className="dashboard-grid">
        <div className="day-column">
          <div className="section-heading"><div><p className="eyebrow muted">Wednesday · 18 September</p><h2>Your day, flexing with you</h2></div><button className="more-button" aria-label="More options"><MoreHorizontal size={20} /></button></div>
          <div className="timeline">{agenda.map((item, index) => { const Icon = item.icon; return <article className={`agenda-item ${index === 1 ? 'current' : ''}`} key={item.title}><time>{item.time}</time><div className={`agenda-icon ${item.color}`}><Icon size={17} /></div><div className="agenda-content"><div className="agenda-title"><h3>{item.title}</h3>{index === 1 && <span className="now-pill">Now</span>}</div><p>{item.place}</p><span className="item-tag">{item.tag}</span></div><button className="item-arrow" aria-label={`Open ${item.title}`}><ArrowUpRight size={17} /></button></article> })}</div><button className="add-stop"><Plus size={16} /> Add a moment</button>
        </div>

        <aside className="side-column">
          <section className="weather-panel"><div className="panel-top"><span className="eyebrow muted">The city around you</span><CloudRain size={20} /></div><div className="weather-main"><span className="temperature">24°</span><div><strong>Bright, then breezy</strong><p>Lisbon · 14:20</p></div></div><div className="weather-bars"><span style={{ width: '76%' }} /><span style={{ width: '42%' }} /><span style={{ width: '58%' }} /></div><div className="weather-foot"><span><Wind size={14} /> 18 km/h</span><span><CloudRain size={14} /> 20% rain</span></div></section>
          <section className="group-panel"><div className="panel-top"><span className="eyebrow muted">The group pulse</span><Users size={19} /></div><div className="people"><span className="mini-avatar peach">M</span><span className="mini-avatar green">J</span><span className="mini-avatar blue">S</span><span className="mini-avatar more">+1</span><span className="group-note">4 people, 4 points of view</span></div><div className="preference-row"><span>Slow mornings</span><b>92%</b></div><div className="preference-row"><span>Local food</span><b>84%</b></div><button className="outline-button">See the compromise <ArrowUpRight size={15} /></button></section>
          <section className="budget-panel"><div className="panel-top"><span className="eyebrow muted">Trip wallet</span><Wallet size={18} /></div><div className="budget-amount">€438 <span>of €720</span></div><div className="budget-track"><span /></div><div className="budget-foot"><span>On track</span><strong>Save €42 today</strong></div></section>
        </aside>
      </section>

      <section className="feature-zone" id="before-trip">
        <div className="feature-zone-heading"><div><p className="eyebrow muted">Before you go</p><h2>Make the unknown feel easy.</h2></div><span className="agent-status"><span className="pulse-dot" /> Agent ready</span></div>
        <div className="feature-grid">
          <article className="feature-card vibe-card"><div className="feature-card-top"><div className="feature-icon coral-icon"><Sparkles size={18} /></div><span className="card-kicker">Vibe search</span></div><h3>Find somewhere that feels like <em>{vibe}</em></h3><div className="vibe-input"><span>I'm looking for</span><input aria-label="Vibe search" value={vibe} onChange={event => setVibe(event.target.value)} /><ArrowUpRight size={16} /></div><div className="result-row"><div className="result-image image-cafe" /><div><strong>Casa do Beco</strong><p>Hidden garden · 4.8 km away</p></div><span className="match">96%</span></div></article>
          <article className="feature-card booking-card"><div className="feature-card-top"><div className="feature-icon yellow-icon"><ShieldCheck size={18} /></div><span className="card-kicker">Autonomous booking</span></div><h3>Two small decisions, handled.</h3><div className="booking-row"><span><Camera size={15} /> Fado at Mesa de Frades</span><b>€32</b><button className="mini-book">Book</button></div><div className="booking-row"><span><MapPinned size={15} /> Airport → apartment</span><b>€18</b><button className="mini-book booked"><Check size={14} /> Done</button></div><p className="card-foot"><CreditCard size={14} /> Within your €720 trip budget</p></article>
          <article className="feature-card prep-card"><div className="feature-card-top"><div className="feature-icon blue-icon"><Backpack size={18} /></div><span className="card-kicker">Smart prep</span></div><h3>Ready for Lisbon's micro-climates.</h3><div className="prep-list"><span><Backpack size={14} /> Light layer <small>18° evenings</small></span><span><FileCheck size={14} /> Passport valid <small>Visa not required</small></span></div><button className="outline-button" onClick={() => setPacked(!packed)}>{packed ? <Check size={15} /> : <Plus size={15} />} {packed ? 'Packing list saved' : 'Build my packing list'}</button></article>
        </div>
      </section>

      <section className="live-search-zone" id="live-booking">
        <div className="feature-zone-heading"><div><p className="eyebrow muted">Live inventory</p><h2>Book the next chapter.</h2></div><span className="provider-label"><Search size={14} /> Amadeus connected</span></div>
        <div className="search-grid">
          <form className="search-panel flight-search" onSubmit={event => { event.preventDefault(); searchTravel('flights') }}><div className="search-panel-title"><Plane size={18} /><strong>Flights</strong><span>Real-time fares</span></div><div className="search-fields"><label>From<input value={flightSearch.origin} maxLength="3" onChange={event => setFlightSearch({ ...flightSearch, origin: event.target.value.toUpperCase() })} /></label><label>To<input value={flightSearch.destination} maxLength="3" onChange={event => setFlightSearch({ ...flightSearch, destination: event.target.value.toUpperCase() })} /></label><label>Depart<input type="date" value={flightSearch.departureDate} onChange={event => setFlightSearch({ ...flightSearch, departureDate: event.target.value })} /></label><label>Travelers<input type="number" min="1" max="9" value={flightSearch.adults} onChange={event => setFlightSearch({ ...flightSearch, adults: event.target.value })} /></label></div><button className="dark-button" disabled={searching}><Search size={15} /> {searching ? 'Searching...' : 'Search flights'}</button></form>
          <form className="search-panel hotel-search" onSubmit={event => { event.preventDefault(); searchTravel('hotels') }}><div className="search-panel-title"><Hotel size={18} /><strong>Hotels</strong><span>Live availability</span></div><div className="search-fields"><label>City code<input value={hotelSearch.cityCode} maxLength="3" onChange={event => setHotelSearch({ ...hotelSearch, cityCode: event.target.value.toUpperCase() })} /></label><label>Check in<input type="date" value={hotelSearch.checkInDate} onChange={event => setHotelSearch({ ...hotelSearch, checkInDate: event.target.value })} /></label><label>Check out<input type="date" value={hotelSearch.checkOutDate} onChange={event => setHotelSearch({ ...hotelSearch, checkOutDate: event.target.value })} /></label></div><button className="dark-button" disabled={searching}><Search size={15} /> {searching ? 'Searching...' : 'Search hotels'}</button></form>
        </div>
        {apiMessage && <p className="api-message"><ShieldCheck size={15} /> {apiMessage}</p>}
        {travelResults && <div className="search-results"><div className="results-heading"><span>{travelResults.type === 'flights' ? 'Flight options' : 'Hotel options'}</span><small>Live from Amadeus</small></div>{travelResults.results.length === 0 ? <p className="empty-results">No live options matched those dates.</p> : travelResults.results.slice(0, 3).map(result => <div className="search-result" key={result.id || result.hotelId}><div><strong>{travelResults.type === 'flights' ? `${result.airline || 'Airline'} · ${result.stops} stop${result.stops === 1 ? '' : 's'}` : result.name}</strong><p>{travelResults.type === 'flights' ? `${result.duration?.replace('PT', '').replace('H', 'h ').replace('M', 'm') || 'Flexible duration'}` : `${result.rating ? `${result.rating} star · ` : ''}${result.room || 'Room available'}`}</p></div><b>{result.currency} {result.price}</b><button className="mini-book">Select</button></div>)}</div>}
      </section>

      <section className="feature-zone ground-zone" id="during-trip">
        <div className="feature-zone-heading"><div><p className="eyebrow muted">On the ground</p><h2>Help that keeps up.</h2></div><span className="offline-label"><WifiOff size={14} /> Offline ready</span></div>
        <div className="ground-grid"><article className="map-card"><div className="map-copy"><span className="card-kicker">Explore without signal</span><h3>Alfama, in layers.</h3><p>Your route, saved offline. Point your camera at the city and let its stories surface.</p><div className="map-actions"><button className="dark-button"><MapPinned size={15} /> Open offline map</button><button className="small-icon-button" aria-label="Open AR landmark view"><Camera size={16} /></button></div></div><div className="map-art"><span className="map-pin pin-one" /><span className="map-pin pin-two" /><span className="map-street street-one" /><span className="map-street street-two" /><span className="map-label">AR LAYER ON</span></div></article><article className="assist-card"><div className="feature-card-top"><div className="feature-icon purple-icon"><Languages size={18} /></div><span className="card-kicker">Instant assist</span></div><h3>Point, scan, understand.</h3><div className="assist-item"><Utensils size={16} /><div><strong>Menu translator</strong><p>“Does this contain shellfish?” highlighted in Portuguese.</p></div><span className="live-pill">Live</span></div><div className="assist-item"><ScanLine size={16} /><div><strong>Receipt split</strong><p>€84.20 · 4 people · tax included</p></div><button className="split-button" onClick={() => setReceiptSplit(!receiptSplit)}>{receiptSplit ? 'Split' : 'Scan'}</button></div>{receiptSplit && <div className="split-result"><Check size={14} /> €21.05 each · settled in group wallet</div>}</article></div>
      </section>

      <section className="memory-banner" id="memory"><div className="memory-copy"><span className="eyebrow">After the trip</span><h2>Your Lisbon, remembered.</h2><p>Kinetix turns the little things into a story worth keeping.</p><button className="dark-button" onClick={() => setPlaying(!playing)}>{playing ? 'Playing your story' : 'Preview your story'} <Play size={15} fill="currentColor" /></button></div><div className="memory-stack"><div className="photo photo-back" /><div className="photo photo-mid" /><div className="photo photo-front"><span>18.09.24</span></div></div></section>
      <footer><span>kinetix</span><span>Adaptive by design · Lisbon 2024</span></footer>
    </main>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
