const Chart = require('chart.js/auto');

var chart = null
var chartData = {
    labels: [],
    datasets: [{
        label: '',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        data: [],
    }, {
        label: '',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        data: [],
    }]
};
var chartOptions = {
    scales: {
        yAxes: [{
            ticks: {
                beginAtZero: true
            }
        }]
    }
};

function initChart(){
    var chartElementContext = document.getElementById("chart").getContext("2d")
    chart = new Chart(chartElementContext, {
        type: "line",
        data: chartData,
        options: chartOptions,
    })
}

function clearChart(){
    chart.data.labels = []
    chart.data.datasets[0].data = []
    chart.data.datasets[1].data = []
    chart.update()
}

function displayVerifResults(results){
    if(results["all-equal"] == true){
        console.log("all equal!")
        clearChart()
    }else{
        chart.data.datasets.labels = results["x-axis-array"]
        chart.data.datasets[0].data = results["y-axis-array1"]
        chart.data.datasets[1].data = results["y-axis-array2"]
        chart.update()
    }
}

function main() {
    initChart()
    displayVerifResults({
        "all-equal": false,
        "x-axis-array": [0, 1, 2, 3],
        "y-axis-array1": [1, 2, 3, 4],
        "y-axis-array2": [2, 3, 4, 5],
    })
}

window.onload = main
