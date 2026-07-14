// post donut chart
var postoptions = {
    series: [accept_count, reject_count, pending_count],
    labels: ["Accepted", "Rejected", "Pending"],
    chart: {
    // width: 380,
    type: 'donut',
  },
  plotOptions: {
    pie: {
      startAngle: -90,
      endAngle: 270
    }
  },
  dataLabels: {
    enabled: false
  },
  fill: {
    type: 'gradient',
  },
  legend: {
    formatter: function(val, opts) {
      return val + " - " + opts.w.globals.series[opts.seriesIndex]
    }
  },
  title: {
      text: 'Post',
      align: 'left',
      style: {
        fontSize: "24px",
        color: '#666'
      }
    },
  subtitle: {
    text: 'Last 28 days',
    align: 'left',
    style: {
      fontSize: "14px",  // Smaller font size for "last 28 days"
      color: '#666'
    }
  }, 
  responsive: [{
    breakpoint: 480,
    options: {
      chart: {
        width: 200
      },
      legend: {
        position: 'bottom'
      }
    }
  }]
  };

  var postchart = new ApexCharts(document.querySelector("#post-donut-chart"), postoptions);
  postchart.render();

// total post in radial
// var totalpostoptions = {
//     series: [70],
//     chart: {
//     height: 350,
//     type: 'radialBar',
//   },
//   plotOptions: {
//     radialBar: {
//       hollow: {
//         size: '70%',
//       }
//     },
//   },
//   labels: ['Cricket'],
//   };

//   var totalpostchart = new ApexCharts(document.querySelector("#total-post-chart"), totalpostoptions);
//   totalpostchart.render();

// Total Post line chart
var totalpostoptions = {
    series: [{
      name: 'Post',
      // data: [4, 3, 10, 9, 29, 19, 22, 9, 12, 7, 19, 5, 13, 9, 17, 2, 7, 5]
      data: recent_post
    }],
    chart: {
      type: 'line',
      toolbar: {
        show: false  // 🔥 This hides the toolbar
      }
    },
    stroke: {
      width: 5,
      curve: 'smooth',
    },
    xaxis: {
      type: 'category',
      // categories: ['1/11/2000', '2/11/2000', '3/11/2000', '4/11/2000', '5/11/2000', '6/11/2000', '7/11/2000', '8/11/2000', '9/11/2000', '10/11/2000', '11/11/2000', '12/11/2000', '1/11/2001', '2/11/2001', '3/11/2001','4/11/2001' ,'5/11/2001' ,'6/11/2001'],
      categories: days,
      tickAmount: 10,
      labels: {
        show: false // 🔥 This hides x-axis labels
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      labels: {
        show: false  // 🔥 This hides y-axis labels
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    grid: {
        show: false
    },
    title: {
      text: 'Total Post',
      align: 'left',
      style: {
        fontSize: "24px",  // Larger font size for "Total Post"
        color: '#666'
      }
    },
    subtitle: {
      text: 'Last 28 days',
      align: 'left',
      style: {
        fontSize: "14px",  // Smaller font size for "last 28 days"
        color: '#666'
      }
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'dark',
        gradientToColors: ['#FDD835'],
        shadeIntensity: 1,
        type: 'horizontal',
        opacityFrom: 1,
        opacityTo: 1,
        stops: [0, 100, 100, 100]
      },
    }
  };
  
  var totalpostchart = new ApexCharts(document.querySelector("#total-post-chart"), totalpostoptions);
  totalpostchart.render();
  
// Pending Post line chart
var pendingpostoptions = {
    series: [{
      name: 'Pending',
      data: pending_post
    }],
    chart: {
      type: 'line',
      toolbar: {
        show: false  // 🔥 This hides the toolbar
      }
    },
    stroke: {
      width: 5,
      curve: 'smooth',
    },
    xaxis: {
      type: 'category',
      categories: days,
      tickAmount: 10,
      labels: {
        show: false // 🔥 This hides x-axis labels
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      labels: {
        show: false  // 🔥 This hides y-axis labels
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    grid: {
        show: false
    },
    title: {
      text: 'Pending Post',
      align: 'left',
      style: {
        fontSize: "24px",
        color: '#666'
      }
    },
    subtitle: {
      text: 'Last 28 days',
      align: 'left',
      style: {
        fontSize: "14px",  // Smaller font size for "last 28 days"
        color: '#666'
      }
    },
    fill: {
      type: 'gradient',
      gradient: {
        shade: 'dark',
        gradientToColors: ['#FDD835'],
        shadeIntensity: 1,
        type: 'horizontal',
        opacityFrom: 1,
        opacityTo: 1,
        stops: [0, 100, 100, 100]
      },
    }
  };
  
  var pendingpostchart = new ApexCharts(document.querySelector("#pending-post-chart"), pendingpostoptions);
  pendingpostchart.render();

// accept vs pending bar chart
var acceptvspendingoptions = {
    series: [{
      name: 'Accept',
      data: accept_post
    },
    {
      name: 'Pending',
      data: pending_post
    }],
    chart: {
      type: 'bar',
    //   height: 440,
      stacked: true,
      toolbar: {
        show: false  // ✅ Remove the menu button
      }
    },
    colors: ['#008FFB', '#FF4560'],
    plotOptions: {
      bar: {
        borderRadius: 5,
        borderRadiusApplication: 'end',
        borderRadiusWhenStacked: 'all',
        horizontal: true,
        barHeight: '80%',
      }
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      width: 1,
      colors: ["#fff"]
    },
    grid: {
      show: false  // ✅ Hides all grid lines
    },
    yaxis: {
      show: false  // ✅ Hides y-axis completely
    },
    xaxis: {
      show: false,  // ✅ Hides x-axis completely
    //   categories: ['85+', '80-84', '75-79', '70-74', '65-69', '60-64', '55-59', '50-54',
    //     '45-49', '40-44', '35-39', '30-34', '25-29', '20-24', '15-19', '10-14', '5-9', '0-4'
    //   ],
      labels: {
        show: false
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    tooltip: {
      show: false
    },
    title: {
      text: 'Accept vs Pending',
      align: 'left',
      style: {
        fontSize: "24px",
        color: '#666'
      }
    },
    subtitle: {
      text: 'Last 28 days',
      align: 'left',
      style: {
        fontSize: "14px",  // Smaller font size for "last 28 days"
        color: '#666'
      }
    },    
  };
  
  var acceptvspendingchart = new ApexCharts(document.querySelector("#accept-pending-chart"), acceptvspendingoptions);
  acceptvspendingchart.render();