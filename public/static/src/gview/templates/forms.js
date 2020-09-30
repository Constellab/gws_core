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