"use client";

import { useEffect, useMemo, useState } from "react";
import seedData from "../public/data/dashboard.json";

type Horizon = "short" | "long";
type Signal = "ACCUMULATE" | "HOLD" | "REDUCE" | "AVOID" | "WATCH";
type Stock = { symbol: string; company: string; sector: string; price: number; change: number; signal: Signal; confidence: number; score: number; allocation: number; rationale: string; risk: string; spark: number[] };
type IntelligenceEvent = { id: string; timestamp: string; region: string; title: string; source: string; sourceUrl?: string; status: "CONFIRMED" | "DEVELOPING" | "DISPUTED"; impact: "POSITIVE" | "NEGATIVE" | "MIXED"; companies: string[]; summary: string };
type DashboardData = { generatedAt: string; market: { regime: string; score: number; nifty: number; niftyChange: number; vix: number; breadth: number }; portfolio: { value: number; dayChange: number; totalReturn: number; maxDrawdown: number; cash: number; history: number[] }; shortTerm: Stock[]; longTerm: Stock[]; events: IntelligenceEvent[]; sectors: { name: string; score: number; change: number }[] };

const initialData = seedData as DashboardData;

function formatINR(value: number, compact = false) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: compact ? 0 : 2, notation: compact ? "compact" : "standard" }).format(value);
}

