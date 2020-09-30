new GViewTemplate({
    class: "gview:table",
    render: function (data) {
        var header = ''
        for(var val of data.colnames){
            header += '<th>'+val+'</th>'
        }

        var body = ''
        for(var row of data.data){
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
    class: "gview:table-task",
    render: function (data) {
        var header = ''
        for(var val of data.colnames){
            header += '<th>'+val+'</th>'
        }

        var body = ''
        for(var row of data.data){
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