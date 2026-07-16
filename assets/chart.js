(function () {
  if (typeof ApexCharts === 'undefined') {
    return;
  }

  const data = window.dashboardData || {};
  const labels = Array.isArray(data.labels) ? data.labels : [];
  const series = Array.isArray(data.series) ? data.series : [];
  const pendingSeries = Array.isArray(data.pendingSeries) ? data.pendingSeries : [];

  if (document.getElementById('activity-chart')) {
    const activityOptions = {
      chart: { type: 'line', toolbar: { show: false } },
      series: [{ name: 'Activity', data: pendingSeries }],
      stroke: { width: 3, curve: 'smooth' },
      xaxis: { categories: labels, labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
      yaxis: { labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
      grid: { show: false },
      colors: ['#2563eb'],
      title: { text: 'Pending trend', align: 'left', style: { fontSize: '20px', color: '#374151' } },
      subtitle: { text: 'Last 28 days', align: 'left', style: { fontSize: '13px', color: '#6b7280' } }
    };
    new ApexCharts(document.getElementById('activity-chart'), activityOptions).render();
  }

  if (document.getElementById('status-chart')) {
    const statusOptions = {
      chart: { type: 'donut', toolbar: { show: false } },
      series: [
        series[0] && Array.isArray(series[0].data) ? series[0].data.reduce(function (sum, value) { return sum + value; }, 0) : 0,
        series[1] && Array.isArray(series[1].data) ? series[1].data.reduce(function (sum, value) { return sum + value; }, 0) : 0,
        pendingSeries.reduce(function (sum, value) { return sum + value; }, 0)
      ],
      labels: ['Approvals', 'Rejections', 'Pending'],
      colors: ['#16a34a', '#dc2626', '#f59e0b'],
      legend: { position: 'bottom' },
      dataLabels: { enabled: false },
      title: { text: 'Status mix', align: 'left', style: { fontSize: '20px', color: '#374151' } },
      subtitle: { text: 'All reports', align: 'left', style: { fontSize: '13px', color: '#6b7280' } }
    };
    new ApexCharts(document.getElementById('status-chart'), statusOptions).render();
  }
})();