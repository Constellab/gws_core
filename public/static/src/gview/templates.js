

new GViewTemplate({
    class: "gview:sidebar-btn",
    render: function (data) {
        return `
            <li class="active">
                <a href="`+ data.url + `" target="">
                    <i class="`+ data.icon + `"></i>
                    <p>`+ data.name + `</p>
                </a>
            </li>
        `;
    }
})

new GViewTemplate({
    class: "gview:card",
    render: function (data) {
        data.style = data.style || ""
        return `
            <div class="card ` + data.style + `">
                <div class="card-header">
                    ` + data.title + `
                </div>
                <div class="card-body">
                    ` + data.body + `
                </div>
            </div>
        `;
    }
})

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

new GViewTemplate({
    class: "gview:simple-table",
    render: function (data) {
        var header = ''
        for(var val of data.header){
            header += '<th>'+val+'</th>'
        }

        var body = ''
        for(var row of data.body){
            var rowText = ""
            for(var val of row){
                rowText += '<td>'+val+'</td>'
            }
            body += '<tr>'+rowText+'</tr>'
        }
        
        data.style = data.style || ""
        return `
            <div class="card `+data.style+`">
                <div class="card-header">
                    <h4 class="card-title">`+data.title+`</h4>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table tablesorter" id="">
                            <thead class="text-primary">
                                <tr>
                                `+header+`
                                </tr>
                            </thead>
                            <tbody>
                                `+body+`
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
})

new GViewTemplate({
    class: "gview:form",
    render: function (data) {
        rows = ''
        data.style = data.style || ""
        data.title = data.title || ""
        for(var i in data.fields){   
            if(data.fields[i].type == "hidden"){
                rows += `
                    <input type="hidden" value="`+data.fields[i].value+`" name="`+data.fields[i].name+`">
                `;
            } else{
                rows += `
                    <div class="`+(data.col ? data.col : "col-md-12")+`">
                        <div class="form-group">
                            <label>`+(data.fields[i].label ? data.fields[i].label : "&nbsp;")+`</label>
                            <input  type="`+data.fields[i].type+`" 
                                    class="form-control" 
                                    `+ (data.fields[i].disabled ? "disabled" : "") +`
                                    placeholder="`+(data.fields[i].placeholder ? data.fields[i].placeholder: "")+`" 
                                    value="`+data.fields[i].value+`" name="`+data.fields[i].name+`">
                        </div>
                    </div>
                `;
            }
        }
        
        if(data.title != ""){
            titleHTML = `
                <div class="card-header">
                    <h5 class="title">`+data.title+`</h5>
                </div>
            `
        } else{
            titleHTML = ""
        }
        
        return `
            <form action="`+data.submit.url+`" method="post">
            <div class="card `+data.style+`">
                `+titleHTML+`
                <div class="card-body">
                    <div class="row">
                        `+ rows +`
                    </div>
                </div>
                <div class="card-footer">
                    <button type="submit" class="btn `+data.style+`">`+data.submit.value+`</button>
                </div>
            </div>
            </form>
        `;

    }
})

new GViewTemplate({
    class: "gview:action",
    render: function (data) {
        var target = data.target
        console.log(target)
        console.log(document.querySelector(target))
        var gviewObj = document.querySelector(target).userData.gview
        gviewObj.render(data)
    }
})

new GViewTemplate({
    class: "gview:cell-g3",
    render: function (data) {
        return loadG3Data
    }
})