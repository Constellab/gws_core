new GViewTemplate({
    class: "gview:chart",
    render: function (data) {
        return `
            <div class="card card-chart">
                <div class="card-header">
                <h5 class="card-category">` + data.title + `</h5>
                <h3 class="card-title"><i class="` + data.icon + `"></i>` + data.summary + `</h3>
                </div>
                <div class="card-body">
                <div class="chart-area">
                    <canvas id="CountryChart"></canvas>
                </div>
                </div>
            </div>
        `;
    }
})