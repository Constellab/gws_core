new GViewTemplate({
    class: "gview:form",
    render: function (data) {

        function _form(container, data){
            var rows = ''
            data.style = data.style || ""
            data.title = data.title || ""
            data.valuetype = data.valuetype || "text"

            for(var i in data.fields){   
                var uuid = uuidv4()
                
                if(data.fields[i].type == "hidden"){
                    rows += `
                        <input type="hidden" value="`+data.fields[i].value+`" name="`+data.fields[i].name+`">
                    `;
                } else{
                    var pattern = ''
                    if(data.fields[i].valuetype == "numeric" || data.fields[i].valuetype == "num"){
                        pattern = 'pattern="-?[0-9]*(\.[0-9]+)?"'
                    }
                    rows += `
                        <div class="mdl-textfield mdl-js-textfield mdl-textfield--floating-label">
                            <input class="mdl-textfield__input" type="text" `+pattern+` id="`+uuid+`" name="`+data.fields[i].name+`">
                            <label class="mdl-textfield__label" for="`+uuid+`">`+data.fields[i].label+`</label>
                            <span class="mdl-textfield__error">Invalid value</span>
                        </div>
                    `;
                }
            }
            
            container.innerHTML = `
                <form action="`+data.submit.url+`" method="post">
                `+rows+`
                </form>
            `;
            componentHandler.upgradeDom();
        }

        return _form
    }
})