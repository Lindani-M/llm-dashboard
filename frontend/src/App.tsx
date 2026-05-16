import { useEffect, useState, useCallback } from 'react';
import './dashboard.css';
import { Metrics, Commentary, CommentarySection } from './types';
import { fetchMetrics, fetchCommentary, saveCommentary, revertCommentary, refreshData } from './api';
import CommentaryBox from './components/CommentaryBox';
import EditableText from './components/EditableText';

function fmt(n: number) {
  return n.toLocaleString('en-US');
}

function fmtPct(n: number) {
  return `${n.toFixed(1)}%`;
}

function fmtUSD(n: number) {
  return `$${n.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
}

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [commentary, setCommentary] = useState<Commentary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchCommentary()])
      .then(([m, c]) => { setMetrics(m); setCommentary(c); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = useCallback(async (sectionId: string, content: string) => {
    const updated = await saveCommentary(sectionId, content);
    setCommentary((prev) => prev ? { ...prev, [sectionId]: updated } : prev);
  }, []);

  const handleRevert = useCallback(async (sectionId: string) => {
    const updated = await revertCommentary(sectionId);
    setCommentary((prev) => prev ? { ...prev, [sectionId]: updated } : prev);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg('Refreshing data and regenerating AI commentary…');
    try {
      const result = await refreshData();
      setMetrics(result.metrics);
      setCommentary(result.commentary);
      const errMsg = result.errors.length > 0 ? ` (${result.errors.length} AI error(s))` : '';
      setRefreshMsg(`Updated ${new Date().toLocaleTimeString()}${errMsg}`);
    } catch (e: unknown) {
      setRefreshMsg('Refresh failed — check backend');
    } finally {
      setRefreshing(false);
    }
  };

  const c = (id: string): CommentarySection | undefined => commentary?.[id];

  if (loading) return <div className="loading-screen">Loading dashboard data…</div>;
  if (error) return <div className="loading-screen" style={{ color: '#c0392b' }}>Error: {error}</div>;
  if (!metrics) return null;

  const { kpis, geography, age, gender, products, activity, balance, credit_score, tenure } = metrics;

  // Highest churn tenure year (for gold highlight)
  const maxTenureRate = Math.max(...Object.values(tenure).map((t) => t.churn_rate));

  // Summary table rows
  const tableRows = [
    { segment: 'Products', category: '4 Products', ...products['4'], risk: 'high' },
    { segment: 'Products', category: '3 Products', ...products['3'], risk: 'high' },
    { segment: 'Age', category: '50–59', ...age['50-59'], risk: 'high' },
    { segment: 'Geography', category: 'Germany', ...geography['Germany'], risk: 'high' },
    { segment: 'Age', category: '40–49', ...age['40-49'], risk: 'high' },
    { segment: 'Products', category: '1 Product', ...products['1'], risk: 'medium' },
    { segment: 'Age', category: '60+', ...age['60+'], risk: 'medium' },
    { segment: 'Activity', category: 'Inactive', ...activity['Inactive'], risk: 'medium' },
    { segment: 'Gender', category: 'Female', ...gender['Female'], risk: 'medium' },
    { segment: 'Balance', category: 'Has Balance', ...balance['Has Balance'], risk: 'medium' },
    { segment: 'Gender', category: 'Male', ...gender['Male'], risk: 'low' },
    { segment: 'Activity', category: 'Active', ...activity['Active'], risk: 'low' },
    { segment: 'Products', category: '2 Products', ...products['2'], risk: 'low' },
  ].filter((r) => r.total !== undefined);

  return (
    <>
      {/* ── Header ── */}
      <div className="dashboard-header">
        <div className="header-top">
          <div className="header-title">
            <h1>Customer Churn Dashboard</h1>
            <div className="header-subtitle">
              Retention Analytics &amp; Risk Assessment · Analysis Period 2026
            </div>
          </div>
          <div className="header-actions">
            <div>
              <button className="refresh-btn" onClick={handleRefresh} disabled={refreshing}>
                {refreshing ? 'Refreshing…' : '↻ Refresh Data'}
              </button>
              {refreshMsg && <div className="refresh-status">{refreshMsg}</div>}
            </div>
            <div className="brand">
              Acme <span>&amp;</span> Trust<br />
              <span style={{ fontSize: '11px', letterSpacing: '2px', fontFamily: 'Source Sans Pro, sans-serif', fontStyle: 'normal' }}>
                BANKING GROUP
              </span>
            </div>
          </div>
        </div>
        <div className="tabs">
          <div className="tab active">Churn Overview</div>
          <div className="tab">Customer Portfolio</div>
          <div className="tab">Risk Segments</div>
          <div className="tab">Retention Strategy</div>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="main-content">

        <h2 className="section-title">Customer Churn — Portfolio Overview</h2>
        <p className="section-subtitle">
          <EditableText
            sectionId="section_subtitle"
            data={c('section_subtitle')}
            multiline
            onSave={handleSave}
            onRevert={handleRevert}
          />
        </p>

        {/* KPI Row */}
        <div className="kpi-row">
          <div className="kpi-card">
            <div className="kpi-label">Total Customers</div>
            <div className="kpi-value">{fmt(kpis.total_customers)}</div>
            <div className="kpi-desc">Active portfolio under analysis</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Churned Customers</div>
            <div className="kpi-value danger">{fmt(kpis.churned_customers)}</div>
            <div className="kpi-desc">Customers who have exited the bank</div>
          </div>
          <div className="kpi-card highlight">
            <div className="kpi-label">Overall Churn Rate</div>
            <div className="kpi-value danger">{fmtPct(kpis.churn_rate)}</div>
            <div className="kpi-desc">1 in {Math.round(100 / kpis.churn_rate)} customers leaving</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Avg Balance (Churned)</div>
            <div className="kpi-value">{fmtUSD(kpis.avg_balance_churned)}</div>
            <div className="kpi-desc">
              {Math.round((kpis.avg_balance_churned / kpis.avg_balance_retained - 1) * 100)}% higher than retained customers
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Retention Rate</div>
            <div className="kpi-value positive">{fmtPct(kpis.retention_rate)}</div>
            <div className="kpi-desc">{fmt(kpis.retained_customers)} customers retained</div>
          </div>
        </div>

        {/* Executive Summary */}
        <CommentaryBox
          sectionId="executive_summary"
          data={c('executive_summary')}
          variant="box"
          title="Executive Summary"
          onSave={handleSave}
          onRevert={handleRevert}
        />

        {/* Charts Row 1: Geography + Age */}
        <div className="charts-row">
          {/* Geography */}
          <div className="chart-card">
            <div className="chart-title">Churn by Geography (Cumulative)</div>
            <div className="legend">
              <div className="legend-item"><div className="legend-dot navy" />Retained</div>
              <div className="legend-item"><div className="legend-dot gold" />Churned</div>
            </div>
            <div className="bar-chart">
              {Object.entries(geography).map(([geo, stat]) => (
                <div className="bar-row" key={geo}>
                  <div className="bar-label">{geo}</div>
                  <div className="stacked-bar-track">
                    <div className="stacked-segment retained" style={{ width: `${100 - stat.churn_rate}%` }} />
                    <div className="stacked-segment churned" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className={`bar-value${stat.churn_rate > 25 ? ' danger' : ''}`}>
                    {fmtPct(stat.churn_rate)}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--gray-200)' }}>
              {Object.entries(geography).map(([geo, stat]) => (
                <div key={geo}>
                  <div style={{ fontSize: '11px', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '1px' }}>{geo}</div>
                  <div style={{ fontFamily: 'Playfair Display, serif', fontSize: '18px', color: 'var(--navy)', fontWeight: 700 }}>{fmt(stat.total)}</div>
                </div>
              ))}
            </div>
            <CommentaryBox sectionId="geography_insight" data={c('geography_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>

          {/* Age */}
          <div className="chart-card">
            <div className="chart-title">Churn by Age Group</div>
            <div className="legend">
              <div className="legend-item"><div className="legend-dot navy" />Retained</div>
              <div className="legend-item"><div className="legend-dot gold" />Churned</div>
            </div>
            <div className="bar-chart">
              {Object.entries(age).map(([group, stat]) => (
                <div className="bar-row" key={group}>
                  <div className="bar-label">{group}</div>
                  <div className="stacked-bar-track">
                    <div className="stacked-segment retained" style={{ width: `${100 - stat.churn_rate}%` }} />
                    <div className="stacked-segment churned" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className={`bar-value${stat.churn_rate > 25 ? ' danger' : ''}`}>
                    {fmtPct(stat.churn_rate)}
                  </div>
                </div>
              ))}
            </div>
            <CommentaryBox sectionId="age_insight" data={c('age_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>
        </div>

        {/* High-Risk Segments */}
        <h2 className="status-header">High-Risk Segments</h2>
        <p className="section-subtitle" style={{ marginTop: '4px' }}>
          Deep-dive into the customer segments contributing most to attrition.
        </p>

        <div className="grantee-cards">
          {/* Inactive Members */}
          <div className="grantee-card">
            <div className="grantee-card-header">
              <div>
                <h3><EditableText sectionId="grantee_title_inactive" data={c('grantee_title_inactive')} onSave={handleSave} onRevert={handleRevert} /></h3>
                <div className="grantee-badge">Engagement Risk</div>
              </div>
              <div>
                <div className="grantee-stat">{fmtPct(activity['Inactive'].churn_rate)}</div>
                <div className="grantee-stat-label">Churn Rate</div>
              </div>
            </div>
            <CommentaryBox sectionId="inactive_members_body" data={c('inactive_members_body')} variant="grantee" onSave={handleSave} onRevert={handleRevert} />
            <div className="grantee-metrics">
              <div><div className="grantee-metric-value">{fmt(activity['Inactive'].total)}</div><div className="grantee-metric-label">Total Inactive</div></div>
              <div><div className="grantee-metric-value">{fmt(activity['Inactive'].churned)}</div><div className="grantee-metric-label">Churned</div></div>
              <div><div className="grantee-metric-value">{(activity['Inactive'].churn_rate / activity['Active'].churn_rate).toFixed(1)}×</div><div className="grantee-metric-label">vs Active Rate</div></div>
            </div>
          </div>

          {/* Multi-Product */}
          <div className="grantee-card">
            <div className="grantee-card-header">
              <div>
                <h3><EditableText sectionId="grantee_title_multiproduct" data={c('grantee_title_multiproduct')} onSave={handleSave} onRevert={handleRevert} /></h3>
                <div className="grantee-badge">Product Risk</div>
              </div>
              <div>
                <div className="grantee-stat">
                  {products['3'] && products['4']
                    ? fmtPct((products['3'].churn_rate + products['4'].churn_rate) / 2)
                    : products['3'] ? fmtPct(products['3'].churn_rate) : 'N/A'}
                </div>
                <div className="grantee-stat-label">Avg Churn Rate (3–4 prod)</div>
              </div>
            </div>
            <CommentaryBox sectionId="multi_product_body" data={c('multi_product_body')} variant="grantee" onSave={handleSave} onRevert={handleRevert} />
            <div className="grantee-metrics">
              <div>
                <div className="grantee-metric-value">{fmt((products['3']?.total ?? 0) + (products['4']?.total ?? 0))}</div>
                <div className="grantee-metric-label">Customers (3+ Prod)</div>
              </div>
              <div>
                <div className="grantee-metric-value">{fmt((products['3']?.churned ?? 0) + (products['4']?.churned ?? 0))}</div>
                <div className="grantee-metric-label">Churned</div>
              </div>
              <div>
                <div className="grantee-metric-value">{products['4'] ? fmtPct(products['4'].churn_rate) : 'N/A'}</div>
                <div className="grantee-metric-label">4-Product Exit</div>
              </div>
            </div>
          </div>

          {/* Female Customers */}
          <div className="grantee-card">
            <div className="grantee-card-header">
              <div>
                <h3><EditableText sectionId="grantee_title_female" data={c('grantee_title_female')} onSave={handleSave} onRevert={handleRevert} /></h3>
                <div className="grantee-badge">Demographic Risk</div>
              </div>
              <div>
                <div className="grantee-stat">{fmtPct(gender['Female'].churn_rate)}</div>
                <div className="grantee-stat-label">Churn Rate</div>
              </div>
            </div>
            <CommentaryBox sectionId="female_customers_body" data={c('female_customers_body')} variant="grantee" onSave={handleSave} onRevert={handleRevert} />
            <div className="grantee-metrics">
              <div><div className="grantee-metric-value">{fmt(gender['Female'].total)}</div><div className="grantee-metric-label">Total Female</div></div>
              <div><div className="grantee-metric-value">{fmt(gender['Female'].churned)}</div><div className="grantee-metric-label">Churned</div></div>
              <div><div className="grantee-metric-value">{(gender['Female'].churn_rate / gender['Male'].churn_rate).toFixed(1)}×</div><div className="grantee-metric-label">vs Male Rate</div></div>
            </div>
          </div>

          {/* Germany */}
          <div className="grantee-card">
            <div className="grantee-card-header">
              <div>
                <h3><EditableText sectionId="grantee_title_germany" data={c('grantee_title_germany')} onSave={handleSave} onRevert={handleRevert} /></h3>
                <div className="grantee-badge">Geographic Risk</div>
              </div>
              <div>
                <div className="grantee-stat">{fmtPct(geography['Germany'].churn_rate)}</div>
                <div className="grantee-stat-label">Churn Rate</div>
              </div>
            </div>
            <CommentaryBox sectionId="germany_body" data={c('germany_body')} variant="grantee" onSave={handleSave} onRevert={handleRevert} />
            <div className="grantee-metrics">
              <div><div className="grantee-metric-value">{fmt(geography['Germany'].total)}</div><div className="grantee-metric-label">Total Germany</div></div>
              <div><div className="grantee-metric-value">{fmt(geography['Germany'].churned)}</div><div className="grantee-metric-label">Churned</div></div>
              <div>
                <div className="grantee-metric-value">{(geography['Germany'].churn_rate / geography['France'].churn_rate).toFixed(1)}×</div>
                <div className="grantee-metric-label">vs France Rate</div>
              </div>
            </div>
          </div>
        </div>

        <div className="section-divider" />

        {/* Charts Row 2: Products + Gender */}
        <div className="charts-row">
          {/* Products */}
          <div className="chart-card">
            <div className="chart-title">Churn by Number of Products</div>
            <div className="bar-chart">
              {[1, 2, 3, 4].map((n) => {
                const stat = products[String(n)];
                if (!stat) return null;
                const isHigh = stat.churn_rate > 50;
                const isLow = stat.churn_rate < 15;
                return (
                  <div className="bar-row" key={n}>
                    <div className="bar-label">{n} Product{n > 1 ? 's' : ''}</div>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${stat.churn_rate}%`, background: isHigh ? 'var(--red)' : 'var(--navy)' }}
                      />
                    </div>
                    <div className={`bar-value${isHigh ? ' danger' : isLow ? ' positive' : ''}`}>
                      {fmtPct(stat.churn_rate)}
                    </div>
                  </div>
                );
              })}
            </div>
            <CommentaryBox sectionId="products_insight" data={c('products_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>

          {/* Gender */}
          <div className="chart-card">
            <div className="chart-title">Churn by Gender</div>
            <div className="legend">
              <div className="legend-item"><div className="legend-dot navy" />Retained</div>
              <div className="legend-item"><div className="legend-dot gold" />Churned</div>
            </div>
            <div className="bar-chart" style={{ marginBottom: '20px' }}>
              {Object.entries(gender).map(([g, stat]) => (
                <div className="bar-row" key={g}>
                  <div className="bar-label">{g}</div>
                  <div className="stacked-bar-track">
                    <div className="stacked-segment retained" style={{ width: `${100 - stat.churn_rate}%` }} />
                    <div className="stacked-segment churned" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className={`bar-value${stat.churn_rate > 22 ? ' danger' : ''}`}>
                    {fmtPct(stat.churn_rate)}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', paddingTop: '16px', borderTop: '1px solid var(--gray-200)' }}>
              {Object.entries(gender).map(([g, stat]) => (
                <div key={g} style={{ textAlign: 'center' }}>
                  <div style={{ fontFamily: 'Playfair Display, serif', fontSize: '24px', color: 'var(--navy)', fontWeight: 700 }}>{fmt(stat.total)}</div>
                  <div style={{ fontSize: '11px', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '1px' }}>{g} Customers</div>
                  <div style={{ fontSize: '13px', color: stat.churn_rate > 22 ? 'var(--red)' : 'var(--gray-500)', marginTop: '4px' }}>
                    {fmt(stat.churned)} churned
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Charts Row 3: Credit Score + Activity/Balance */}
        <div className="charts-row">
          {/* Credit Score */}
          <div className="chart-card">
            <div className="chart-title">Churn by Credit Score Band</div>
            <div className="bar-chart">
              {Object.entries(credit_score).map(([band, stat]) => (
                <div className="bar-row" key={band}>
                  <div className="bar-label">{band}</div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className="bar-value">{fmtPct(stat.churn_rate)}</div>
                </div>
              ))}
            </div>
            <CommentaryBox sectionId="credit_score_insight" data={c('credit_score_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>

          {/* Activity + Balance */}
          <div className="chart-card">
            <div className="chart-title">Churn by Activity &amp; Balance Status</div>
            <div className="legend">
              <div className="legend-item"><div className="legend-dot navy" />Retained</div>
              <div className="legend-item"><div className="legend-dot gold" />Churned</div>
            </div>
            <div className="bar-chart">
              {Object.entries(activity).map(([name, stat]) => (
                <div className="bar-row" key={name}>
                  <div className="bar-label">{name}</div>
                  <div className="stacked-bar-track">
                    <div className="stacked-segment retained" style={{ width: `${100 - stat.churn_rate}%` }} />
                    <div className="stacked-segment churned" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className={`bar-value${stat.churn_rate > 22 ? ' danger' : ''}`}>
                    {fmtPct(stat.churn_rate)}
                  </div>
                </div>
              ))}
              <div style={{ marginTop: '14px' }} />
              {Object.entries(balance).map(([name, stat]) => (
                <div className="bar-row" key={name}>
                  <div className="bar-label">{name}</div>
                  <div className="stacked-bar-track">
                    <div className="stacked-segment retained" style={{ width: `${100 - stat.churn_rate}%` }} />
                    <div className="stacked-segment churned" style={{ width: `${stat.churn_rate}%` }} />
                  </div>
                  <div className={`bar-value${stat.churn_rate > 22 ? ' danger' : ''}`}>
                    {fmtPct(stat.churn_rate)}
                  </div>
                </div>
              ))}
            </div>
            <CommentaryBox sectionId="activity_balance_insight" data={c('activity_balance_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>
        </div>

        <div className="section-divider" />

        {/* Tenure Chart */}
        <div className="charts-row">
          <div className="chart-card full-width">
            <div className="chart-title">Churn Rate by Tenure (Years with Bank)</div>
            <div className="tenure-chart">
              {Object.entries(tenure).map(([yr, stat]) => {
                const isMax = stat.churn_rate === maxTenureRate;
                const heightPx = Math.round(stat.churn_rate * 6);
                return (
                  <div className="tenure-bar-col" key={yr}>
                    <div
                      className={`tenure-bar-pct${isMax ? '' : ''}`}
                      style={{ color: isMax ? 'var(--gold)' : 'var(--navy)' }}
                    >
                      {fmtPct(stat.churn_rate)}
                    </div>
                    <div
                      className={`tenure-bar-fill${isMax ? ' highlight' : ''}`}
                      style={{ height: `${heightPx}px` }}
                    />
                    <div className="tenure-bar-label">{yr}</div>
                  </div>
                );
              })}
            </div>
            <div className="tenure-axis-label">Tenure (Years)</div>
            <CommentaryBox sectionId="tenure_insight" data={c('tenure_insight')} variant="inline" onSave={handleSave} onRevert={handleRevert} />
          </div>
        </div>

        <div className="section-divider" />

        {/* Summary Table */}
        <h2 className="status-header">Churn Status Summary</h2>
        <p className="section-subtitle" style={{ marginTop: '4px' }}>
          Consolidated view of churn rates across all segmentation dimensions.
        </p>
        <div className="chart-card" style={{ marginBottom: '36px', padding: 0, overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Segment</th>
                <th>Category</th>
                <th>Total Customers</th>
                <th>Churned</th>
                <th>Churn Rate</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, i) => (
                <tr key={i}>
                  <td>{row.segment}</td>
                  <td>{row.category}</td>
                  <td>{fmt(row.total ?? 0)}</td>
                  <td>{fmt(row.churned ?? 0)}</td>
                  <td>{fmtPct(row.churn_rate ?? 0)}</td>
                  <td>
                    <span className={`rate-pill ${row.risk}`}>
                      {row.risk === 'high' ? 'Critical/High' : row.risk === 'medium' ? 'Medium' : 'Low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Strategic Recommendations */}
        <CommentaryBox
          sectionId="strategic_recommendations"
          data={c('strategic_recommendations')}
          variant="box"
          title="Strategic Recommendations"
          onSave={handleSave}
          onRevert={handleRevert}
        />

      </div>

      {/* Footer */}
      <div className="dashboard-footer">
        CUSTOMER CHURN ANALYTICS · CONFIDENTIAL · ACME &amp; TRUST BANKING GROUP · 2026
      </div>
    </>
  );
}
