import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable'; // For trend indicators
}

/**
 * MetricCard Component
 *
 * Displays a single performance metric in a card format.
 */
export const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, trend }) => {
  return (
    <div style={{ border: '1px solid #eee', padding: '15px', margin: '10px', minWidth: '150px', textAlign: 'center' }}>
      <h4>{title}</h4>
      <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
        {value} {unit || ''}
      </p>
      {trend && <p>Trend: {trend}</p>}
    </div>
  );
};

interface RealTimeChartProps {
  // TODO: Define props for data stream, chart configuration
  dataSourceUrl?: string; // Example for WebSocket or polling
  metricName: string;
}

/**
 * RealTimeChart Component
 *
 * Displays real-time data, typically as a line or area chart.
 */
export const RealTimeChart: React.FC<RealTimeChartProps> = ({ metricName }) => {
  return (
    <div style={{ border: '1px dashed #ccc', padding: '20px', minHeight: '200px', marginTop: '20px' }}>
      <h5>Real-time: {metricName}</h5>
      <p>Live data chart will appear here.</p>
    </div>
  );
};


/**
 * PerformanceMetrics Components Collection
 *
 * This file will contain components related to displaying performance metrics,
 * such as real-time data dashboards, metric cards, trend charts, and alert indicators.
 */
const PerformanceMetricsOverview: React.FC = () => {
  // Placeholder for a collection of metrics components
  return (
    <div style={{ padding: '10px' }}>
      <h3>Performance Metrics Overview</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>
        <MetricCard title="CPU Usage" value="75" unit="%" trend="up" />
        <MetricCard title="Memory" value="12.5" unit="GB" trend="stable" />
        <MetricCard title="API Errors" value="3" unit="/min" trend="down" />
      </div>
      <RealTimeChart metricName="Network Throughput" />
    </div>
  );
};

export default PerformanceMetricsOverview;