function timeAgo(timestamp: string, referenceTimestamp: string) {
  const minutes = Math.max(1, Math.floor((new Date(referenceTimestamp).getTime() - new Date(timestamp).getTime()) / 60000));
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours}h ago` : `${Math.floor(hours / 24)}d ago`;
}

function Sparkline({ values, positive = true }: { values: number[]; positive?: boolean }) {
  const width = 120, height = 36, min = Math.min(...values), max = Math.max(...values), range = Math.max(1, max - min);
  const points = values.map((value, index) => `${(index / (values.length - 1)) * width},${height - ((value - min) / range) * height}`).join(" ");
  return <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} aria-hidden="true"><polyline points={points} fill="none" stroke={positive ? "#9eff7a" : "#ff7a91"} strokeWidth="2.5" /></svg>;
}

function PortfolioChart({ values }: { values: number[] }) {
  const width = 720, height = 180, min = Math.min(...values) * 0.995, max = Math.max(...values) * 1.005, range = max - min;
  const points = values.map((value, index) => `${(index / (values.length - 1)) * width},${height - ((value - min) / range) * height}`).join(" ");
  return <svg className="portfolio-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Portfolio value over the last 30 sessions"><defs><linearGradient id="portfolioFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#c7ff4a" stopOpacity="0.28" /><stop offset="100%" stopColor="#c7ff4a" stopOpacity="0" /></linearGradient></defs>{[0,1,2,3].map((line) => <line key={line} x1="0" x2={width} y1={(height / 3) * line} y2={(height / 3) * line} stroke="rgba(255,255,255,.08)" />)}<polygon points={`0,${height} ${points} ${width},${height}`} fill="url(#portfolioFill)" /><polyline points={points} fill="none" stroke="#c7ff4a" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" /></svg>;
}

export default function Home() {
  const [data, setData] = useState<DashboardData>(initialData);
  const [horizon, setHorizon] = useState<Horizon>("long");
  const [selected, setSelected] = useState(initialData.longTerm[0].symbol);
  const [query, setQuery] = useState("");
  const [eventFilter, setEventFilter] = useState<"ALL" | "CONFIRMED" | "DEVELOPING">("ALL");

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
    fetch(`${base}/data/dashboard.json?ts=${Date.now()}`).then((response) => response.ok ? response.json() : Promise.reject()).then((fresh: DashboardData) => setData(fresh)).catch(() => undefined);
  }, []);

  const stocks = horizon === "long" ? data.longTerm : data.shortTerm;
  const filteredStocks = stocks.filter((stock) => `${stock.symbol} ${stock.company} ${stock.sector}`.toLowerCase().includes(query.toLowerCase()));
  const selectedStock = stocks.find((stock) => stock.symbol === selected) ?? stocks[0];
  const visibleEvents = data.events.filter((event) => eventFilter === "ALL" || event.status === eventFilter);
  const updatedLabel = useMemo(() => new Date(data.generatedAt).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Kolkata" }), [data.generatedAt]);
  const changeHorizon = (next: Horizon) => { setHorizon(next); setSelected((next === "long" ? data.longTerm : data.shortTerm)[0].symbol); };

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand" aria-label="World Market Intelligence home"><div className="brand-mark">W</div><div><strong>WORLD//MARKET</strong><span>INTELLIGENCE</span></div></div>
      <nav className="nav-list" aria-label="Primary navigation"><a className="nav-item active" href="#overview"><span>01</span>Overview</a><a className="nav-item" href="#signals"><span>02</span>Signals</a><a className="nav-item" href="#intelligence"><span>03</span>Intelligence</a><a className="nav-item" href="#portfolio"><span>04</span>Portfolio</a></nav>
      <div className="sidebar-foot"><div className="system-state"><i />SYSTEM OPERATIONAL</div><p>Last research cycle</p><strong>{updatedLabel}</strong><small>Personal research environment</small></div>
    </aside>

    <section className="workspace">
      <header className="topbar"><div><p className="eyebrow">DECISION TERMINAL / INDIA</p><h1>Market Intelligence</h1></div><div className="top-actions"><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search securities" aria-label="Search securities" /></label><button className="icon-button" aria-label="Notifications">◉<b>3</b></button><button className="profile-button" aria-label="User profile">GA</button></div></header>

      <div className="content" id="overview">
        <section className="market-strip" aria-label="Market overview"><article className="regime-card"><div><p>MARKET REGIME</p><strong>{data.market.regime}</strong></div><div className="regime-score"><span>{data.market.score}</span><small>/100</small></div></article><article><p>NIFTY 50</p><strong>{data.market.nifty.toLocaleString("en-IN")}</strong><span className={data.market.niftyChange >= 0 ? "positive" : "negative"}>▲ {data.market.niftyChange.toFixed(2)}%</span></article><article><p>INDIA VIX</p><strong>{data.market.vix.toFixed(2)}</strong><span className="muted">LOW–MODERATE</span></article><article><p>MARKET BREADTH</p><strong>{data.market.breadth}%</strong><span className="positive">ADVANCING</span></article></section>

        <section className="dashboard-grid">
          <article className="panel portfolio-panel" id="portfolio"><div className="panel-head"><div><p className="panel-kicker">PORTFOLIO VALUE</p><h2>{formatINR(data.portfolio.value, true)}</h2></div><div className="period-tabs"><button>1W</button><button className="active">1M</button><button>3M</button><button>1Y</button></div></div><div className="portfolio-meta"><span className="positive">+{data.portfolio.dayChange}% today</span><span><b>+{data.portfolio.totalReturn}%</b> total return</span><span><b>{data.portfolio.maxDrawdown}%</b> max drawdown</span></div><PortfolioChart values={data.portfolio.history} /><div className="chart-labels"><span>JUL 06</span><span>JUL 13</span><span>JUL 20</span><span>JUL 27</span><span>AUG 03</span></div></article>

          <article className="panel world-panel"><div className="panel-head"><div><p className="panel-kicker">GLOBAL EVENT PULSE</p><h3>Active impact zones</h3></div><span className="live-badge">● LIVE</span></div><div className="world-map" aria-label="Stylised world event map"><div className="continent americas" /><div className="continent europe" /><div className="continent asia" /><div className="continent africa" /><div className="continent oceania" /><i className="pulse p1"><b>4</b></i><i className="pulse p2 warning"><b>7</b></i><i className="pulse p3"><b>3</b></i><i className="pulse p4 danger"><b>5</b></i></div><div className="impact-legend"><span><i className="positive-dot" />POSITIVE 8</span><span><i className="mixed-dot" />MIXED 11</span><span><i className="negative-dot" />NEGATIVE 6</span></div></article>

          <article className="panel signals-panel" id="signals"><div className="panel-head signal-heading"><div><p className="panel-kicker">DECISION ENGINE</p><h3>Highest-conviction signals</h3></div><div className="horizon-toggle" role="tablist" aria-label="Investment horizon"><button className={horizon === "short" ? "active" : ""} onClick={() => changeHorizon("short")}>SHORT TERM</button><button className={horizon === "long" ? "active" : ""} onClick={() => changeHorizon("long")}>LONG TERM</button></div></div><div className="stock-table" role="table"><div className="stock-row stock-header" role="row"><span>SECURITY</span><span>PRICE / MOVE</span><span>TREND</span><span>DECISION</span><span>CONFIDENCE</span></div>{filteredStocks.map((stock) => <button className={`stock-row ${selectedStock.symbol === stock.symbol ? "selected" : ""}`} key={stock.symbol} onClick={() => setSelected(stock.symbol)} role="row"><span className="security"><b>{stock.symbol}</b><small>{stock.company}</small></span><span><b>{formatINR(stock.price)}</b><small className={stock.change >= 0 ? "positive" : "negative"}>{stock.change >= 0 ? "+" : ""}{stock.change}%</small></span><Sparkline values={stock.spark} positive={stock.change >= 0} /><span><em className={`signal ${stock.signal.toLowerCase()}`}>{stock.signal}</em><small>{stock.score}/100 score</small></span><span className="confidence"><b>{stock.confidence}%</b><i><u style={{ width: `${stock.confidence}%` }} /></i></span></button>)}</div></article>

          <aside className="panel thesis-panel" aria-live="polite"><div className="thesis-top"><span>{selectedStock.sector}</span><em className={`signal ${selectedStock.signal.toLowerCase()}`}>{selectedStock.signal}</em></div><h2>{selectedStock.symbol}</h2><p className="company-name">{selectedStock.company}</p><div className="score-ring" style={{ "--score": selectedStock.score } as React.CSSProperties}><strong>{selectedStock.score}</strong><small>COMPOSITE<br />SCORE</small></div><div className="thesis-block"><p>WHY NOW</p><span>{selectedStock.rationale}</span></div><div className="thesis-block risk"><p>KEY RISK</p><span>{selectedStock.risk}</span></div><div className="allocation"><span>MODEL ALLOCATION</span><strong>{selectedStock.allocation}%</strong></div><button className="review-button">OPEN FULL EVIDENCE <span>→</span></button></aside>

          <article className="panel intelligence-panel" id="intelligence"><div className="panel-head"><div><p className="panel-kicker">VERIFIED INTELLIGENCE</p><h3>Events moving the market</h3></div><div className="filter-tabs">{(["ALL", "CONFIRMED", "DEVELOPING"] as const).map((filter) => <button className={eventFilter === filter ? "active" : ""} onClick={() => setEventFilter(filter)} key={filter}>{filter}</button>)}</div></div><div className="event-list">{visibleEvents.map((event) => <article className="event-item" key={event.id}><div className={`event-impact ${event.impact.toLowerCase()}`}>{event.impact === "POSITIVE" ? "↗" : event.impact === "NEGATIVE" ? "↘" : "↔"}</div><div className="event-copy"><div><span>{event.region}</span><i>•</i><span>{timeAgo(event.timestamp, data.generatedAt)}</span><em className={event.status.toLowerCase()}>{event.status}</em></div><h4>{event.sourceUrl ? <a href={event.sourceUrl} target="_blank" rel="noreferrer">{event.title}</a> : event.title}</h4><p>{event.summary}</p><small>Source: {event.source}</small></div><div className="company-tags">{event.companies.map((company) => <span key={company}>{company}</span>)}</div></article>)}</div></article>

          <article className="panel sector-panel"><div className="panel-head"><div><p className="panel-kicker">SECTOR RELATIVE STRENGTH</p><h3>Capital rotation</h3></div><span className="muted">30D SCORE</span></div><div className="sector-list">{data.sectors.map((sector) => <div className="sector-row" key={sector.name}><span>{sector.name}</span><i><u style={{ width: `${sector.score}%` }} /></i><strong>{sector.score}</strong><em className={sector.change >= 0 ? "positive" : "negative"}>{sector.change >= 0 ? "+" : ""}{sector.change}%</em></div>)}</div></article>
        </section>
        <footer><span>Research system, not investment advice.</span><span>Evidence records are timestamped to prevent look-ahead bias.</span></footer>
      </div>
    </section>
  </main>;
}
