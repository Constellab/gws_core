new GViewTemplate({
    class: "gview:table",
    render: function (data) {
        function _table(container, data){
            var header = ''
            data.coltypes = data.coltypes || []

            for(var i in data.colnames){
                cls = ""
                if(i < data.coltypes.length && data.coltypes[i] == "num" ){
                    cls = "mdc-data-table__header-cell--numeric"
                }
                header += '<th class="mdc-data-table__header-cell role="columnheader" scope="col" '+cls+'">'+data.colnames[i]+'</th>'
            }

            var body = ''
            for(var row of data.data){
                var rowText = ""
                for(var val of row){
                    rowText += '<td class="mdc-data-table__cell mdc-data-table__cell--numeric">'+val+'</td>'
                }
                body += '<tr class="mdc-data-table__row">'+rowText+'</tr>'
            }
            
            data.style = data.style || ""
            container.innerHTML = `
                <div class="mdc-data-table">
                    <div class="mdc-data-table__table-container">

                        <table class="mdc-data-table__table">
                            <thead>
                            <tr class="mdc-data-table__header-row">
                                `+header+`
                            </tr>
                            </thead>
                            <tbody class="mdc-data-table__content">
                                `+body+`
                            </tbody>
                        </table>

                    </div>
                </div>
            `;
        }
        
        return _table
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