Chart.defaults.global.legend.display = false;

var ctx = document.getElementById("budget_chart");
var ctx2 = document.getElementById("schedule_chart");
var ctx3 = document.getElementById("overhead_chart");

var data = {
    labels: ["2011", "2012", "2013", "2014", "2015", "2016", "2017"],
    datasets: [
        {
            label: "Overall average",
            fill: false,
            borderColor: "#31b0d5",
            pointBorderColor: "#31b0d5",
            pointBackgroundColor: "#31b0d5",
            pointBorderWidth: 5,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(75,192,192,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: [75, 60, 65, 50, 20, 25, 20],
            spanGaps: false,
        },
        {
            label: "Average - small projects",
            fill: false,
            borderColor: "rgba(223,105,26,0.25)",
            pointBorderColor: "rgba(223,105,26,0.25)",
            pointBackgroundColor: "rgba(223,105,26,0.25)",
            pointBorderWidth: 5,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(223,105,26,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: [90, 80, 80, 60, 40, 45, 40],
            spanGaps: false,
        },        
        {
            label: "Average - medium projects",
            fill: false,
            borderColor: "rgba(240,173,78,0.25)",
            pointBorderColor: "rgba(240,173,78,0.25)",
            pointBackgroundColor: "rgba(240,173,78,0.25)",
            pointBorderWidth: 5,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(240,173,78,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: [75, 55, 60, 30, 20, 15, 10],
            spanGaps: false,
        },
        {
            label: "Average - large projects",
            fill: false,
            borderColor: "rgba(92,184,92,0.25)",
            pointBorderColor: "rgba(92,184,92,0.25)",
            pointBackgroundColor: "rgba(92,184,92,0.25)",
            pointBorderWidth: 5,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "rgba(92,184,92,1)",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: [90, 70, 50, 30, 20, 10, 5],
            spanGaps: false,
        }
    ]
};

var budget_options = {
	title: {
		display: true,
		text: "Budget Overage",
		fontColor: "#fff"
	},
	scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true
                }
            }]
    }
};

var schedule_options = {
	title: {
		display: true,
		text: "Schedule Overage",
		fontColor: "#fff"
	},
	scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true
                }
            }]
    }
};

var overhead_options = {
	title: {
		display: true,
		text: "Overhead",
		fontColor: "#fff"
	},
	scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true
                }
            }]
    }
};

var budget_chart = new Chart(ctx, {
    type: 'line',
    data: data,
    options: budget_options,
});

var schedule_chart = new Chart(ctx2, {
    type: 'line',
    data: data,
    options: schedule_options
});

var overhead_chart = new Chart(ctx3, {
    type: 'line',
    data: data,
    options: overhead_options
});