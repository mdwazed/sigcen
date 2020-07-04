
// generaate and display dynamic graph using canvasJS

window.onload = function () {
    let raw_data = [];
    $.get("/get_wk_graph_data/", { 'csrfmiddlewaretoken': csrf_token }, function (data) {
        console.log(data);
        data.forEach(function (el) {
            let sta = el.sta;
            raw_data.push([sta, el.create_wk, el.count ])
        })
        graph_data = prepare_graph_data(raw_data);
        chart = init_chart(graph_data)
        chart.render();
    }).fail(function () {
        alert('failed');
    });

    // console.log(raw_data);

    
}
// console.log(graph_data)

// ////////////////////////
function prepare_graph_data(raw_data) {
    // console.log(`rawdata: ${raw_data}`);
    sta_arr = []
    graph_data = []
    raw_data.forEach(function(el) {
        if (!sta_arr.includes(el[0])) {
            sta_arr.push(el[0])
        }
        // graph_data.push({x:el[1], y:el[2]});
    })
    for (let i=0; i<sta_arr.length; i++) {
        let tmp_arr = [];
        cur_sta = sta_arr[i];
        raw_data.forEach(function (el) {
            if(el[0] == cur_sta) {
                tmp_arr.push({x:el[1], y: el[2]})
            }
        })
        graph_data[i]=tmp_arr;
    }
    
    // console.log(sta_arr);
    // console.log(graph_data);
    return [sta_arr, graph_data];
    
}


function init_chart(graph_data){
    console.log('init chart');
    let data=[]
    let [sta_arr, data_arr] = graph_data;
    console.log(sta_arr);
    console.log(data_arr);
    for(var i=0; i<sta_arr.length; i++) {
        data[i] = 
            {
            type: "line",
            axisYType: "secondary",
            name: sta_arr[i],
            showInLegend: true,
            markerSize: 0,
            yValueFormatString: "#,###",
            dataPoints: data_arr[i],
            }
    };
    var chart = new CanvasJS.Chart("chartContainer", {
        title: {
            text: "Weekly DAK Generation"
        },
        axisX: {
            // valueFormatString: "MMM YYYY"
            title: "Week",
        },
        axisY2: {
            title: "Total No.",
            // prefix: "$",
            // suffix: "K"
        },
        toolTip: {
            shared: true
        },
        legend: {
            cursor: "pointer",
            verticalAlign: "top",
            horizontalAlign: "center",
            dockInsidePlotArea: true,
            itemclick: toogleDataSeries
        },
        data: data,
    });
    return chart;
}

function toogleDataSeries(e) {
    if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
        e.dataSeries.visible = false;
    } else {
        e.dataSeries.visible = true;
    }
    chart.render();
};
